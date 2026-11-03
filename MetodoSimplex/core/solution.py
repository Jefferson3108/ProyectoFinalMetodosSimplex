"""
core/solution.py
----------------
Convierte la tabla final del simplex en una solución legible:
- valor de Z (con el signo correcto si era minimización)
- valor de cada variable con su nombre y unidad
- uso de cada recurso (holguras) y cuáles están agotados
- verificación de las restricciones pendientes ('>=', '=')
- detección de posibles soluciones múltiples
"""
from __future__ import annotations
from dataclasses import dataclass, field
from fractions import Fraction
from MetodoSimplex.Utils.formatters import formatear_numero
from .models import Restriccion
from .simplex import EstadoSimplex, ResultadoSimplex
from .standarizer import ProblemaEstandar, parsear_a_fraction

@dataclass
class ValorVariable:
    nombre: str
    unidad: str
    valor: Fraction
    es_basica: bool

@dataclass
class UsoRecurso:
    """Estado de una restricción '<=' incluida en el simplex."""
    nombre: str
    unidad: str
    disponible: Fraction     # lado derecho
    usado: Fraction          # lado izquierdo evaluado en la solución
    holgura: Fraction        # sobrante (valor de s_i)
    agotado: bool            # holgura == 0 (restricción activa)

@dataclass
class VerificacionRestriccion:
    """Resultado de comprobar una restricción pendiente."""
    restriccion: Restriccion
    lado_izquierdo: Fraction
    se_cumple: bool

@dataclass
class Solucion:
    estado: EstadoSimplex
    mensaje: str
    nombre_objetivo: str = "Z"
    unidad_objetivo: str = ""
    valor_z: Fraction | None = None
    variables: list[ValorVariable] = field(default_factory=list)
    recursos: list[UsoRecurso] = field(default_factory=list)
    pendientes: list[VerificacionRestriccion] = field(default_factory=list)
    posibles_soluciones_multiples: bool = False

    @property
    def requiere_dual(self) -> bool:
        """True si alguna restricción pendiente se viola."""
        return any(not p.se_cumple for p in self.pendientes)

    @property
    def es_final(self) -> bool:
        """True si es óptima para el problema COMPLETO (no hace falta dual)."""
        return self.estado is EstadoSimplex.OPTIMA and not self.requiere_dual

    def como_texto(self, decimales: int = 4) -> str:
        f = lambda v: formatear_numero(v, decimales)
        lineas = [self.mensaje]
        if self.valor_z is not None:
            u = f" {self.unidad_objetivo}" if self.unidad_objetivo else ""
            lineas.append(f"\n{self.nombre_objetivo} = {f(self.valor_z)}{u}")
        if self.variables:
            lineas.append("\nVariables:")
            for v in self.variables:
                u = f" {v.unidad}" if v.unidad else ""
                lineas.append(f"  {v.nombre} = {f(v.valor)}{u}")
        if self.recursos:
            lineas.append("\nRecursos:")
            for r in self.recursos:
                u = f" {r.unidad}" if r.unidad else ""
                estado = "AGOTADO" if r.agotado else f"sobran {f(r.holgura)}{u}"
                lineas.append(f"  {r.nombre}: {f(r.usado)} de "
                             f"{f(r.disponible)}{u} ({estado})")
        if self.pendientes:
            lineas.append("\nRestricciones pendientes:")
            for p in self.pendientes:
                marca = "se cumple" if p.se_cumple else "SE VIOLA"
                lineas.append(f"  {p.restriccion.nombre}: lado izquierdo = "
                             f"{f(p.lado_izquierdo)} "
                             f"({p.restriccion.signo.value} "
                             f"{f(p.restriccion.rhs)}) -> {marca}")
        if self.posibles_soluciones_multiples:
            lineas.append("\nNota: hay una variable no básica con costo "
                         "reducido 0; pueden existir soluciones óptimas "
                         "alternativas.")
        return "\n".join(lineas)

def construir_solucion(est: ProblemaEstandar,
                       res: ResultadoSimplex) -> Solucion:
    """Arma la Solucion a partir del resultado del simplex."""
    problema = est.problema
    base = Solucion(estado=res.estado, mensaje=res.mensaje,
                    nombre_objetivo=problema.nombre_objetivo,
                    unidad_objetivo=problema.unidad_objetivo)
    
    # Sin solución óptima: solo se informa el estado
    if res.estado is not EstadoSimplex.OPTIMA:
        if est.hay_pendientes and res.estado is EstadoSimplex.NO_ACOTADA:
            base.mensaje += (" Ojo: se ignoraron las restricciones "
                            "pendientes; con ellas el problema podría "
                            "estar acotado (requiere otro método).")
        return base

    tabla = res.tabla_final
    valores = tabla.valores_columnas()
    n = est.n_variables
    x = valores[:n]
    en_base = set(tabla.base)

    # Z con el signo original
    base.valor_z = -tabla.valor_z if est.invertir_z else tabla.valor_z

    # Variables de decisión
    base.variables = [
        ValorVariable(v.nombre, v.unidad, x[j], j in en_base)
        for j, v in enumerate(problema.variables)
    ]

    # Recursos (restricciones incluidas)
    for i, r in enumerate(est.incluidas):
        holgura = valores[n + i]
        
        usado = sum(parsear_a_fraction(a) * xv for a, xv in zip(r.coeficientes, x))
        disponible = parsear_a_fraction(r.rhs)
        base.recursos.append(UsoRecurso(r.nombre, r.unidad, disponible, usado,
                                        holgura, holgura == 0))

    # Restricciones pendientes
    for r in est.pendientes:
        
        lado = sum(parsear_a_fraction(a) * xv for a, xv in zip(r.coeficientes, x))
        base.pendientes.append(VerificacionRestriccion(r, lado,
                                                       r.se_cumple(x)))

    # Soluciones múltiples: columna no básica con z_j - c_j = 0
    base.posibles_soluciones_multiples = any(
        j not in en_base and tabla.fila_z[j] == 0
        for j in range(tabla.n_columnas))

    # Mensaje final según las pendientes
    if base.requiere_dual:
        violadas = ", ".join(f"'{p.restriccion.nombre}'"
                            for p in base.pendientes if not p.se_cumple)
        base.mensaje = (f"El simplex llegó a un óptimo, pero viola: "
                        f"{violadas}. Para continuar se necesita el "
                        f"simplex dual.")
    elif est.hay_pendientes:
        base.mensaje = ("Solución óptima. Cumple todas las restricciones "
                        "pendientes, por lo tanto es óptima para el "
                        "problema completo.")
    else:
        base.mensaje = "Solución óptima."

    return base


# ---------------------------------------------------------------------------
# Prueba rápida:  python -m core.solution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from .models import Problema, Variable
    from .simplex import resolver
    from .standarizer import estandarizar

    problema = Problema(
        tipo="max",
        nombre_objetivo="Utilidad",
        unidad_objetivo="$/semana",
        variables=[Variable("Mesas", "unidades/semana"),
                   Variable("Sillas", "unidades/semana")],
        coef_objetivo=[30, 20],
        restricciones=[
            Restriccion("Carpintería", "horas", [2, 1], "<=", 100),
            Restriccion("Acabado", "horas", [1, 1], "<=", 80),
            Restriccion("Demanda mesas", "unidades", [1, 0], "<=", 40),
            Restriccion("Mínimo de mesas", "unidades", [1, 0], ">=", 10),
        ],
    )
    est = estandarizar(problema)
    print(construir_solucion(est, resolver(est)).como_texto())
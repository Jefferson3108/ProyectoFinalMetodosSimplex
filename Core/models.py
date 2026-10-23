"""
core/models.py
--------------
Estructuras de datos del problema de programación lineal.

Este módulo NO resuelve nada: solo describe el problema y valida que esté
bien formado. Todos los números se guardan como `Fraction` para que las
tablas del simplex sean exactas (3/2 en vez de 1.5000000001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Union

Numero = Union[int, float, str, Fraction]


# ---------------------------------------------------------------------------
# Errores y utilidades
# ---------------------------------------------------------------------------
class ErrorModelo(ValueError):
    """Se lanza cuando el problema ingresado no es válido."""


def a_fraccion(valor: Numero) -> Fraction:
    """
    Convierte lo que escriba el usuario a Fraction.
    Acepta: 3, 2.5, "2,5", "3/2", Fraction(3, 2).
    """
    if isinstance(valor, Fraction):
        return valor
    try:
        if isinstance(valor, float):
            return Fraction(str(valor))      # evita errores de binario (0.1)
        if isinstance(valor, str):
            return Fraction(valor.strip().replace(",", "."))
        return Fraction(valor)
    except (ValueError, ZeroDivisionError, TypeError):
        raise ErrorModelo(f"'{valor}' no es un número válido") from None


# ---------------------------------------------------------------------------
# Enumeraciones
# ---------------------------------------------------------------------------
class TipoOptimizacion(Enum):
    MAX = "max"
    MIN = "min"


class Signo(Enum):
    LE = "<="
    GE = ">="
    EQ = "="

    @classmethod
    def desde_texto(cls, texto: str) -> "Signo":
        """Acepta '<=', '≤', '>=', '≥', '=' (con o sin espacios)."""
        mapa = {"<=": cls.LE, "≤": cls.LE,
                ">=": cls.GE, "≥": cls.GE,
                "=": cls.EQ, "==": cls.EQ}
        try:
            return mapa[texto.strip()]
        except KeyError:
            raise ErrorModelo(f"Signo no reconocido: '{texto}'") from None


# ---------------------------------------------------------------------------
# Variable de decisión
# ---------------------------------------------------------------------------
@dataclass
class Variable:
    """
    Variable de decisión.
    Ejemplo: Variable("Mesas", "unidades/semana")
    """
    nombre: str
    unidad: str = ""

    def __post_init__(self):
        self.nombre = self.nombre.strip()
        self.unidad = self.unidad.strip()
        if not self.nombre:
            raise ErrorModelo("Toda variable necesita un nombre")

    def __str__(self) -> str:
        return f"{self.nombre} [{self.unidad}]" if self.unidad else self.nombre


# ---------------------------------------------------------------------------
# Restricción
# ---------------------------------------------------------------------------
@dataclass
class Restriccion:
    """
    Restricción lineal:  a1*x1 + a2*x2 + ... (signo) rhs

    Ejemplo: Restriccion("Horas de carpintería", "horas",
                         coeficientes=[2, 3], signo=Signo.LE, rhs=100)
    """
    nombre: str
    unidad: str
    coeficientes: list[Fraction]
    signo: Signo
    rhs: Fraction

    def __post_init__(self):
        self.nombre = self.nombre.strip()
        self.unidad = self.unidad.strip()
        if not self.nombre:
            raise ErrorModelo("Toda restricción necesita un nombre")
        self.coeficientes = [a_fraccion(c) for c in self.coeficientes]
        self.rhs = a_fraccion(self.rhs)
        if isinstance(self.signo, str):
            self.signo = Signo.desde_texto(self.signo)

    def se_cumple(self, valores: list[Fraction]) -> bool:
        """True si los valores de las variables satisfacen la restricción."""
        lado_izq = sum(a * x for a, x in zip(self.coeficientes, valores))
        if self.signo is Signo.LE:
            return lado_izq <= self.rhs
        if self.signo is Signo.GE:
            return lado_izq >= self.rhs
        return lado_izq == self.rhs

    def __str__(self) -> str:
        return (f"{self.nombre}: "
                f"{_formatear_lineal(self.coeficientes)} "
                f"{self.signo.value} {self.rhs}"
                f"{' ' + self.unidad if self.unidad else ''}")


# ---------------------------------------------------------------------------
# Problema completo
# ---------------------------------------------------------------------------
@dataclass
class Problema:
    """
    Problema de programación lineal completo.

    - tipo:            MAX o MIN
    - variables:       lista de Variable (define n.º de variables)
    - coef_objetivo:   coeficientes de la función objetivo (uno por variable)
    - restricciones:   lista de Restriccion
    - nombre_objetivo: ej. "Utilidad total"
    - unidad_objetivo: ej. "$" o "$/semana"
    """
    tipo: TipoOptimizacion
    variables: list[Variable]
    coef_objetivo: list[Fraction]
    restricciones: list[Restriccion] = field(default_factory=list)
    nombre_objetivo: str = "Z"
    unidad_objetivo: str = ""

    def __post_init__(self):
        if isinstance(self.tipo, str):
            self.tipo = TipoOptimizacion(self.tipo.lower())
        self.coef_objetivo = [a_fraccion(c) for c in self.coef_objetivo]
        self.validar()

    # -- Propiedades de conveniencia ----------------------------------------
    @property
    def n_variables(self) -> int:
        return len(self.variables)

    @property
    def n_restricciones(self) -> int:
        return len(self.restricciones)

    @property
    def es_maximizacion(self) -> bool:
        return self.tipo is TipoOptimizacion.MAX

    @property
    def es_forma_canonica(self) -> bool:
        """
        True si TODAS las restricciones son aptas para el simplex primal
        (todas '<=' con RHS >= 0). Sirve para maximizar y para minimizar.
        """
        return all(_es_apta_primal(r) for r in self.restricciones)

    def separar_restricciones(self) -> tuple[list[Restriccion],
                                             list[Restriccion]]:
        """
        Divide las restricciones en (aptas, pendientes):
          - aptas:      '<=' con RHS >= 0  -> las resuelve el simplex primal
          - pendientes: '>=', '=' o RHS negativo -> quedan para verificarse
                        después (y para el simplex dual si se violan)
        """
        aptas = [r for r in self.restricciones if _es_apta_primal(r)]
        pendientes = [r for r in self.restricciones
                      if not _es_apta_primal(r)]
        return aptas, pendientes

    # -- Validación ---------------------------------------------------------
    def validar(self) -> None:
        """Lanza ErrorModelo si el problema está mal formado."""
        if self.n_variables == 0:
            raise ErrorModelo("El problema necesita al menos una variable")
        if self.n_restricciones == 0:
            raise ErrorModelo("El problema necesita al menos una restricción")

        if len(self.coef_objetivo) != self.n_variables:
            raise ErrorModelo(
                f"La función objetivo tiene {len(self.coef_objetivo)} "
                f"coeficientes pero hay {self.n_variables} variables")

        nombres_var = [v.nombre.lower() for v in self.variables]
        if len(set(nombres_var)) != len(nombres_var):
            raise ErrorModelo("Hay nombres de variables repetidos")

        nombres_res = [r.nombre.lower() for r in self.restricciones]
        if len(set(nombres_res)) != len(nombres_res):
            raise ErrorModelo("Hay nombres de restricciones repetidos")

        for r in self.restricciones:
            self._validar_coeficientes(r)

    def _validar_coeficientes(self, restriccion: Restriccion) -> None:
        if len(restriccion.coeficientes) != self.n_variables:
            raise ErrorModelo(
                f"La restricción '{restriccion.nombre}' tiene "
                f"{len(restriccion.coeficientes)} coeficientes pero hay "
                f"{self.n_variables} variables")

    # -- Construcción incremental (útil para la interfaz) -------------------
    def agregar_restriccion(self, restriccion: Restriccion) -> None:
        """
        Agrega una restricción solo si es válida. Si no lo es, lanza
        ErrorModelo y el problema queda exactamente como estaba.
        """
        if any(r.nombre.lower() == restriccion.nombre.lower()
               for r in self.restricciones):
            raise ErrorModelo(
                f"Ya existe una restricción llamada '{restriccion.nombre}'")
        self._validar_coeficientes(restriccion)
        self.restricciones.append(restriccion)

    # -- Presentación -------------------------------------------------------
    def __str__(self) -> str:
        tipo = "Maximizar" if self.es_maximizacion else "Minimizar"
        unidad = f" [{self.unidad_objetivo}]" if self.unidad_objetivo else ""
        nombres = [v.nombre for v in self.variables]
        lineas = [
            f"{tipo} {self.nombre_objetivo}{unidad} = "
            f"{_formatear_lineal(self.coef_objetivo, nombres)}",
            "Sujeto a:",
        ]
        for r in self.restricciones:
            lineas.append(
                f"  {r.nombre}: "
                f"{_formatear_lineal(r.coeficientes, nombres)} "
                f"{r.signo.value} {r.rhs}"
                f"{' ' + r.unidad if r.unidad else ''}")
        lineas.append("  " + ", ".join(nombres) + " >= 0")
        return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------
def _es_apta_primal(restriccion: Restriccion) -> bool:
    """Una restricción es apta para el simplex primal si es '<=' y RHS >= 0."""
    return restriccion.signo is Signo.LE and restriccion.rhs >= 0



def _formatear_lineal(coefs: list[Fraction],
                      nombres: list[str] | None = None) -> str:
    """Convierte [3, -2] en '3·x1 - 2·x2' (omite coeficientes cero)."""
    if nombres is None:
        nombres = [f"x{i + 1}" for i in range(len(coefs))]
    partes: list[str] = []
    for c, nombre in zip(coefs, nombres):
        if c == 0:
            continue
        signo = "-" if c < 0 else "+"
        valor = abs(c)
        termino = nombre if valor == 1 else f"{valor}·{nombre}"
        if not partes:
            partes.append(f"-{termino}" if c < 0 else termino)
        else:
            partes.append(f"{signo} {termino}")
    return " ".join(partes) if partes else "0"


# ---------------------------------------------------------------------------
# Prueba rápida:  python -m core.models
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    problema = Problema(
        tipo=TipoOptimizacion.MAX,
        nombre_objetivo="Utilidad",
        unidad_objetivo="$/semana",
        variables=[
            Variable("Mesas", "unidades/semana"),
            Variable("Sillas", "unidades/semana"),
        ],
        coef_objetivo=[30, 20],
        restricciones=[
            Restriccion("Carpintería", "horas", [2, 1], Signo.LE, 100),
            Restriccion("Acabado", "horas", [1, 1], "<=", 80),
            Restriccion("Demanda de mesas", "unidades", [1, 0], "<=", 40),
        ],
    )
    print(problema)
    print("\n¿Forma canónica (sin artificiales)?", problema.es_forma_canonica)

    # El bug corregido: una restricción inválida NO debe quedar en la lista
    try:
        problema.agregar_restriccion(
            Restriccion("Mala", "u", [1, 1, 1], "<=", 5))
    except ErrorModelo as e:
        print("\nError esperado:", e)
    print("Restricciones tras el fallo:", problema.n_restricciones)
"""
core/standardizer.py
--------------------
Convierte un Problema a la forma estándar que necesita el simplex primal.
 
Hace tres cosas:
  1. Separa las restricciones: las '<=' con RHS >= 0 van al simplex;
     las demás ('>=', '=', RHS negativo) quedan PENDIENTES (se verifican
     después de resolver; si se violan, el caso es para el simplex dual).
  2. Si el problema es de minimizar, lo convierte a maximizar
     (min Z = c·x  <=>  max (-Z) = (-c)·x).
  3. Agrega una variable de holgura a cada restricción incluida.
 
No usa variables artificiales ni de exceso (nada de Gran M / dos fases).
"""
 
from __future__ import annotations
 
from dataclasses import dataclass
from fractions import Fraction
 
from .models import ErrorModelo, Problema, Restriccion
 
 
@dataclass
class ProblemaEstandar:
    """
    Resultado de la estandarización (lo que consume tableau.py).
 
    - coef_z:       coeficientes de la función objetivo YA en forma de
                    maximización (si era min, vienen con el signo cambiado)
    - invertir_z:   True si hay que cambiar el signo del Z final al reportar
    - columnas:     encabezados: x1..xn seguidos de s1..sm
    - matriz:       coeficientes de las restricciones incluidas + holguras
    - rhs:          lado derecho de cada restricción incluida
    - base_inicial: índice de columna de la variable básica de cada fila
                    (las holguras)
    - incluidas:    restricciones que resuelve el simplex (fila i <-> s{i+1})
    - pendientes:   restricciones que NO entran al simplex primal
    """
    problema: Problema
    coef_z: list[Fraction]
    invertir_z: bool
    columnas: list[str]
    matriz: list[list[Fraction]]
    rhs: list[Fraction]
    base_inicial: list[int]
    incluidas: list[Restriccion]
    pendientes: list[Restriccion]
 
    @property
    def n_variables(self) -> int:
        return self.problema.n_variables
 
    @property
    def n_holguras(self) -> int:
        return len(self.incluidas)
 
    @property
    def hay_pendientes(self) -> bool:
        return len(self.pendientes) > 0
 
    def resumen(self) -> str:
        """Texto explicativo de cómo quedó el problema estandarizado."""
        lineas = []
        if self.invertir_z:
            lineas.append("• Minimización convertida a maximización "
                          "(se cambió el signo de Z).")
        lineas.append(f"• {len(self.incluidas)} restricción(es) al simplex "
                      f"(una holgura cada una).")
        for i, r in enumerate(self.incluidas):
            lineas.append(f"    s{i + 1} <- {r.nombre}")
        if self.pendientes:
            lineas.append(f"• {len(self.pendientes)} restricción(es) "
                          f"pendiente(s), se verificarán al final:")
            for r in self.pendientes:
                lineas.append(f"    {r}")
        return "\n".join(lineas)
 
 
def estandarizar(problema: Problema) -> ProblemaEstandar:
    """Convierte `problema` a la forma estándar del simplex primal."""
    incluidas, pendientes = problema.separar_restricciones()
    if not incluidas:
        raise ErrorModelo(
            "Ninguna restricción es apta para el simplex primal "
            "(se necesita al menos una '<=' con lado derecho >= 0).")
 
    n = problema.n_variables
    m = len(incluidas)
 
    # Minimizar -> maximizar
    invertir = not problema.es_maximizacion
    coef_z = [-c if invertir else c for c in problema.coef_objetivo]
 
    # Encabezados
    columnas = ([f"x{j + 1}" for j in range(n)]
                + [f"s{i + 1}" for i in range(m)])
 
    # Matriz [A | I]: coeficientes + una holgura por fila
    matriz = []
    for i, r in enumerate(incluidas):
        holguras = [Fraction(1) if k == i else Fraction(0) for k in range(m)]
        matriz.append(list(r.coeficientes) + holguras)
 
    return ProblemaEstandar(
        problema=problema,
        coef_z=coef_z,
        invertir_z=invertir,
        columnas=columnas,
        matriz=matriz,
        rhs=[r.rhs for r in incluidas],
        base_inicial=[n + i for i in range(m)],
        incluidas=incluidas,
        pendientes=pendientes,
    )
 
 
# ---------------------------------------------------------------------------
# Prueba rápida:  python -m core.standardizer
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from .models import Variable
 
    nombres = ["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8"]
    cotas = [138, 497, 2933, 694, 1014, 36, 22, 696]
 
    restricciones = []
    for j, (nom, cota) in enumerate(zip(nombres, cotas)):
        fila = [0] * 8
        fila[j] = 1
        restricciones.append(Restriccion(f"Límite {nom}", "unidades",
                                         fila, "<=", cota))
    restricciones += [
        Restriccion("Presupuesto", "$",
                    ["1214,98", "739,94", "739,94", "739,94", "739,94",
                     "780,05", "780,05", "1593,27"], "<=", 2500000),
        Restriccion("Despacho", "unidades", [1] * 8, "<=", 4000),
        Restriccion("Capacidad pasta", "unidades",
                    [0, 1, 1, 1, 1, 0, 0, 0], "<=", 2500),
        Restriccion("Complementarios mínimos", "unidades",
                    [0, 0, 0, 0, 0, 1, 1, 0], ">=", 30),
    ]
 
    problema = Problema(
        tipo="max",
        variables=[Variable(n, "unidades") for n in nombres],
        coef_objetivo=[180, 140, 150, 155, 160, 210, 220, 380],
        restricciones=restricciones,
    )
 
    est = estandarizar(problema)
    print(est.resumen())
    print(f"\nMatriz: {len(est.matriz)} filas x {len(est.columnas)} columnas")
    print("Base inicial:", [est.columnas[i] for i in est.base_inicial])
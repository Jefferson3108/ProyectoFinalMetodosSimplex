"""
core/standardizer.py
--------------------
Convierte un Problema a la forma estándar que necesita el simplex primal.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .models import ErrorModelo, Problema, Restriccion


def parsear_a_fraction(val) -> Fraction:
    """
    Convierte cualquier tipo de entrada (int, float, str con comas/puntos o fracciones 'a/b')
    a un objeto Fraction exacto.
    """
    if isinstance(val, Fraction):
        return val
    if isinstance(val, (int, float)):
        return Fraction(str(val))
    
    # Si es cadena de texto, limpiar espacios y reemplazar coma por punto
    s = str(val).strip().replace(',', '.')
    if not s:
        return Fraction(0)
    
    try:
        return Fraction(s)
    except ValueError:
        raise ErrorModelo(f"El valor '{val}' no es un número o fracción válida.")


@dataclass
class ProblemaEstandar:
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
    """Convierte `problema` a la forma estándar del simplex primal con objetos Fraction."""
    incluidas, pendientes = problema.separar_restricciones()
    if not incluidas:
        raise ErrorModelo(
            "Ninguna restricción es apta para el simplex primal "
            "(se necesita al menos una '<=' con lado derecho >= 0).")

    n = problema.n_variables
    m = len(incluidas)

    # Convertir coeficientes de la función objetivo a Fraction
    coef_obj_frac = [parsear_a_fraction(c) for c in problema.coef_objetivo]

    # Minimizar -> maximizar
    invertir = not problema.es_maximizacion
    coef_z = [-c if invertir else c for c in coef_obj_frac]

    # Encabezados
    columnas = ([f"x{j + 1}" for j in range(n)]
                + [f"s{i + 1}" for i in range(m)])

    # Matriz [A | I]: coeficientes + una holgura por fila
    matriz = []
    for i, r in enumerate(incluidas):
        holguras = [Fraction(1) if k == i else Fraction(0) for k in range(m)]
        coef_restriccion = [parsear_a_fraction(c) for c in r.coeficientes]
        matriz.append(coef_restriccion + holguras)

    return ProblemaEstandar(
        problema=problema,
        coef_z=coef_z,
        invertir_z=invertir,
        columnas=columnas,
        matriz=matriz,
        rhs=[parsear_a_fraction(r.rhs) for r in incluidas],
        base_inicial=[n + i for i in range(m)],
        incluidas=incluidas,
        pendientes=pendientes,
    )
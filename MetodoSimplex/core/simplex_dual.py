"""Simplex dual para incorporar restricciones pendientes al tableau óptimo."""

from __future__ import annotations

from fractions import Fraction

from .models import Restriccion
from .simplex import (
    EstadoSimplex,
    Iteracion,
    ResultadoSimplex,
    pivotear,
    resolver as resolver_primal,
)
from .standarizer import ProblemaEstandar
from .table_simplex import Tableau


def resolver(
    est: ProblemaEstandar,
    resultado_primal: ResultadoSimplex | None = None,
    max_iteraciones: int = 1000,
) -> ResultadoSimplex:
    """Resuelve las restricciones pendientes desde el óptimo primal.

    Las restricciones pendientes se agregan al tableau en forma canónica.
    Como el tableau inicial ya es dualmente factible, los pivotes duales
    restauran la factibilidad primal sin perder la optimalidad.
    """
    if resultado_primal is None:
        resultado_primal = resolver_primal(est, max_iteraciones)
    if resultado_primal.estado is not EstadoSimplex.OPTIMA:
        return resultado_primal

    tabla = resultado_primal.tabla_final.copiar()
    tabla.columnas = list(tabla.columnas)
    tabla.matriz_original = [fila.copy()
                             for fila in tabla.matriz_original]
    tabla.rhs_original = list(tabla.rhs_original)
    tabla.coef_z_original = list(tabla.coef_z_original)
    tabla.base_inicial = list(tabla.base_inicial)
    historial: list[Iteracion] = []
    pivotes = 0

    for restriccion in est.pendientes:
        for coeficientes, rhs in _direcciones(restriccion):
            _agregar_fila(tabla, coeficientes, rhs,
                          len(est.problema.variables))

            while True:
                fila = _fila_rhs_negativo(tabla)
                if fila is None:
                    break

                columna, razones = _columna_dual(tabla, fila)
                if columna is None:
                    historial.append(Iteracion(
                        pivotes, tabla.copiar(), razones=razones))
                    return ResultadoSimplex(
                        EstadoSimplex.INFACTIBLE,
                        historial,
                        tabla,
                        "Las restricciones pendientes son incompatibles con "
                        "las restricciones del problema.",
                    )

                historial.append(Iteracion(
                    pivotes, tabla.copiar(), columna, fila, razones))
                if pivotes >= max_iteraciones:
                    return ResultadoSimplex(
                        EstadoSimplex.LIMITE_ITERACIONES,
                        historial,
                        tabla,
                        f"Se superó el límite de {max_iteraciones} pivotes "
                        "del simplex dual.",
                    )
                pivotear(tabla, fila, columna)
                pivotes += 1

    historial.append(Iteracion(pivotes, tabla.copiar()))
    if not est.pendientes:
        mensaje = ("No hay restricciones pendientes; no se requirieron "
                   "pivotes duales.")
    elif pivotes:
        mensaje = "Se alcanzó la solución óptima mediante el simplex dual."
    else:
        mensaje = ("La solución primal ya satisface las restricciones "
                   "pendientes; no se requirieron pivotes duales.")
    return ResultadoSimplex(
        EstadoSimplex.OPTIMA,
        historial,
        tabla,
        mensaje,
    )


def _direcciones(
    restriccion: Restriccion,
) -> list[tuple[list[Fraction], Fraction]]:
    coeficientes = restriccion.coeficientes_frac
    rhs = restriccion.rhs_frac
    signo = restriccion.signo_enum.value
    if signo == "<=":
        return [(coeficientes, rhs)]
    if signo == ">=":
        return [([-coef for coef in coeficientes], -rhs)]
    return [
        (coeficientes, rhs),
        ([-coef for coef in coeficientes], -rhs),
    ]


def _agregar_fila(
    tabla: Tableau,
    coeficientes: list[Fraction],
    rhs: Fraction,
    n_variables: int,
) -> None:
    indice_holgura = len(tabla.columnas)
    nombre_holgura = f"s{indice_holgura - n_variables + 1}"

    for fila in tabla.cuerpo:
        fila.append(Fraction(0))
    tabla.fila_z.append(Fraction(0))
    tabla.columnas.append(nombre_holgura)

    fila_nueva = (list(coeficientes)
                  + [Fraction(0)] * (indice_holgura - n_variables)
                  + [Fraction(1)])
    rhs_nuevo = rhs

    for indice_fila, columna_base in enumerate(tabla.base):
        factor = fila_nueva[columna_base]
        if factor:
            fila_nueva = [valor - factor * valor_base
                          for valor, valor_base in
                          zip(fila_nueva, tabla.cuerpo[indice_fila])]
            rhs_nuevo -= factor * tabla.rhs[indice_fila]

    tabla.cuerpo.append(fila_nueva)
    tabla.rhs.append(rhs_nuevo)
    tabla.base.append(indice_holgura)

    for fila in tabla.matriz_original:
        fila.append(Fraction(0))
    fila_original = (list(coeficientes)
                     + [Fraction(0)] * (indice_holgura - n_variables)
                     + [Fraction(1)])
    tabla.matriz_original.append(fila_original)
    tabla.rhs_original.append(rhs)
    tabla.coef_z_original.append(Fraction(0))
    tabla.base_inicial.append(indice_holgura)


def _fila_rhs_negativo(tabla: Tableau) -> int | None:
    negativas = [i for i, rhs in enumerate(tabla.rhs) if rhs < 0]
    return min(negativas, key=lambda i: tabla.rhs[i]) if negativas else None


def _columna_dual(
    tabla: Tableau,
    fila: int,
) -> tuple[int | None, list[Fraction | None]]:
    razones: list[Fraction | None] = [None] * tabla.n_columnas
    elegida = None
    for columna, coeficiente in enumerate(tabla.cuerpo[fila]):
        reducido = tabla.fila_z[columna]
        if coeficiente < 0 and reducido >= 0:
            razon = reducido / -coeficiente
            razones[columna] = razon
            if elegida is None or razon < razones[elegida]:
                elegida = columna
    return elegida, razones
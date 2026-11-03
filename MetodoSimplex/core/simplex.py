"""
core/simplex.py
---------------
El proceso del simplex primal. Aquí viven TODAS las decisiones y la
operación sobre la tabla:

  - elegir_columna_entrante():  variable que entra (fila Z más negativa)
  - calcular_razones():         RHS / elemento de la columna pivote
  - elegir_fila_saliente():     razón mínima -> variable que sale
  - pivotear():                 Gauss-Jordan sobre la tabla
  - resolver():                 itera todo y guarda el historial

Desempates: siempre se elige el PRIMER índice (la columna o fila de más
a la izquierda / más arriba).

tableau.py solo construye la tabla; este módulo es quien la transforma.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

from .models import ErrorModelo
from .standarizer import ProblemaEstandar
from .table_simplex import Tableau


# ---------------------------------------------------------------------------
# Resultado y historial
# ---------------------------------------------------------------------------
class EstadoSimplex(Enum):
    OPTIMA = "óptima"
    NO_ACOTADA = "no acotada"
    LIMITE_ITERACIONES = "límite de iteraciones"


@dataclass
class Iteracion:
    """
    Una tabla del historial junto con la decisión que se toma sobre ella.
    La última tabla (la óptima) no tiene pivote: col/fila quedan en None.
    """
    numero: int
    tabla: Tableau                       # copia de la tabla ANTES de pivotear
    col_entrante: int | None = None
    fila_saliente: int | None = None
    razones: list[Fraction | None] = field(default_factory=list)

    @property
    def variable_entrante(self) -> str | None:
        if self.col_entrante is None:
            return None
        return self.tabla.columnas[self.col_entrante]

    @property
    def variable_saliente(self) -> str | None:
        if self.fila_saliente is None:
            return None
        return self.tabla.columnas[self.tabla.base[self.fila_saliente]]

    @property
    def elemento_pivote(self) -> Fraction | None:
        if self.fila_saliente is None or self.col_entrante is None:
            return None
        return self.tabla.cuerpo[self.fila_saliente][self.col_entrante]


@dataclass
class ResultadoSimplex:
    estado: EstadoSimplex
    historial: list[Iteracion]
    tabla_final: Tableau
    mensaje: str = ""

    @property
    def n_iteraciones(self) -> int:
        """Cantidad de pivotes realizados."""
        return sum(1 for it in self.historial if it.fila_saliente is not None)


# ---------------------------------------------------------------------------
# Decisiones del simplex
# ---------------------------------------------------------------------------
def elegir_columna_entrante(tabla: Tableau) -> int | None:
    """
    Columna con el valor MÁS NEGATIVO en la fila Z.
    Empate -> la primera. Si no hay negativos, la tabla es óptima (None).
    """
    mejor = None
    for j, z in enumerate(tabla.fila_z):
        if z < 0 and (mejor is None or z < tabla.fila_z[mejor]):
            mejor = j
    return mejor


def calcular_razones(tabla: Tableau, col: int) -> list[Fraction | None]:
    """
    Razón RHS / elemento para cada fila, solo si el elemento es > 0.
    Las filas donde no aplica quedan en None.
    """
    razones: list[Fraction | None] = []
    for i in range(tabla.n_filas):
        a = tabla.cuerpo[i][col]
        razones.append(tabla.rhs[i] / a if a > 0 else None)
    return razones


def elegir_fila_saliente(razones: list[Fraction | None]) -> int | None:
    """
    Fila con la razón MÍNIMA. Empate -> la primera.
    Si ninguna fila tiene razón válida, el problema es no acotado (None).
    """
    mejor = None
    for i, r in enumerate(razones):
        if r is not None and (mejor is None or r < razones[mejor]):
            mejor = i
    return mejor


# ---------------------------------------------------------------------------
# Operación sobre la tabla
# ---------------------------------------------------------------------------
def pivotear(tabla: Tableau, fila: int, col: int) -> None:
    """
    Pivotea (Gauss-Jordan) sobre el elemento (fila, col), modificando `tabla`.
      1. Divide la fila pivote entre el elemento pivote.
      2. Hace cero el resto de la columna (otras filas y fila Z).
      3. La variable de la columna entra a la base en esa fila.
    """
    pivote = tabla.cuerpo[fila][col]
    if pivote == 0:
        raise ErrorModelo("El elemento pivote no puede ser cero")

    # 1. Normalizar la fila pivote
    tabla.cuerpo[fila] = [a / pivote for a in tabla.cuerpo[fila]]
    tabla.rhs[fila] = tabla.rhs[fila] / pivote

    # 2. Eliminar la columna en las demás filas
    for i in range(tabla.n_filas):
        if i == fila:
            continue
        factor = tabla.cuerpo[i][col]
        if factor != 0:
            tabla.cuerpo[i] = [a - factor * p for a, p
                               in zip(tabla.cuerpo[i], tabla.cuerpo[fila])]
            tabla.rhs[i] -= factor * tabla.rhs[fila]

    # ... y en la fila Z
    factor_z = tabla.fila_z[col]
    if factor_z != 0:
        tabla.fila_z = [z - factor_z * p for z, p
                        in zip(tabla.fila_z, tabla.cuerpo[fila])]
        tabla.valor_z -= factor_z * tabla.rhs[fila]

    # 3. Actualizar la base
    tabla.base[fila] = col


# ---------------------------------------------------------------------------
# Algoritmo completo
# ---------------------------------------------------------------------------
def resolver(est: ProblemaEstandar,
             max_iteraciones: int = 1000) -> ResultadoSimplex:
    """
    Ejecuta el simplex primal sobre el problema estandarizado.
    Guarda una copia de cada tabla (con su pivote) en el historial.
    """
    tabla = Tableau.desde_estandar(est)
    historial: list[Iteracion] = []

    for numero in range(max_iteraciones + 1):
        col = elegir_columna_entrante(tabla)

        # Óptima: ninguna columna mejora Z
        if col is None:
            historial.append(Iteracion(numero, tabla.copiar()))
            return ResultadoSimplex(EstadoSimplex.OPTIMA, historial, tabla,
                                    "Se alcanzó la solución óptima.")

        razones = calcular_razones(tabla, col)
        fila = elegir_fila_saliente(razones)
        historial.append(Iteracion(numero, tabla.copiar(), col, fila, razones))

        # No acotada: la columna que mejora Z no tiene límite
        if fila is None:
            return ResultadoSimplex(
                EstadoSimplex.NO_ACOTADA, historial, tabla,
                f"La variable {tabla.columnas[col]} puede aumentar "
                f"indefinidamente sin violar ninguna restricción: "
                f"el problema no tiene solución acotada.")

        pivotear(tabla, fila, col)

    return ResultadoSimplex(
        EstadoSimplex.LIMITE_ITERACIONES, historial, tabla,
        f"Se superó el límite de {max_iteraciones} iteraciones "
        f"(posible ciclo).")


# ---------------------------------------------------------------------------
# Prueba rápida:  python -m core.simplex
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from .models import Problema, Restriccion, Variable
    from .standarizer import estandarizar
    from Utils.formatters import formatear_numero

    problema = Problema(
        tipo="max",
        variables=[Variable("Mesas"), Variable("Sillas")],
        coef_objetivo=[30, 20],
        restricciones=[
            Restriccion("Carpintería", "h", [2, 1], "<=", 100),
            Restriccion("Acabado", "h", [1, 1], "<=", 80),
            Restriccion("Demanda mesas", "u", [1, 0], "<=", 40),
        ],
    )
    res = resolver(estandarizar(problema))

    for it in res.historial:
        print(f"--- Tabla {it.numero} ---")
        print(it.tabla)
        if it.fila_saliente is not None:
            r = ", ".join("-" if x is None else formatear_numero(x)
                          for x in it.razones)
            print(f"Entra {it.variable_entrante}, sale {it.variable_saliente}"
                  f" (razones: {r}; pivote = "
                  f"{formatear_numero(it.elemento_pivote)})")
        print()

    print(f"Estado: {res.estado.value} | pivotes: {res.n_iteraciones}")
    print("Z =", formatear_numero(res.tabla_final.valor_z))
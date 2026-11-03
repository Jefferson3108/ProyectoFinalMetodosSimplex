
"""
Método Simplex Dual.

Resuelve problemas de programación lineal mediante
el simplex dual aplicado al modelo dual matemático.

No utiliza librerías externas de optimización.
"""

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

from .models import ErrorModelo
from .standarizer import ProblemaEstandar
from .table_simplex import Tableau
from .simplex import pivotear


class EstadoDual(Enum):
    OPTIMA = "óptima"
    INFACTIBLE = "infactible"
    LIMITE_ITERACIONES = "límite de iteraciones"


@dataclass
class IteracionDual:
    numero: int
    tabla: Tableau
    fila_pivote: int | None = None
    columna_pivote: int | None = None
    razones: list = field(default_factory=list)

    @property
    def variable_entrante(self):
        if self.columna_pivote is None:
            return None
        return self.tabla.columnas[self.columna_pivote]

    @property
    def variable_saliente(self):
        if self.fila_pivote is None:
            return None
        return self.tabla.etiquetas_base[self.fila_pivote]

    @property
    def pivote(self):
        if self.fila_pivote is None or self.columna_pivote is None:
            return None
        return self.tabla.cuerpo[
            self.fila_pivote
        ][self.columna_pivote]


@dataclass
class ResultadoDual:
    estado: EstadoDual
    historial: list[IteracionDual]
    tabla_final: Tableau
    mensaje: str
    valores_primal: list = field(default_factory=list)
    valor_objetivo: Fraction | None = None
    degeneracion: bool = False

    @property
    def n_iteraciones(self):
        return sum(
            1 for it in self.historial
            if it.fila_pivote is not None
            and it.columna_pivote is not None
        )


def construir_tabla_dual(est):
    """
    Primal: max c'x, Ax <= b, x >= 0.
    Dual:   min b'y, A'y >= c, y >= 0.

    Se transforma el dual para construir su tableau.
    """
    if est.hay_pendientes:
        raise ErrorModelo(
            "Este módulo requiere restricciones <= "
            "con lado derecho no negativo."
        )

    n = est.n_variables
    m = len(est.incluidas)

    A = [fila[:n] for fila in est.matriz]
    b = list(est.rhs)
    c = list(est.coef_z)

    columnas = (
        [f"y{i + 1}" for i in range(m)]
        + [f"s{j + 1}" for j in range(n)]
    )

    matriz = []
    rhs = []

    for j in range(n):
        fila = [-A[i][j] for i in range(m)]
        holguras = [
            Fraction(int(k == j))
            for k in range(n)
        ]

        matriz.append(fila + holguras)
        rhs.append(-c[j])

    # Objetivo transformado: max -b'y.
    fila_z = list(b) + [Fraction(0)] * n

    return Tableau(
        columnas=columnas,
        cuerpo=matriz,
        rhs=rhs,
        fila_z=fila_z,
        valor_z=Fraction(0),
        base=[m + j for j in range(n)],
        matriz_original=[list(f) for f in matriz],
        rhs_original=list(rhs),
        coef_z_original=[-v for v in b],
        base_inicial=[m + j for j in range(n)],
    )


def elegir_fila_pivote(tabla):
    """Selecciona la fila con RHS más negativo."""
    candidatas = [
        i for i in range(tabla.n_filas)
        if tabla.rhs[i] < 0
    ]

    if not candidatas:
        return None

    return min(
        candidatas,
        key=lambda i: (tabla.rhs[i], i)
    )


def calcular_razones_duales(tabla, fila):
    """Calcula zj-cj dividido entre el negativo de aij."""
    razones = []

    for j in range(tabla.n_columnas):
        a = tabla.cuerpo[fila][j]

        if a < 0:
            razones.append(tabla.fila_z[j] / (-a))
        else:
            razones.append(None)

    return razones


def elegir_columna_pivote(razones):
    """Selecciona la menor razón dual válida."""
    candidatas = [
        j for j, razon in enumerate(razones)
        if razon is not None
    ]

    if not candidatas:
        return None

    return min(
        candidatas,
        key=lambda j: (razones[j], j)
    )


def resolver(est, max_iteraciones=1000):
    """Ejecuta el simplex dual y guarda todas las iteraciones."""
    tabla = construir_tabla_dual(est)
    historial = []
    degeneracion = False

    if any(valor < 0 for valor in tabla.fila_z):
        raise ErrorModelo(
            "La tabla inicial no es dual-factible."
        )

    for numero in range(max_iteraciones + 1):
        fila = elegir_fila_pivote(tabla)

        if fila is None:
            historial.append(
                IteracionDual(numero, tabla.copiar())
            )

            m = len(est.incluidas)
            n = est.n_variables

            # Recuperación de la solución primal.
            x = [
                tabla.fila_z[m + j]
                for j in range(n)
            ]

            z = -tabla.valor_z

            if est.invertir_z:
                z = -z

            degeneracion = (
                degeneracion
                or any(valor == 0 for valor in tabla.rhs)
            )

            return ResultadoDual(
                estado=EstadoDual.OPTIMA,
                historial=historial,
                tabla_final=tabla,
                mensaje="Solución óptima encontrada.",
                valores_primal=x,
                valor_objetivo=z,
                degeneracion=degeneracion,
            )

        razones = calcular_razones_duales(tabla, fila)
        columna = elegir_columna_pivote(razones)

        historial.append(
            IteracionDual(
                numero=numero,
                tabla=tabla.copiar(),
                fila_pivote=fila,
                columna_pivote=columna,
                razones=razones,
            )
        )

        if columna is None:
            return ResultadoDual(
                estado=EstadoDual.INFACTIBLE,
                historial=historial,
                tabla_final=tabla,
                mensaje=(
                    "No existe columna pivote válida. "
                    "El problema original es no acotado "
                    "o requiere revisar la formulación."
                ),
                degeneracion=degeneracion,
            )

        if tabla.rhs[fila] == 0:
            degeneracion = True

        pivotear(tabla, fila, columna)

    return ResultadoDual(
        estado=EstadoDual.LIMITE_ITERACIONES,
        historial=historial,
        tabla_final=tabla,
        mensaje="Se alcanzó el límite de iteraciones.",
        degeneracion=degeneracion,
    )

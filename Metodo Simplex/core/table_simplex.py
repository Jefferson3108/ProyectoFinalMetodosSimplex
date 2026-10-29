"""
core/tableau.py
---------------
La tabla simplex: construcción, copia y pivoteo.

Convención de la fila Z:  z_j - c_j
  - Tabla inicial: -c_j bajo las variables de decisión, 0 bajo las holguras.
  - La solución es óptima cuando TODOS los valores de la fila Z son >= 0.

Este módulo solo CONSTRUYE y MUESTRA la tabla. Todo el proceso (elegir el
pivote y ejecutarlo con Gauss-Jordan) vive en simplex.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


from Utils.formatters import formatear_numero

from .standarizer import ProblemaEstandar


@dataclass
class Tableau:
    """
    Una tabla simplex (una "foto" del método).

    Parte que CAMBIA en cada iteración:
      cuerpo   : m filas x N columnas (restricciones)
      rhs      : lado derecho de cada fila
      fila_z   : valores z_j - c_j (N columnas)
      valor_z  : valor actual de Z
      base     : índice de la variable básica de cada fila

    Parte que NO cambia (se conserva para el análisis de sensibilidad):
      columnas, matriz_original, rhs_original, coef_z_original, base_inicial
    """
    columnas: list[str]
    cuerpo: list[list[Fraction]]
    rhs: list[Fraction]
    fila_z: list[Fraction]
    valor_z: Fraction
    base: list[int]

    matriz_original: list[list[Fraction]]
    rhs_original: list[Fraction]
    coef_z_original: list[Fraction]
    base_inicial: list[int]

    # -- Construcción -------------------------------------------------------
    @classmethod
    def desde_estandar(cls, est: ProblemaEstandar) -> "Tableau":
        """Arma la Tabla 0 a partir del problema estandarizado."""
        n_cols = len(est.columnas)
        fila_z = [-c for c in est.coef_z] + [Fraction(0)] * (n_cols - len(est.coef_z))
        return cls(
            columnas=list(est.columnas),
            cuerpo=[list(f) for f in est.matriz],
            rhs=list(est.rhs),
            fila_z=fila_z,
            valor_z=Fraction(0),
            base=list(est.base_inicial),
            matriz_original=[list(f) for f in est.matriz],
            rhs_original=list(est.rhs),
            coef_z_original=list(est.coef_z),
            base_inicial=list(est.base_inicial),
        )

    def copiar(self) -> "Tableau":
        """
        Copia independiente (para guardar en el historial).
        Los Fraction son inmutables, así que basta copiar las listas.
        Las partes 'originales' se comparten porque nunca se modifican.
        """
        return Tableau(
            columnas=self.columnas,
            cuerpo=[list(f) for f in self.cuerpo],
            rhs=list(self.rhs),
            fila_z=list(self.fila_z),
            valor_z=self.valor_z,
            base=list(self.base),
            matriz_original=self.matriz_original,
            rhs_original=self.rhs_original,
            coef_z_original=self.coef_z_original,
            base_inicial=self.base_inicial,
        )

    # -- Consultas ----------------------------------------------------------
    @property
    def n_filas(self) -> int:
        return len(self.cuerpo)

    @property
    def n_columnas(self) -> int:
        return len(self.columnas)

    @property
    def etiquetas_base(self) -> list[str]:
        """Nombre de la variable básica de cada fila."""
        return [self.columnas[j] for j in self.base]

    def valores_columnas(self) -> list[Fraction]:
        """Valor de cada variable (x y s): básicas = RHS, no básicas = 0."""
        valores = [Fraction(0)] * self.n_columnas
        for fila, col in enumerate(self.base):
            valores[col] = self.rhs[fila]
        return valores

    # -- Presentación -------------------------------------------------------
    def como_filas_texto(self, decimales: int = 4) -> list[list[str]]:
        """
        La tabla como lista de filas de texto (encabezado incluido).
        La interfaz puede usarla directamente para dibujar la grilla.
        """
        f = lambda v: formatear_numero(v, decimales)
        filas = [["Base"] + self.columnas + ["RHS"]]
        for i in range(self.n_filas):
            filas.append([self.columnas[self.base[i]]]
                         + [f(a) for a in self.cuerpo[i]] + [f(self.rhs[i])])
        filas.append(["Z"] + [f(z) for z in self.fila_z] + [f(self.valor_z)])
        return filas

    def __str__(self) -> str:
        filas = self.como_filas_texto()
        ancho = max(len(c) for fila in filas for c in fila)
        return "\n".join(" ".join(c.rjust(ancho) for c in fila)
                         for fila in filas)


# ---------------------------------------------------------------------------
# Prueba rápida:  python -m core.tableau
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from .models import Problema, Restriccion, Variable
    from .standarizer import estandarizar

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
    t = Tableau.desde_estandar(estandarizar(problema))
    print("Tabla 0\n" + str(t))

    copia = t.copiar()
    t.rhs[0] = Fraction(999)           # modificar la original...
    print("\n¿La copia quedó independiente?", copia.rhs[0] == 100)
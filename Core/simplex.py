"""
core/simplex.py
---------------
El proceso del simplex primal. Aquí vive:
  - pivotear(): la operación de Gauss-Jordan sobre la tabla
  - (siguiente paso) elegir columna/fila pivote, iterar y guardar historial

tableau.py solo construye la tabla; este módulo es quien la transforma.
"""

from __future__ import annotations

from .models import ErrorModelo
from .tableau import Tableau


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
# Prueba rápida:  python -m core.simplex
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
    antes = t.copiar()
    print("Tabla 0\n" + str(t))

    pivotear(t, fila=2, col=0)         # entra x1, sale s3 (razón mínima 40)
    print("\nTabla 1 (pivote en x1, fila 3)\n" + str(t))
    print("\n¿La copia de la Tabla 0 quedó intacta?",
          antes.valor_z == 0 and antes.base == [2, 3, 4])
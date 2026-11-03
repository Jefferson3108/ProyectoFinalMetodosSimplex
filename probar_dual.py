
from MetodoSimplex.core.models import (
    Problema,
    Variable,
    Restriccion,
)
from MetodoSimplex.core.standarizer import estandarizar
from MetodoSimplex.core.simplex_dual import resolver


problema = Problema(
    tipo="max",
    variables=[
        Variable("Mesas"),
        Variable("Sillas"),
    ],
    coef_objetivo=[30, 20],
    restricciones=[
        Restriccion("R1", "h", [2, 1], "<=", 100),
        Restriccion("R2", "h", [1, 1], "<=", 80),
        Restriccion("R3", "u", [1, 0], "<=", 40),
    ],
)

est = estandarizar(problema)
resultado = resolver(est)

print("\nMÉTODO SIMPLEX DUAL")
print("=" * 50)

for it in resultado.historial:
    print(f"\nTABLA {it.numero}")
    print(it.tabla)

    if it.fila_pivote is not None:
        print("Variable saliente:", it.variable_saliente)

        if it.columna_pivote is not None:
            print("Variable entrante:", it.variable_entrante)
            print("Pivote:", it.pivote)
            print("Razones:", it.razones)

print("\nRESULTADO")
print("Estado:", resultado.estado.value)
print("Iteraciones:", resultado.n_iteraciones)

if resultado.valor_objetivo is not None:
    print("Variables:", resultado.valores_primal)
    print("Z =", resultado.valor_objetivo)

print("Degeneración:", resultado.degeneracion)
print(resultado.mensaje)

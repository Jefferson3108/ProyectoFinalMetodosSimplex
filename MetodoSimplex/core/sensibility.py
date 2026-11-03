"""
core/sensitivity.py
-------------------
Análisis de sensibilidad calculado DESDE LA TABLA ÓPTIMA del simplex.

Entrega, con nombres, unidades y una frase de interpretación:
  - precio sombra de cada restricción
  - rango de cada coeficiente c_j de la función objetivo
  - rango de cada lado derecho b_i
  - costos reducidos

Las restricciones PENDIENTES ('>=' o '<=' con RHS negativo) no están en la
tabla del simplex. Si la solución las cumple, se agregan a la tabla final
como filas extra (sin hacer ningún pivote) y así las 12, 13, ... se leen
igual que las demás. Si alguna se viola, hace falta el simplex dual primero.

Convención: un límite `None` significa infinito (-∞ abajo, +∞ arriba).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

from MetodoSimplex.Utils.formatters import formatear_numero

from .models import ErrorModelo, Restriccion
from .simplex import EstadoSimplex, ResultadoSimplex
from .standarizer import ProblemaEstandar

Limite = Optional[Fraction]     # None = infinito


def _a_fraccion(valor) -> Fraction:
    """Convierte a Fraction lo que venga: int, float, Fraction o texto ('1214,98')."""
    if isinstance(valor, Fraction):
        return valor
    try:
        if isinstance(valor, float):
            return Fraction(str(valor))
        if isinstance(valor, str):
            return Fraction(valor.strip().replace(",", "."))
        return Fraction(valor)
    except (ValueError, ZeroDivisionError, TypeError):
        raise ErrorModelo(f"'{valor}' no es un número válido") from None


def _signo(restriccion) -> str:
    """Devuelve '<=', '>=' o '=' venga el signo como enum Signo o como texto."""
    s = getattr(restriccion.signo, "value", restriccion.signo)
    s = str(s).strip().replace("≤", "<=").replace("≥", ">=")
    return "=" if s == "==" else s


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------
@dataclass
class SensibilidadCoeficiente:
    """Rango de optimalidad del coeficiente c_j de una variable."""
    variable: str
    unidad: str
    coeficiente: Fraction
    minimo: Limite
    maximo: Limite
    es_basica: bool
    costo_reducido: Fraction     # 0 si es básica
    interpretacion: str


@dataclass
class SensibilidadRestriccion:
    """Precio sombra y rango de factibilidad del lado derecho b_i."""
    restriccion: Restriccion
    precio_sombra: Fraction      # cambio de Z por unidad extra de b_i
    rhs: Fraction
    minimo: Limite
    maximo: Limite
    margen: Fraction             # sobrante (<=) o exceso (>=); 0 = agotada
    interpretacion: str

    @property
    def agotada(self) -> bool:
        return self.margen == 0


@dataclass
class ResultadoSensibilidad:
    coeficientes: list[SensibilidadCoeficiente] = field(default_factory=list)
    restricciones: list[SensibilidadRestriccion] = field(default_factory=list)

    def como_texto(self, decimales: int = 4) -> str:
        f = lambda v: formatear_numero(v, decimales)
        lineas = ["PRECIOS SOMBRA Y RANGO DE CADA LADO DERECHO"]
        for s in self.restricciones:
            r = s.restriccion
            lineas.append(
                f"- {r.nombre}: precio sombra = {f(s.precio_sombra)} | "
                f"b = {f(s.rhs)} en [{_lim(s.minimo, True, f)}, "
                f"{_lim(s.maximo, False, f)}]")
            lineas.append(f"    {s.interpretacion}")
        lineas.append("\nRANGO DE CADA COEFICIENTE DE LA FUNCIÓN OBJETIVO")
        for c in self.coeficientes:
            lineas.append(
                f"- {c.variable}: c = {f(c.coeficiente)} en "
                f"[{_lim(c.minimo, True, f)}, {_lim(c.maximo, False, f)}] | "
                f"costo reducido = {f(c.costo_reducido)}")
            lineas.append(f"    {c.interpretacion}")
        return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Tabla final extendida con las restricciones pendientes
# ---------------------------------------------------------------------------
@dataclass
class _TablaExtendida:
    columnas: list[str]
    cuerpo: list[list[Fraction]]
    rhs: list[Fraction]
    fila_z: list[Fraction]
    base: list[int]
    # id(restriccion) -> (columna de su holgura, ¿se multiplicó por -1?)
    holgura_de: dict[int, tuple[int, bool]]


def _extender(est: ProblemaEstandar, res: ResultadoSimplex) -> _TablaExtendida:
    t = res.tabla_final
    n = est.n_variables
    columnas = list(t.columnas)
    cuerpo = [list(f) for f in t.cuerpo]
    rhs = list(t.rhs)
    fila_z = list(t.fila_z)
    base = list(t.base)

    holgura_de = {id(r): (n + i, False) for i, r in enumerate(est.incluidas)}

    for k, r in enumerate(est.pendientes):
        signo = _signo(r)
        if signo == "=":
            raise ErrorModelo(
                f"La restricción de igualdad '{r.nombre}' todavía no es "
                f"compatible con el análisis de sensibilidad.")
        if signo not in ("<=", ">="):
            raise ErrorModelo(f"Signo no reconocido en '{r.nombre}': {signo}")

        # '>=' se multiplica por -1 para dejarla como '<='
        invertida = signo == ">="
        a = [_a_fraccion(c) for c in r.coeficientes]
        b = _a_fraccion(r.rhs)
        if invertida:
            a = [-c for c in a]
            b = -b

        # Columna nueva (holgura de la restricción pendiente)
        for fila in cuerpo:
            fila.append(Fraction(0))
        fila_z.append(Fraction(0))
        columnas.append(f"t{k + 1}")
        col_t = len(columnas) - 1

        nueva = a + [Fraction(0)] * (col_t - n) + [Fraction(1)]
        nuevo_rhs = b

        # Reducir con las filas de las variables básicas (sin pivotear)
        for fila, col_b in enumerate(base):
            coef = nueva[col_b]
            if coef != 0:
                nueva = [x - coef * y for x, y in zip(nueva, cuerpo[fila])]
                nuevo_rhs -= coef * rhs[fila]

        if nuevo_rhs < 0:
            raise ErrorModelo(
                f"La solución viola la restricción '{r.nombre}'. Hace falta "
                f"el simplex dual antes del análisis de sensibilidad.")

        cuerpo.append(nueva)
        rhs.append(nuevo_rhs)
        base.append(col_t)
        holgura_de[id(r)] = (col_t, invertida)

    return _TablaExtendida(columnas, cuerpo, rhs, fila_z, base, holgura_de)


# ---------------------------------------------------------------------------
# Cálculo de rangos
# ---------------------------------------------------------------------------
def _rango_rhs(tab: _TablaExtendida, col: int) -> tuple[Limite, Limite]:
    """
    Cambio permitido Δ del lado derecho cuya holgura es la columna `col`:
    se exige  rhs_r + Δ·T[r][col] >= 0  para toda fila r.
    """
    dmin: Limite = None
    dmax: Limite = None
    for r, valor in enumerate(tab.rhs):
        a = tab.cuerpo[r][col]
        if a == 0:
            continue
        lim = -valor / a
        if a > 0:
            dmin = lim if dmin is None or lim > dmin else dmin
        else:
            dmax = lim if dmax is None or lim < dmax else dmax
    return dmin, dmax


def _rango_coef(tab: _TablaExtendida, col_x: int,
                c: Fraction) -> tuple[Limite, Limite]:
    """Rango de c_j (en forma de maximización) que mantiene la base óptima."""
    if col_x not in tab.base:
        # No básica: puede bajar sin límite y subir hasta su costo reducido
        return None, c + tab.fila_z[col_x]

    r = tab.base.index(col_x)
    en_base = set(tab.base)
    dmin: Limite = None
    dmax: Limite = None
    for k, d in enumerate(tab.fila_z):
        if k in en_base:
            continue
        a = tab.cuerpo[r][k]
        if a == 0:
            continue
        lim = -d / a
        if a > 0:
            dmin = lim if dmin is None or lim > dmin else dmin
        else:
            dmax = lim if dmax is None or lim < dmax else dmax
    return (None if dmin is None else c + dmin,
            None if dmax is None else c + dmax)


def _sumar(b: Fraction, delta: Limite) -> Limite:
    return None if delta is None else b + delta


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def analizar(est: ProblemaEstandar,
             res: ResultadoSimplex) -> ResultadoSensibilidad:
    """Calcula el análisis de sensibilidad a partir de la tabla óptima."""
    if res.estado is not EstadoSimplex.OPTIMA:
        raise ErrorModelo("El análisis de sensibilidad necesita una "
                          "solución óptima.")

    problema = est.problema
    tab = _extender(est, res)
    n = est.n_variables
    signo_z = -1 if est.invertir_z else 1       # min se resolvió como -max
    obj = problema.nombre_objetivo
    u_obj = problema.unidad_objetivo
    f = lambda v: formatear_numero(v)

    salida = ResultadoSensibilidad()

    # ---- Coeficientes de la función objetivo ------------------------------
    for j, var in enumerate(problema.variables):
        c_orig = _a_fraccion(problema.coef_objetivo[j])
        c_max = _a_fraccion(est.coef_z[j])                      # coeficiente en forma max
        lo, hi = _rango_coef(tab, j, c_max)
        if est.invertir_z:                         # volver al problema original
            lo, hi = (None if hi is None else -hi), (None if lo is None else -lo)
        basica = j in tab.base
        d = Fraction(0) if basica else tab.fila_z[j]
        salida.coeficientes.append(SensibilidadCoeficiente(
            var.nombre, var.unidad, c_orig, lo, hi, basica, d,
            _frase_coef(var.nombre, c_orig, lo, hi, basica, d,
                        obj, u_obj, est.invertir_z, f)))

    # ---- Restricciones (en el orden que las ingresó el usuario) -----------
    for r in problema.restricciones:
        col, invertida = tab.holgura_de[id(r)]
        rhs = _a_fraccion(r.rhs)
        y = tab.fila_z[col]
        precio = y * signo_z * (-1 if invertida else 1)

        dmin, dmax = _rango_rhs(tab, col)
        if invertida:      # b' = -b  ->  Δb = -Δb'
            lo = None if dmax is None else rhs - dmax
            hi = None if dmin is None else rhs - dmin
        else:
            lo, hi = _sumar(rhs, dmin), _sumar(rhs, dmax)

        margen = tab.rhs[tab.base.index(col)] if col in tab.base else Fraction(0)
        salida.restricciones.append(SensibilidadRestriccion(
            r, precio, rhs, lo, hi, margen,
            _frase_restriccion(r, precio, lo, hi, margen, obj, u_obj, f)))

    return salida


# ---------------------------------------------------------------------------
# Frases de interpretación
# ---------------------------------------------------------------------------
def _lim(valor: Limite, inferior: bool, f) -> str:
    if valor is None:
        return "-∞" if inferior else "+∞"
    return f(valor)


def _frase_restriccion(r: Restriccion, precio: Fraction, lo: Limite,
                       hi: Limite, margen: Fraction, obj: str, u_obj: str,
                       f) -> str:
    u = f" {r.unidad}" if r.unidad else ""
    uo = f" {u_obj}" if u_obj else ""
    rango = f"[{_lim(lo, True, f)}, {_lim(hi, False, f)}]{u}"
    if precio == 0:
        estado = ("sobran" if _signo(r) == "<=" else "se supera por")
        return (f"'{r.nombre}' no limita la solución ({estado} "
                f"{f(margen)}{u}): mientras su valor esté en {rango}, "
                f"cambiarlo no modifica {obj}.")
    verbo = "aumenta" if precio > 0 else "reduce"
    return (f"Cada unidad adicional de '{r.nombre}' {verbo} {obj} en "
            f"{f(abs(precio))}{uo}; este precio sombra es válido mientras "
            f"el valor esté en {rango}.")


def _frase_coef(nombre: str, c: Fraction, lo: Limite, hi: Limite,
                basica: bool, d: Fraction, obj: str, u_obj: str,
                invertida: bool, f) -> str:
    uo = f" {u_obj}" if u_obj else ""
    rango = f"[{_lim(lo, True, f)}, {_lim(hi, False, f)}]{uo}"
    if basica:
        return (f"Mientras el coeficiente de {nombre} esté en {rango}, la "
                f"solución óptima (cuánto usar de cada variable) no cambia; "
                f"{obj} sí varía.")
    efecto = "aumentaría" if invertida else "reduciría"
    limite = "bajara de" if invertida else "superara"
    cota = lo if invertida else hi
    return (f"{nombre} no entra a la solución. Solo convendría si su "
            f"coeficiente {limite} {_lim(cota, invertida, f)}{uo} "
            f"(hoy es {f(c)}); cada unidad que se forzara {efecto} {obj} "
            f"en {f(d)}{uo}.")


# ---------------------------------------------------------------------------
# Prueba rápida:  python -m core.sensitivity
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from .models import Problema, Variable
    from .simplex import resolver
    from .standarizer import estandarizar

    problema = Problema(
        tipo="max",
        nombre_objetivo="Utilidad", unidad_objetivo="$",
        variables=[Variable("Mesas", "u"), Variable("Sillas", "u")],
        coef_objetivo=[30, 20],
        restricciones=[
            Restriccion("Carpintería", "horas", [2, 1], "<=", 100),
            Restriccion("Acabado", "horas", [1, 1], "<=", 80),
            Restriccion("Demanda mesas", "u", [1, 0], "<=", 40),
            Restriccion("Mínimo de mesas", "u", [1, 0], ">=", 10),
        ],
    )
    est = estandarizar(problema)
    print(analizar(est, resolver(est)).como_texto())
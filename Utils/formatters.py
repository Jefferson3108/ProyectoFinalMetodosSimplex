"""
utils/formatters.py
-------------------
Formato de números para mostrar en pantalla.
El cálculo siempre es exacto (Fraction); solo al MOSTRAR se redondea.
"""
 
from __future__ import annotations
 
from fractions import Fraction
 
 
def formatear_numero(valor: Fraction, decimales: int = 4) -> str:
    """
    Fraction -> texto legible.
        Fraction(5)       -> "5"
        Fraction(3, 2)    -> "1.5"
        Fraction(1, 3)    -> "0.3333"
        Fraction(-1, 7)   -> "-0.1429"
    """
    if valor.denominator == 1:
        return str(valor.numerator)
    texto = f"{float(valor):.{decimales}f}".rstrip("0").rstrip(".")
    return "0" if texto in ("", "-0") else texto
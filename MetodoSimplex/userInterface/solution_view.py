"""
ui/solution_view.py
-------------------
Presenta la `Solucion` (core.solution) de forma legible:
- Banner de estado (óptima / requiere dual / no acotada).
- Valor de la función objetivo.
- Tabla de variables de decisión.
- Tabla de uso de recursos (restricciones '<=' incluidas en el simplex).
- Verificación de restricciones pendientes ('>=', '=').
- Notas (soluciones alternativas).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from MetodoSimplex.Utils.formatters import formatear_numero
from MetodoSimplex.core.simplex import EstadoSimplex
from MetodoSimplex.core.solution import Solucion
from MetodoSimplex.core.standarizer import parsear_a_fraction  # 👈 Import para conversión a Fraction

from .widgets import MarcoDesplazable, fuente_negrita

BANNER = {
    "ok": ("#2e7d32", "✔  "),
    "dual": ("#e65100", "⚠  "),
    "error": ("#c62828", "✖  "),
}


class VistaSolucion(ttk.Frame):
    def __init__(self, master, decimales: int = 4):
        super().__init__(master, padding=10)
        self._decimales = decimales
        self._solucion: Solucion | None = None
        self._marco = MarcoDesplazable(self, desplazar_x=False)
        self._marco.pack(fill="both", expand=True)

        barra = ttk.Frame(self)
        barra.pack(fill="x", pady=(8, 0))

        self._btn_copiar = ttk.Button(
            barra, text="Copiar resultado", command=self._copiar, state="disabled"
        )
        self._btn_copiar.pack(side="right")
        self.limpiar()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def limpiar(self) -> None:
        self._solucion = None
        self._vaciar()
        ttk.Label(
            self._marco.interior,
            foreground="#666666",
            text="Todavía no hay resultados. Define el problema y pulsa «Resolver».",
        ).pack(pady=30)
        self._btn_copiar.configure(state="disabled")

    def mostrar(self, sol: Solucion) -> None:
        self._solucion = sol
        self._vaciar()
        cont = self._marco.interior
        f = lambda v: formatear_numero(parsear_a_fraction(v), self._decimales)

        # 1. Banner
        if sol.es_final:
            tipo = "ok"
        elif sol.estado is EstadoSimplex.OPTIMA:  # óptima pero viola >=, =
            tipo = "dual"
        else:
            tipo = "error"

        color, icono = BANNER[tipo]
        tk.Label(
            cont,
            text=icono + sol.mensaje,
            bg=color,
            fg="white",
            font=fuente_negrita(),
            anchor="w",
            justify="left",
            wraplength=950,
            padx=12,
            pady=10,
        ).pack(fill="x", pady=(0, 10))

        if sol.estado is not EstadoSimplex.OPTIMA:
            self._btn_copiar.configure(state="normal")
            return

        # 2. Valor de Z
        unidad = f" {sol.unidad_objetivo}" if sol.unidad_objetivo else ""
        ttk.Label(
            cont,
            text=f"{sol.nombre_objetivo} = {f(sol.valor_z)}{unidad}",
            font=fuente_negrita(16),
        ).pack(anchor="w", pady=(0, 10))

        # 3. Variables de decisión
        self._seccion(
            cont,
            "Variables de decisión",
            columnas=("Variable", "Valor", "Unidad", "Tipo"),
            anchos=(220, 130, 130, 110),
            filas=[
                (
                    v.nombre,
                    f(v.valor),
                    v.unidad,
                    "Básica" if v.es_basica else "No básica",
                )
                for v in sol.variables
            ],
            etiquetas=[
                "activa" if v.valor != 0 else "cero" for v in sol.variables
            ],
        )

        # 4. Recursos
        if sol.recursos:
            self._seccion(
                cont,
                "Uso de recursos (restricciones ≤)",
                columnas=(
                    "Restricción",
                    "Usado",
                    "Disponible",
                    "Sobrante",
                    "Estado",
                ),
                anchos=(220, 130, 130, 130, 110),
                filas=[
                    (
                        r.nombre,
                        f(r.usado),
                        f(r.disponible),
                        f(r.holgura),
                        "Agotado" if r.agotado else "Con holgura",
                    )
                    for r in sol.recursos
                ],
                etiquetas=[
                    "agotado" if r.agotado else "libre" for r in sol.recursos
                ],
            )

        # 5. Restricciones pendientes (Manejo seguro de signo y conversion a Fraction)
        if sol.pendientes:
            filas_pendientes = []
            for p in sol.pendientes:
                signo_str = (
                    p.restriccion.signo.value
                    if hasattr(p.restriccion.signo, "value")
                    else str(p.restriccion.signo)
                )
                filas_pendientes.append(
                    (
                        p.restriccion.nombre,
                        f(p.lado_izquierdo),
                        f"{signo_str} {f(p.restriccion.rhs)}",
                        "Se cumple" if p.se_cumple else "SE VIOLA",
                    )
                )

            self._seccion(
                cont,
                "Restricciones verificadas después del simplex",
                columnas=(
                    "Restricción",
                    "Lado izquierdo",
                    "Condición",
                    "Resultado",
                ),
                anchos=(220, 130, 160, 110),
                filas=filas_pendientes,
                etiquetas=[
                    "libre" if p.se_cumple else "viola" for p in sol.pendientes
                ],
            )

        # 6. Notas
        if sol.posibles_soluciones_multiples:
            ttk.Label(
                cont,
                wraplength=950,
                justify="left",
                text=(
                    "Nota: hay una variable no básica con costo reducido 0; "
                    "pueden existir soluciones óptimas alternativas."
                ),
            ).pack(anchor="w", pady=(6, 0))

        self._marco.ir_al_inicio()
        self._btn_copiar.configure(state="normal")

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _vaciar(self) -> None:
        for w in self._marco.interior.winfo_children():
            w.destroy()

    def _seccion(
        self, padre, titulo, columnas, anchos, filas, etiquetas
    ) -> None:
        marco = ttk.LabelFrame(padre, text=titulo, padding=6)
        marco.pack(fill="x", pady=(0, 10))

        tabla = ttk.Treeview(
            marco,
            columns=columnas,
            show="headings",
            height=max(len(filas), 1),
            selectmode="none",
        )

        for k, (col, ancho) in enumerate(zip(columnas, anchos)):
            tabla.heading(col, text=col, anchor="w" if k == 0 else "e")
            tabla.column(
                col,
                width=ancho,
                minwidth=60,
                anchor="w" if k == 0 else "e",
                stretch=(k == 0),
            )

        tabla.tag_configure("agotado", background="#fde3c8")
        tabla.tag_configure("viola", background="#f8c9c9")
        tabla.tag_configure("cero", foreground="#888888")
        tabla.tag_configure("activa")
        tabla.tag_configure("libre")

        for fila, etiqueta in zip(filas, etiquetas):
            tabla.insert("", "end", values=fila, tags=(etiqueta,))

        tabla.pack(fill="x")

    def _copiar(self) -> None:
        if self._solucion is None:
            return
        self.clipboard_clear()
        self.clipboard_append(self._solucion.como_texto(self._decimales))
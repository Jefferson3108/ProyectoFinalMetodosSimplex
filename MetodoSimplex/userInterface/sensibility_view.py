"""
userInterface/sensitivity_view.py
---------------------------------
Presenta el análisis de sensibilidad (core.sensitivity) de forma legible:
- Tabla de restricciones: precio sombra y rango del lado derecho.
- Tabla de variables: rango del coeficiente en Z y costo reducido.
- Una frase de interpretación por cada resultado.
- Mensaje cuando el análisis no se puede calcular (p. ej. requiere dual).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from MetodoSimplex.Utils.formatters import formatear_numero
from MetodoSimplex.core.sensibility import ResultadoSensibilidad

from .widgets import MarcoDesplazable, fuente_negrita

COLOR_AVISO = "#e65100"


class VistaSensibilidad(ttk.Frame):
    def __init__(self, master, decimales: int = 4):
        super().__init__(master, padding=10)
        self._decimales = decimales
        self._sens: ResultadoSensibilidad | None = None
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
        self._sens = None
        self._vaciar()
        ttk.Label(
            self._marco.interior,
            foreground="#666666",
            text="Todavía no hay resultados. Define el problema y pulsa «Resolver».",
        ).pack(pady=30)
        self._btn_copiar.configure(state="disabled")

    def mostrar(self, sens: ResultadoSensibilidad | None, motivo: str = "") -> None:
        """Muestra el análisis; si `sens` es None, muestra `motivo` como aviso."""
        self._sens = sens
        self._vaciar()
        cont = self._marco.interior

        if sens is None:
            tk.Label(
                cont,
                text="⚠  Análisis de sensibilidad no disponible. " + motivo,
                bg=COLOR_AVISO,
                fg="white",
                font=fuente_negrita(),
                anchor="w",
                justify="left",
                wraplength=950,
                padx=12,
                pady=10,
            ).pack(fill="x", pady=(0, 10))
            self._marco.ir_al_inicio()
            self._btn_copiar.configure(state="disabled")
            return

        f = lambda v: formatear_numero(v, self._decimales)
        inf = lambda v, inferior: ("-∞" if inferior else "+∞") if v is None else f(v)

        ttk.Label(
            cont,
            wraplength=950,
            justify="left",
            foreground="#444444",
            text=(
                "Calculado desde la tabla óptima del simplex. Un límite «-∞» o «+∞» "
                "significa que no hay tope en ese sentido."
            ),
        ).pack(anchor="w", pady=(0, 10))

        # 1. Restricciones
        self._seccion(
            cont,
            "Restricciones: precio sombra y rango del lado derecho",
            columnas=(
                "Restricción",
                "Precio sombra",
                "Valor actual",
                "Mínimo",
                "Máximo",
                "Unidad",
                "Estado",
            ),
            anchos=(220, 125, 120, 120, 120, 90, 100),
            filas=[
                (
                    s.restriccion.nombre,
                    f(s.precio_sombra),
                    f(s.rhs),
                    inf(s.minimo, True),
                    inf(s.maximo, False),
                    s.restriccion.unidad,
                    "Agotada" if s.agotada else "Con holgura",
                )
                for s in sens.restricciones
            ],
            etiquetas=["agotado" if s.agotada else "libre" for s in sens.restricciones],
        )
        self._interpretacion(
            cont, [s.interpretacion for s in sens.restricciones]
        )

        # 2. Variables
        self._seccion(
            cont,
            "Variables: rango del coeficiente en la función objetivo",
            columnas=(
                "Variable",
                "Coeficiente actual",
                "Mínimo",
                "Máximo",
                "Costo reducido",
                "Tipo",
            ),
            anchos=(220, 150, 120, 120, 125, 110),
            filas=[
                (
                    c.variable,
                    f(c.coeficiente),
                    inf(c.minimo, True),
                    inf(c.maximo, False),
                    f(c.costo_reducido),
                    "Básica" if c.es_basica else "No básica",
                )
                for c in sens.coeficientes
            ],
            etiquetas=["activa" if c.es_basica else "cero" for c in sens.coeficientes],
        )
        self._interpretacion(
            cont, [c.interpretacion for c in sens.coeficientes]
        )

        self._marco.ir_al_inicio()
        self._btn_copiar.configure(state="normal")

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _vaciar(self) -> None:
        for w in self._marco.interior.winfo_children():
            w.destroy()

    def _seccion(self, padre, titulo, columnas, anchos, filas, etiquetas) -> None:
        marco = ttk.LabelFrame(padre, text=titulo, padding=6)
        marco.pack(fill="x", pady=(0, 4))

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
        tabla.tag_configure("cero", foreground="#888888")
        tabla.tag_configure("activa")
        tabla.tag_configure("libre")

        for fila, etiqueta in zip(filas, etiquetas):
            tabla.insert("", "end", values=fila, tags=(etiqueta,))
        tabla.pack(fill="x")

    def _interpretacion(self, padre, frases: list[str]) -> None:
        marco = ttk.LabelFrame(padre, text="Qué significa", padding=6)
        marco.pack(fill="x", pady=(0, 12))
        for frase in frases:
            ttk.Label(
                marco,
                text="•  " + frase,
                wraplength=930,
                justify="left",
            ).pack(anchor="w", pady=1)

    def _copiar(self) -> None:
        if self._sens is None:
            return
        self.clipboard_clear()
        self.clipboard_append(self._sens.como_texto(self._decimales))
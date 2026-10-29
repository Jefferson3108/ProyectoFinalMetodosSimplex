"""
ui/widgets.py
-------------
Widget auxiliar compartido por las vistas: un marco con barras de
desplazamiento (Tkinter no trae uno hecho).

Uso:
    marco = MarcoDesplazable(padre)
    ttk.Label(marco.interior, text="hola").pack()
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont


def fuente_negrita(tamano: int | None = None) -> tkfont.Font:
    """Copia en negrita de la fuente por defecto (requiere ventana creada)."""
    f = tkfont.nametofont("TkDefaultFont").copy()
    f.configure(weight="bold")
    if tamano:
        f.configure(size=tamano)
    return f


class MarcoDesplazable(ttk.Frame):
    """
    Marco con scroll vertical (y horizontal opcional). Los widgets hijos se
    colocan dentro de `self.interior`.

    desplazar_x=False -> el contenido se estira al ancho disponible y solo
                         hay scroll vertical.
    """

    def __init__(self, master, desplazar_x: bool = True, **kwargs):
        super().__init__(master, **kwargs)
        self._desplazar_x = desplazar_x

        fondo = ttk.Style(self).lookup("TFrame", "background") or "#f0f0f0"
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=fondo)
        self._vsb = ttk.Scrollbar(self, orient="vertical",
                                  command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._vsb.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self._vsb.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        if desplazar_x:
            self._hsb = ttk.Scrollbar(self, orient="horizontal",
                                      command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=self._hsb.set)
            self._hsb.grid(row=1, column=0, sticky="ew")

        self.interior = ttk.Frame(self.canvas)
        self._ventana = self.canvas.create_window((0, 0), window=self.interior,
                                                  anchor="nw")
        self.interior.bind("<Configure>", self._actualizar_region)
        self.canvas.bind("<Configure>", self._al_cambiar_tamano)

        # La rueda del ratón solo actúa mientras el puntero está encima
        self.canvas.bind("<Enter>", self._activar_rueda)
        self.canvas.bind("<Leave>", self._desactivar_rueda)

    # -- Región desplazable -------------------------------------------------
    def _actualizar_region(self, _evento=None) -> None:
        ancho = max(self.interior.winfo_reqwidth(), self.canvas.winfo_width())
        alto = max(self.interior.winfo_reqheight(), self.canvas.winfo_height())
        self.canvas.configure(scrollregion=(0, 0, ancho, alto))

    def _al_cambiar_tamano(self, evento) -> None:
        if not self._desplazar_x:
            self.canvas.itemconfigure(self._ventana, width=evento.width)
        self._actualizar_region()

    def ir_al_inicio(self) -> None:
        self.canvas.yview_moveto(0)
        if self._desplazar_x:
            self.canvas.xview_moveto(0)

    # -- Rueda del ratón ----------------------------------------------------
    def _activar_rueda(self, _evento=None) -> None:
        self.canvas.bind_all("<MouseWheel>", self._rueda)     # Windows / macOS
        self.canvas.bind_all("<Button-4>", self._rueda)       # Linux
        self.canvas.bind_all("<Button-5>", self._rueda)

    def _desactivar_rueda(self, _evento=None) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _rueda(self, evento) -> None:
        if evento.num == 4:
            paso = -1
        elif evento.num == 5:
            paso = 1
        else:
            paso = -1 if evento.delta > 0 else 1
        con_shift = bool(evento.state & 0x1)
        if con_shift and self._desplazar_x:
            self.canvas.xview_scroll(paso, "units")
        elif self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(paso, "units")
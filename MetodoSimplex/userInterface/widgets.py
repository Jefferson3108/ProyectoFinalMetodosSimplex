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

PALETA = {
    "fondo": "#1C1B22",
    "superficie": "#25242C",
    "superficie_sutil": "#34333D",
    "texto": "#F9F9FB",
    "texto_secundario": "#C4C3CA",
    "borde": "#000000",
    "primario": "#45A1FF",
    "primario_hover": "#75B8FF",
    "positivo": "#287A55",
    "aviso": "#8A5B12",
    "error": "#963B46",
}


def configurar_estilos(root: tk.Misc) -> None:
    """Aplica el tema compartido de la interfaz a los widgets ttk."""
    estilo = ttk.Style(root)
    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")

    for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont",
                   "TkHeadingFont"):
        tkfont.nametofont(nombre).configure(family="Segoe UI", size=10)

    root.configure(background=PALETA["fondo"])
    estilo.configure("TFrame", background=PALETA["fondo"])
    estilo.configure("Header.TFrame", background=PALETA["superficie"])
    estilo.configure("Accent.TFrame", background=PALETA["primario"])
    estilo.configure("TLabel", background=PALETA["fondo"],
                     foreground=PALETA["texto"], font=("Segoe UI", 10))
    estilo.configure("Header.Kicker.TLabel", background=PALETA["superficie"],
                     foreground=PALETA["primario"],
                     font=("Segoe UI", 9, "bold"))
    estilo.configure("Header.Title.TLabel", background=PALETA["superficie"],
                     foreground=PALETA["texto"],
                     font=("Segoe UI", 23, "bold"))
    estilo.configure("Header.Subtitle.TLabel",
                     background=PALETA["superficie"],
                     foreground=PALETA["texto_secundario"],
                     font=("Segoe UI", 10))
    estilo.configure("TLabelframe", background=PALETA["superficie"],
                     borderwidth=1, bordercolor=PALETA["borde"],
                     lightcolor=PALETA["borde"],
                     darkcolor=PALETA["borde"],
                     relief="solid")
    estilo.configure("TLabelframe.Label", background=PALETA["superficie"],
                     foreground=PALETA["texto"],
                     font=("Segoe UI", 10, "bold"))

    estilo.configure("TNotebook", background=PALETA["fondo"],
                     borderwidth=1, bordercolor=PALETA["borde"],
                     lightcolor=PALETA["borde"], darkcolor=PALETA["borde"],
                     tabmargins=(0, 0, 0, 0))
    estilo.configure("TNotebook.Tab", background=PALETA["superficie_sutil"],
                     foreground=PALETA["texto_secundario"],
                     bordercolor=PALETA["borde"],
                     lightcolor=PALETA["borde"],
                     darkcolor=PALETA["borde"],
                     padding=(12, 8), borderwidth=1, relief="solid",
                     font=("Segoe UI", 10, "bold"))
    estilo.map("TNotebook.Tab",
               padding=[("selected", (12, 8)), ("!selected", (12, 8))],
               background=[("selected", PALETA["superficie"]),
                           ("active", "#303B48")],
               foreground=[("selected", PALETA["primario"]),
                           ("active", PALETA["texto"])])

    estilo.configure("TButton", background=PALETA["superficie"],
                     foreground=PALETA["texto"],
                     bordercolor=PALETA["borde"], borderwidth=1,
                     lightcolor=PALETA["borde"],
                     darkcolor=PALETA["borde"],
                     relief="solid", padding=(12, 8),
                     font=("Segoe UI", 10))
    estilo.map("TButton", background=[("pressed", "#303B48"),
                                       ("active", "#293440")])
    estilo.configure("TMenubutton", background=PALETA["superficie"],
                     foreground=PALETA["texto"],
                     bordercolor=PALETA["borde"], borderwidth=1,
                     lightcolor=PALETA["borde"],
                     darkcolor=PALETA["borde"],
                     relief="solid", padding=(12, 8),
                     font=("Segoe UI", 10))
    estilo.map("TMenubutton", background=[("pressed", "#303B48"),
                                          ("active", "#293440")])
    estilo.configure("Primary.TButton", background=PALETA["primario"],
                     foreground="#101116",
                     bordercolor=PALETA["borde"], borderwidth=1,
                     lightcolor=PALETA["borde"],
                     darkcolor=PALETA["borde"],
                     relief="solid",
                     padding=(16, 9), font=("Segoe UI", 10, "bold"))
    estilo.map("Primary.TButton",
               background=[("disabled", "#394654"),
                           ("pressed", PALETA["primario_hover"]),
                           ("active", PALETA["primario_hover"])],
               foreground=[("disabled", "#A1ADBA"),
                           ("!disabled", "#101116")])

    estilo.configure("TEntry", fieldbackground=PALETA["superficie"],
                     foreground=PALETA["texto"], insertcolor=PALETA["texto"],
                     bordercolor=PALETA["borde"], borderwidth=1,
                     lightcolor=PALETA["borde"],
                     darkcolor=PALETA["borde"],
                     relief="solid", padding=7)
    estilo.map("TEntry", bordercolor=[("focus", PALETA["borde"])])
    estilo.configure("TCombobox", fieldbackground=PALETA["superficie"],
                     foreground=PALETA["texto"],
                     bordercolor=PALETA["borde"], borderwidth=1,
                     lightcolor=PALETA["borde"],
                     darkcolor=PALETA["borde"],
                     relief="solid", padding=6)
    estilo.map("TCombobox", fieldbackground=[("readonly", PALETA["superficie"])],
               selectbackground=[("readonly", PALETA["superficie"])],
               selectforeground=[("readonly", PALETA["texto"])])

    estilo.configure("Treeview", background=PALETA["superficie"],
                     fieldbackground=PALETA["superficie"],
                     foreground=PALETA["texto"], rowheight=30,
                     bordercolor=PALETA["borde"], borderwidth=1,
                     lightcolor=PALETA["borde"],
                     darkcolor=PALETA["borde"],
                     relief="solid", font=("Segoe UI", 10))
    estilo.configure("Treeview.Heading", background=PALETA["superficie_sutil"],
                     foreground=PALETA["texto"],
                     borderwidth=1, bordercolor=PALETA["borde"],
                     relief="solid", lightcolor=PALETA["borde"],
                     darkcolor=PALETA["borde"],
                     font=("Segoe UI", 10, "bold"), padding=(8, 8))
    estilo.map("Treeview", background=[("selected", "#29445A")],
               foreground=[("selected", PALETA["texto"])])
    estilo.configure("TSeparator", background=PALETA["borde"])

    estilo.configure("Vertical.TScrollbar", background=PALETA["superficie_sutil"],
                     troughcolor=PALETA["fondo"], bordercolor=PALETA["borde"],
                     borderwidth=1, relief="solid",
                     arrowcolor=PALETA["texto_secundario"])
    estilo.configure("Horizontal.TScrollbar",
                     background=PALETA["superficie_sutil"],
                     troughcolor=PALETA["fondo"], bordercolor=PALETA["borde"],
                     borderwidth=1, relief="solid",
                     arrowcolor=PALETA["texto_secundario"])


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
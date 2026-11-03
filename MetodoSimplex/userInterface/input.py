"""
ui/input.py
-----------
Panel de entrada: el usuario define el problema de programación lineal.

  - Tipo de optimización y nombre/unidad de la función objetivo.
  - Variables de decisión (nombre, unidad, coeficiente en Z).
  - Restricciones (nombre, unidad, coeficientes, signo, lado derecho).
  - Ejemplos precargados (incluye el caso DM&E).

Esta clase NO resuelve nada: construye un `Problema` (core.models) y avisa
a la ventana principal mediante el callback `on_resolver`.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from MetodoSimplex.core.models import Problema, Restriccion, Variable

from .widgets import MarcoDesplazable, fuente_negrita

SIGNOS = ("<=", ">=", "=")

# ---------------------------------------------------------------------------
# Ejemplos: (tipo, nombre_obj, unidad_obj, variables, coef_obj, restricciones)
#   variables:     [(nombre, unidad), ...]
#   restricciones: [(nombre, unidad, coeficientes, signo, rhs), ...]
# ---------------------------------------------------------------------------
def _ejemplo_dme() -> dict:
    nombres = ["Servilletas", "Macarrón", "Spaghetti", "Macarroncito",
               "Concha", "Salsa tomate", "Mayonesa", "Polvo hornear"]
    cotas = [138, 497, 2933, 694, 1014, 36, 22, 696]
    n = len(nombres)

    restricciones = []
    for j, (nom, cota) in enumerate(zip(nombres, cotas)):
        fila = ["0"] * n
        fila[j] = "1"
        restricciones.append((f"Demanda {nom}", "unidades", fila, "<=",
                              str(cota)))
    restricciones += [
        ("Presupuesto de compra", "COP",
         ["1214,98", "739,94", "739,94", "739,94", "739,94",
          "780,05", "780,05", "1593,27"], "<=", "2500000"),
        ("Capacidad de despacho", "unidades", ["1"] * n, "<=", "4000"),
        ("Capacidad de pasta", "unidades",
         ["0", "1", "1", "1", "1", "0", "0", "0"], "<=", "2500"),
        ("Mínimo complementarios", "unidades",
         ["0", "0", "0", "0", "0", "1", "1", "0"], ">=", "30"),
    ]
    return dict(
        tipo="Maximizar", nombre_obj="Ganancia total", unidad_obj="COP",
        variables=[(nom, "unidades") for nom in nombres],
        coef_obj=["180", "140", "150", "155", "160", "210", "220", "380"],
        restricciones=restricciones)


def _ejemplo_simple() -> dict:
    return dict(
        tipo="Maximizar", nombre_obj="Utilidad", unidad_obj="$/semana",
        variables=[("Mesas", "unidades"), ("Sillas", "unidades")],
        coef_obj=["30", "20"],
        restricciones=[
            ("Carpintería", "horas", ["2", "1"], "<=", "100"),
            ("Acabado", "horas", ["1", "1"], "<=", "80"),
            ("Demanda de mesas", "unidades", ["1", "0"], "<=", "40"),
        ])


def _ejemplo_con_mayor_igual() -> dict:
    ej = _ejemplo_simple()
    ej["restricciones"].append(
        ("Mínimo de mesas", "unidades", ["1", "0"], ">=", "25"))
    return ej


EJEMPLOS = {
    "Caso DM&E (8 productos)": _ejemplo_dme,
    "Ejemplo simple (mesas y sillas)": _ejemplo_simple,
    "Ejemplo con restricción ≥ (requiere dual)": _ejemplo_con_mayor_igual,
}


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------
class PanelEntrada(ttk.Frame):
    """
    Formulario del problema. Mantiene el estado en listas de StringVar y
    redibuja la cuadrícula cuando cambia el número de variables o
    restricciones (así no se pierde lo que el usuario ya escribió).
    """

    def __init__(self, master, on_resolver):
        super().__init__(master, padding=10)
        self._on_resolver = on_resolver

        # Datos del objetivo
        self._tipo = tk.StringVar(value="Maximizar")
        self._nombre_obj = tk.StringVar(value="Z")
        self._unidad_obj = tk.StringVar()

        # Variables (listas paralelas, una posición por variable)
        self._nombres_var: list[tk.StringVar] = []
        self._unidades_var: list[tk.StringVar] = []
        self._coef_obj: list[tk.StringVar] = []

        # Restricciones: lista de dicts con StringVar
        self._filas: list[dict] = []

        self._crear_barra_superior()
        self._marco = MarcoDesplazable(self)
        self._marco.pack(fill="both", expand=True, pady=8)
        self._crear_barra_inferior()

        self.cargar_ejemplo("Caso DM&E (8 productos)")

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_barra_superior(self) -> None:
        barra = ttk.LabelFrame(self, text="Función objetivo", padding=8)
        barra.pack(fill="x")

        ttk.Label(barra, text="Tipo:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(barra, textvariable=self._tipo, state="readonly",
                     values=("Maximizar", "Minimizar"),
                     width=12).grid(row=0, column=1, padx=(4, 16))

        ttk.Label(barra, text="Nombre:").grid(row=0, column=2, sticky="w")
        ttk.Entry(barra, textvariable=self._nombre_obj,
                  width=20).grid(row=0, column=3, padx=(4, 16))

        ttk.Label(barra, text="Unidad:").grid(row=0, column=4, sticky="w")
        ttk.Entry(barra, textvariable=self._unidad_obj,
                  width=12).grid(row=0, column=5, padx=4)

    def _crear_barra_inferior(self) -> None:
        barra = ttk.Frame(self)
        barra.pack(fill="x")

        ttk.Button(barra, text="+ Variable",
                   command=self.agregar_variable).pack(side="left", padx=2)
        ttk.Button(barra, text="− Variable",
                   command=self.quitar_variable).pack(side="left", padx=2)
        ttk.Button(barra, text="+ Restricción",
                   command=self.agregar_restriccion).pack(side="left",
                                                          padx=(12, 2))
        ttk.Button(barra, text="− Restricción",
                   command=self.quitar_restriccion).pack(side="left", padx=2)

        menu_btn = ttk.Menubutton(barra, text="Cargar ejemplo ▾")
        menu = tk.Menu(menu_btn, tearoff=False)
        for nombre in EJEMPLOS:
            menu.add_command(label=nombre,
                             command=lambda n=nombre: self.cargar_ejemplo(n))
        menu_btn["menu"] = menu
        menu_btn.pack(side="left", padx=(12, 2))

        ttk.Button(barra, text="Limpiar",
                   command=self.limpiar).pack(side="left", padx=2)

        ttk.Button(barra, text="Resolver con simplex primal  ▶",
                   command=self._on_resolver).pack(side="right", padx=2)

        ttk.Label(self, foreground="#666666",
                  text="Se aceptan decimales con coma o punto y fracciones "
                       "(ej. 1214,98 o 3/2). Una celda vacía vale 0."
                  ).pack(anchor="w", pady=(6, 0))

    # ------------------------------------------------------------------
    # Dibujo de la cuadrícula (se rehace al cambiar el tamaño)
    # ------------------------------------------------------------------
    def _dibujar(self) -> None:
        g = self._marco.interior
        for w in g.winfo_children():
            w.destroy()

        n = len(self._nombres_var)
        c0 = 2                     # primera columna de variables
        c_signo = c0 + n
        c_rhs = c0 + n + 1

        negrita_f = fuente_negrita()

        def etiqueta(texto, fila, col, negrita=False, **grid):
            lbl = ttk.Label(g, text=texto,
                            font=negrita_f if negrita else None)
            lbl.grid(row=fila, column=col, padx=3, pady=2, **grid)
            return lbl

        # --- Bloque de variables -----------------------------------------
        etiqueta("Variables de decisión", 0, 0, True, sticky="w",
                 columnspan=2)
        for j in range(n):
            etiqueta(f"x{j + 1}", 0, c0 + j, True)

        etiqueta("Nombre", 1, 0, sticky="w")
        etiqueta("Unidad", 2, 0, sticky="w")
        etiqueta("Coef. en Z", 3, 0, sticky="w")
        for j in range(n):
            ttk.Entry(g, textvariable=self._nombres_var[j], width=13
                      ).grid(row=1, column=c0 + j, padx=3, pady=2)
            ttk.Entry(g, textvariable=self._unidades_var[j], width=13
                      ).grid(row=2, column=c0 + j, padx=3, pady=2)
            ttk.Entry(g, textvariable=self._coef_obj[j], width=13,
                      justify="right"
                      ).grid(row=3, column=c0 + j, padx=3, pady=2)

        ttk.Separator(g, orient="horizontal").grid(
            row=4, column=0, columnspan=c_rhs + 1, sticky="ew", pady=8)

        # --- Bloque de restricciones -------------------------------------
        etiqueta("Restricción", 5, 0, True, sticky="w")
        etiqueta("Unidad", 5, 1, True, sticky="w")
        for j in range(n):
            etiqueta(f"x{j + 1}", 5, c0 + j, True)
        etiqueta("Signo", 5, c_signo, True)
        etiqueta("Lado derecho", 5, c_rhs, True)

        for i, fila in enumerate(self._filas):
            r = 6 + i
            ttk.Entry(g, textvariable=fila["nombre"], width=26
                      ).grid(row=r, column=0, padx=3, pady=2)
            ttk.Entry(g, textvariable=fila["unidad"], width=10
                      ).grid(row=r, column=1, padx=3, pady=2)
            for j in range(n):
                ttk.Entry(g, textvariable=fila["coefs"][j], width=13,
                          justify="right"
                          ).grid(row=r, column=c0 + j, padx=3, pady=2)
            ttk.Combobox(g, textvariable=fila["signo"], values=SIGNOS,
                         state="readonly", width=4
                         ).grid(row=r, column=c_signo, padx=3, pady=2)
            ttk.Entry(g, textvariable=fila["rhs"], width=14, justify="right"
                      ).grid(row=r, column=c_rhs, padx=3, pady=2)

    # ------------------------------------------------------------------
    # Modificación del tamaño del problema
    # ------------------------------------------------------------------
    def agregar_variable(self, nombre: str = "", unidad: str = "",
                         coef: str = "0", redibujar: bool = True) -> None:
        n = len(self._nombres_var)
        self._nombres_var.append(tk.StringVar(value=nombre or f"x{n + 1}"))
        self._unidades_var.append(tk.StringVar(value=unidad))
        self._coef_obj.append(tk.StringVar(value=coef))
        for fila in self._filas:
            fila["coefs"].append(tk.StringVar(value="0"))
        if redibujar:
            self._dibujar()

    def quitar_variable(self) -> None:
        if len(self._nombres_var) <= 1:
            return
        self._nombres_var.pop()
        self._unidades_var.pop()
        self._coef_obj.pop()
        for fila in self._filas:
            fila["coefs"].pop()
        self._dibujar()

    def agregar_restriccion(self, nombre: str = "", unidad: str = "",
                            coefs: list[str] | None = None,
                            signo: str = "<=", rhs: str = "0",
                            redibujar: bool = True) -> None:
        n = len(self._nombres_var)
        coefs = list(coefs) if coefs is not None else ["0"] * n
        self._filas.append({
            "nombre": tk.StringVar(
                value=nombre or f"Restricción {len(self._filas) + 1}"),
            "unidad": tk.StringVar(value=unidad),
            "coefs": [tk.StringVar(value=c) for c in coefs],
            "signo": tk.StringVar(value=signo),
            "rhs": tk.StringVar(value=rhs),
        })
        if redibujar:
            self._dibujar()

    def quitar_restriccion(self) -> None:
        if len(self._filas) <= 1:
            return
        self._filas.pop()
        self._dibujar()

    # ------------------------------------------------------------------
    # Cargar / limpiar
    # ------------------------------------------------------------------
    def cargar_ejemplo(self, nombre: str) -> None:
        ej = EJEMPLOS[nombre]()
        self._reiniciar_estado()
        self._tipo.set(ej["tipo"])
        self._nombre_obj.set(ej["nombre_obj"])
        self._unidad_obj.set(ej["unidad_obj"])
        for (nom, uni), coef in zip(ej["variables"], ej["coef_obj"]):
            self.agregar_variable(nom, uni, coef, redibujar=False)
        for nom, uni, coefs, signo, rhs in ej["restricciones"]:
            self.agregar_restriccion(nom, uni, coefs, signo, rhs,
                                     redibujar=False)
        self._dibujar()
        self._marco.ir_al_inicio()

    def limpiar(self) -> None:
        """Deja un formulario en blanco de 2 variables y 1 restricción."""
        self._reiniciar_estado()
        self._tipo.set("Maximizar")
        self._nombre_obj.set("Z")
        self._unidad_obj.set("")
        self.agregar_variable(redibujar=False)
        self.agregar_variable(redibujar=False)
        self.agregar_restriccion(redibujar=False)
        self._dibujar()

    def _reiniciar_estado(self) -> None:
        self._nombres_var.clear()
        self._unidades_var.clear()
        self._coef_obj.clear()
        self._filas.clear()

    # ------------------------------------------------------------------
    # Salida: del formulario al modelo
    # ------------------------------------------------------------------
    def construir_problema(self) -> Problema:
        """
        Lee el formulario y devuelve un `Problema`.
        Lanza ErrorModelo (de core.models) si algo es inválido: nombre
        vacío, número mal escrito, nombres repetidos, etc.
        """
        def num(texto: str) -> str:
            texto = texto.strip()
            return texto if texto else "0"

        variables = [Variable(nom.get(), uni.get())
                     for nom, uni in zip(self._nombres_var,
                                         self._unidades_var)]
        restricciones = [
            Restriccion(f["nombre"].get(), f["unidad"].get(),
                        [num(c.get()) for c in f["coefs"]],
                        f["signo"].get(), num(f["rhs"].get()))
            for f in self._filas
        ]
        return Problema(
            tipo="max" if self._tipo.get() == "Maximizar" else "min",
            variables=variables,
            coef_objetivo=[num(c.get()) for c in self._coef_obj],
            restricciones=restricciones,
            nombre_objetivo=self._nombre_obj.get().strip() or "Z",
            unidad_objetivo=self._unidad_obj.get().strip(),
        )
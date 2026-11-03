"""
ui/table_view.py
----------------
Visor de las tablas del simplex primal, iteración por iteración.

Dibuja cada `Iteracion` del historial como una cuadrícula y resalta:
  - la columna entrante (verde),
  - la fila saliente (naranja),
  - el elemento pivote (amarillo),
  - la columna de razones (RHS / elemento) con la razón mínima marcada.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from MetodoSimplex.Utils.formatters import formatear_numero

from MetodoSimplex.core.simplex import EstadoSimplex, Iteracion, ResultadoSimplex
from MetodoSimplex.core.standarizer import ProblemaEstandar

from .widgets import MarcoDesplazable, fuente_negrita

COLOR = {
    "encabezado": "#d9e2ef",
    "z": "#eef2f7",
    "normal": "#ffffff",
    "columna": "#d8f0d8",
    "fila": "#fde3c8",
    "pivote": "#ffd54a",
    "razon_min": "#fff2b3",
}


class VistaTablas(ttk.Frame):

    def __init__(self, master, decimales: int = 4):
        super().__init__(master, padding=10)
        self._decimales = decimales
        self._est: ProblemaEstandar | None = None
        self._res: ResultadoSimplex | None = None
        self._indice = 0

        self._crear_navegacion()
        self._crear_panel_estandar()

        self._info = tk.StringVar()
        self._lbl_info = ttk.Label(self, textvariable=self._info,
                                   wraplength=1000, justify="left")
        self._lbl_info.pack(anchor="w", pady=(0, 6))

        self._marco = MarcoDesplazable(self)
        self._marco.pack(fill="both", expand=True)
        self._crear_leyenda()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_navegacion(self) -> None:
        barra = ttk.Frame(self)
        barra.pack(fill="x", pady=(0, 6))

        self._btn_primera = ttk.Button(barra, text="⏮", width=3,
                                       command=lambda: self.ir_a(0))
        self._btn_ant = ttk.Button(barra, text="◀ Anterior",
                                   command=lambda: self.ir_a(self._indice - 1))
        self._combo = ttk.Combobox(barra, state="readonly", width=34)
        self._combo.bind("<<ComboboxSelected>>",
                         lambda _e: self.ir_a(self._combo.current()))
        self._btn_sig = ttk.Button(barra, text="Siguiente ▶",
                                   command=lambda: self.ir_a(self._indice + 1))
        self._btn_ultima = ttk.Button(barra, text="⏭", width=3,
                                      command=lambda: self.ir_a(self._total() - 1))

        for w in (self._btn_primera, self._btn_ant, self._combo,
                  self._btn_sig, self._btn_ultima):
            w.pack(side="left", padx=2)

        self._btn_estandar = ttk.Button(barra, text="Ver estandarización",
                                        command=self._alternar_estandar)
        self._btn_estandar.pack(side="right")

    def _crear_panel_estandar(self) -> None:
        self._panel_estandar = ttk.LabelFrame(
            self, text="Forma estándar del problema", padding=8)
        self._texto_estandar = tk.StringVar()
        ttk.Label(self._panel_estandar, textvariable=self._texto_estandar,
                  justify="left").pack(anchor="w")
        self._estandar_visible = False

    def _alternar_estandar(self) -> None:
        if self._estandar_visible:
            self._panel_estandar.pack_forget()
            self._btn_estandar.configure(text="Ver estandarización")
        else:
            self._panel_estandar.pack(fill="x", pady=(0, 6),
                                      before=self._lbl_info)
            self._btn_estandar.configure(text="Ocultar estandarización")
        self._estandar_visible = not self._estandar_visible

    def _crear_leyenda(self) -> None:
        leyenda = ttk.Frame(self)
        leyenda.pack(fill="x", pady=(6, 0))
        ttk.Label(leyenda, text="Leyenda:").pack(side="left", padx=(0, 6))
        for clave, texto in (("columna", "Columna entrante"),
                             ("fila", "Fila saliente"),
                             ("pivote", "Elemento pivote"),
                             ("razon_min", "Razón mínima")):
            tk.Label(leyenda, text=texto, bg=COLOR[clave], fg="black",
                     relief="solid", bd=1, padx=6).pack(side="left", padx=3)
        ttk.Label(leyenda, foreground="#666666",
                  text="   Fila Z = z_j − c_j (la tabla es óptima cuando "
                       "todos son ≥ 0)").pack(side="left", padx=8)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def mostrar(self, est: ProblemaEstandar, res: ResultadoSimplex) -> None:
        """Carga el resultado del simplex y muestra la Tabla 0."""
        self._est, self._res = est, res
        self._texto_estandar.set(est.resumen())
        self._combo["values"] = [self._rotulo(i)
                                 for i in range(len(res.historial))]
        self.ir_a(0)

    def limpiar(self) -> None:
        self._est = self._res = None
        self._combo["values"] = []
        self._combo.set("")
        self._info.set("")
        for w in self._marco.interior.winfo_children():
            w.destroy()

    def ir_a(self, indice: int) -> None:
        if self._res is None:
            return
        self._indice = max(0, min(indice, self._total() - 1))
        self._combo.current(self._indice)
        self._actualizar_botones()
        self._dibujar()

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _total(self) -> int:
        return len(self._res.historial) if self._res else 0

    def _rotulo(self, i: int) -> str:
        ultima = i == len(self._res.historial) - 1
        if i == 0 and ultima:
            return "Tabla 0 (inicial = final)"
        if i == 0:
            return "Tabla 0 (inicial)"
        if ultima:
            etiqueta = {EstadoSimplex.OPTIMA: "óptima",
                        EstadoSimplex.NO_ACOTADA: "no acotada",
                        }.get(self._res.estado, "última")
            return f"Tabla {i} ({etiqueta})"
        return f"Tabla {i}"

    def _actualizar_botones(self) -> None:
        primera = self._indice == 0
        ultima = self._indice == self._total() - 1
        for btn, desactivar in ((self._btn_primera, primera),
                                (self._btn_ant, primera),
                                (self._btn_sig, ultima),
                                (self._btn_ultima, ultima)):
            btn.state(["disabled"] if desactivar else ["!disabled"])

    def _texto_decision(self, it: Iteracion) -> str:
        f = lambda v: formatear_numero(v, self._decimales)
        if it.col_entrante is None:
            return ("Tabla óptima: todos los valores de la fila Z son ≥ 0, "
                    "ninguna variable puede mejorar Z.")
        z = it.tabla.fila_z[it.col_entrante]
        entra = f"Entra {it.variable_entrante} (z_j − c_j = {f(z)}, el más negativo)."
        if it.fila_saliente is None:
            return (f"{entra} Ninguna fila tiene razón válida: el problema "
                    f"no está acotado.")
        razon = it.razones[it.fila_saliente]
        return (f"{entra}  Sale {it.variable_saliente} "
                f"(razón mínima = {f(razon)}).  "
                f"Elemento pivote = {f(it.elemento_pivote)}.")

    def _dibujar(self) -> None:
        it = self._res.historial[self._indice]
        self._info.set(f"Tabla {it.numero}:  " + self._texto_decision(it))

        filas = it.tabla.como_filas_texto(self._decimales)
        m = it.tabla.n_filas
        hay_pivote_col = it.col_entrante is not None

        # Columna extra con las razones RHS / elemento
        if hay_pivote_col:
            filas[0].append("Razón")
            for i in range(m):
                r = it.razones[i]
                filas[1 + i].append(
                    "—" if r is None
                    else formatear_numero(r, self._decimales))
            filas[-1].append("")

        # Ancho uniforme por columna
        n_cols = len(filas[0])
        anchos = [max(len(fila[c]) for fila in filas) + 2
                  for c in range(n_cols)]
        col_razon = n_cols - 1 if hay_pivote_col else None
        col_pivote = it.col_entrante + 1 if hay_pivote_col else None
        fila_pivote = it.fila_saliente + 1 if it.fila_saliente is not None \
            else None

        negrita = fuente_negrita()
        normal = tkfont.nametofont("TkDefaultFont")

        g = self._marco.interior
        for w in g.winfo_children():
            w.destroy()

        for r, fila in enumerate(filas):
            es_encabezado = r == 0
            es_z = r == len(filas) - 1
            for c, texto in enumerate(fila):
                bg = COLOR["normal"]
                usar_negrita = False
                if es_encabezado:
                    bg, usar_negrita = COLOR["encabezado"], True
                elif es_z:
                    bg, usar_negrita = COLOR["z"], True
                elif c == 0:
                    usar_negrita = True

                if not es_encabezado and not es_z:
                    if c == col_pivote:
                        bg = COLOR["columna"]
                    if r == fila_pivote:
                        bg = COLOR["fila"]
                    if r == fila_pivote and c == col_pivote:
                        bg, usar_negrita = COLOR["pivote"], True
                    if c == col_razon and r == fila_pivote:
                        bg, usar_negrita = COLOR["razon_min"], True
                elif es_z and c == col_pivote:
                    bg = COLOR["columna"]

                tk.Label(g, text=texto, bg=bg, fg="black",
                         font=negrita if usar_negrita else normal,
                         width=anchos[c], anchor="w" if c == 0 else "e",
                         relief="solid", bd=1, padx=2, pady=3
                         ).grid(row=r, column=c, sticky="nsew")
"""
ui/app.py
---------
Ventana principal. Une el núcleo (core) con las tres vistas:

    Problema  ->  estandarizar -> resolver (simplex primal)
              ->  construir_solucion
    y reparte el resultado a la vista de tablas y a la de solución.
"""

from __future__ import annotations

import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from MetodoSimplex.core import simplex, simplex_dual
from MetodoSimplex.core.models import ErrorModelo
from MetodoSimplex.core.sensibility import analizar
from MetodoSimplex.core.solution import construir_solucion
from MetodoSimplex.core.standarizer import estandarizar

from .input import PanelEntrada
from .sensibility_view import VistaSensibilidad
from .solution_view import VistaSolucion
from .table_view import VistaTablas
from .widgets import configurar_estilos


class App(tk.Tk):

    TITULO = "Método Simplex — DM&E S.A.S."

    def __init__(self):
        super().__init__()
        self.title(self.TITULO)
        self.geometry("1200x720")
        self.minsize(900, 560)
        self.state("zoomed")
        configurar_estilos(self)

        ttk.Frame(self, style="Accent.TFrame", height=3).pack(fill="x")
        encabezado = ttk.Frame(
            self, style="Header.TFrame", padding=(28, 14, 28, 14))
        encabezado.pack(fill="x")
        ttk.Label(encabezado, text="SIMPLEX  /  DM&E S.A.S.",
                  style="Header.Kicker.TLabel").pack(anchor="w")
       
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=10, pady=(0, 16))

        self.entrada = PanelEntrada(self._notebook, on_resolver=self.resolver)
        self.tablas = VistaTablas(self._notebook)
        self.tablas_dual = VistaTablas(
            self._notebook, metodo="simplex dual")
        self.solucion = VistaSolucion(self._notebook)
        self.sensibilidad = VistaSensibilidad(self._notebook)

        self._notebook.add(self.entrada, text="Problema")
        self._notebook.add(self.tablas, text="Tablas del simplex")
        self._notebook.add(self.tablas_dual, text="Tablas duales")
        self._notebook.add(self.solucion, text="Solución")
        self._notebook.add(self.sensibilidad, text="Sensibilidad")
        self._habilitar_resultados(False)

        # Atajo: Ctrl+Enter resuelve desde cualquier pestaña
        self.bind("<Control-Return>", lambda _e: self.resolver())

    # ------------------------------------------------------------------
    def resolver(self) -> None:
        """Lee el formulario, ejecuta el simplex primal y muestra todo."""
        try:
            problema = self.entrada.construir_problema()
            est = estandarizar(problema)
            res = simplex.resolver(est)
            res_dual = simplex_dual.resolver(est, res)
            resultado_final = (
                res_dual if res_dual is not res and res_dual.n_iteraciones
                else res
            )
            sol = construir_solucion(est, resultado_final)
        except ErrorModelo as error:
            self._habilitar_resultados(False)
            messagebox.showerror("Problema no válido", str(error), parent=self)
            return
        except Exception as error:
            traceback.print_exc()
            self._habilitar_resultados(False)
            messagebox.showerror(
                "Error inesperado",
                f"{type(error).__name__}: {error}", parent=self)
            return

        # La sensibilidad se calcula aparte: si falla (p. ej. una restricción
        # pendiente violada que requiere el dual), la solución se muestra igual.
        sens, motivo = self._calcular_sensibilidad(est, res)

        self.tablas.mostrar(est, res)
        self.tablas_dual.mostrar(est, res_dual)
        metodo = ("simplex dual" if resultado_final is res_dual
              else "simplex primal")
        self.solucion.mostrar(sol, metodo=metodo)
        self.sensibilidad.mostrar(sens, motivo)
        self._habilitar_resultados(True)
        if res_dual is not res and res_dual.n_iteraciones:
            self._notebook.select(self.tablas_dual)
        else:
            self._notebook.select(self.solucion)

    def _calcular_sensibilidad(self, est, res):
        """Devuelve (resultado, motivo). Si no se puede calcular: (None, motivo)."""
        if res.estado is not simplex.EstadoSimplex.OPTIMA:
            return None, "No hay una solución óptima sobre la cual calcularlo."
        try:
            return analizar(est, res), ""
        except ErrorModelo as error:
            return None, str(error)
        except Exception as error:
            traceback.print_exc()
            return None, f"{type(error).__name__}: {error}"

    def _habilitar_resultados(self, activo: bool) -> None:
        estado = "normal" if activo else "disabled"
        self._notebook.tab(self.tablas, state=estado)
        self._notebook.tab(self.tablas_dual, state=estado)
        self._notebook.tab(self.solucion, state=estado)
        self._notebook.tab(self.sensibilidad, state=estado)
        if not activo:
            self.tablas.limpiar()
            self.tablas_dual.limpiar()
            self.solucion.limpiar()
            self.sensibilidad.limpiar()
            self._notebook.select(self.entrada)
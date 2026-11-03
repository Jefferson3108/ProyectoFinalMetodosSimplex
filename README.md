# Método Simplex primal y dual

Aplicación de escritorio para formular y resolver problemas de programación lineal. El proyecto se desarrolló en el contexto del análisis de rentabilidad de DM&E S.A.S., con un ejemplo precargado de ocho productos.

## Funcionalidades

- Define una función objetivo de maximización o minimización, variables de decisión y restricciones.
- Resuelve el modelo con simplex primal y, cuando se requiere, continúa con simplex dual.
- Muestra las tablas de cada iteración, la solución, el uso de recursos y la verificación de restricciones.
- Calcula precios sombra y rangos de sensibilidad cuando el análisis está disponible.
- Identifica resultados óptimos, problemas no acotados e incompatibilidad de restricciones.
- Usa aritmética racional exacta mediante `fractions.Fraction` para evitar errores de redondeo durante los pivotes.

## Requisitos

- Python 3.10 o posterior.
- Tkinter, incluido en la instalación oficial de Python para Windows (asegúrate de incluir Tcl/Tk durante la instalación).
- No se requieren paquetes externos.

## Instrucciones de instalación

1. Instala Python 3.10 o posterior desde [python.org](https://www.python.org/downloads/). En Windows, habilita la opción **Tcl/Tk and IDLE** en el instalador.
2. Clona o descarga este repositorio y extrae sus archivos.
3. Abre PowerShell en la carpeta del proyecto, donde se encuentra `main.py`.
4. Comprueba que Python esté disponible:

```powershell
python --version
```

No es necesario ejecutar `pip install`: el proyecto no utiliza dependencias externas.

## Instrucciones de ejecución

Desde la carpeta del proyecto, inicia la interfaz con:

```powershell
python main.py
```

En Windows también puedes usar el lanzador `py` si `python` no está disponible:

```powershell
py main.py
```

La ventana se abre maximizada. Para resolver un modelo, completa los campos de la pestaña **Problema** y pulsa **Resolver con simplex primal**. También puedes iniciar el cálculo desde cualquier pestaña con `Ctrl+Enter`.

## Ejecución de pruebas unitarias o ejercicios precargados

El proyecto no incluye actualmente una suite de pruebas unitarias automatizadas. Para probar los métodos desde la interfaz:

1. Ejecuta la aplicación con `python main.py`.
2. En **Problema**, pulsa **Cargar ejemplo** y selecciona uno de los ejercicios.
3. Pulsa **Resolver con simplex primal**. Revisa las iteraciones en **Tablas del simplex** y, si el ejercicio necesita pivotes duales, en **Tablas duales**. La pestaña **Solución** presenta el resultado final.

Ejercicios precargados:

- **Caso DM&E (8 productos):** modelo de rentabilidad con límites de demanda, presupuesto, despacho, capacidad de pasta y mínimo de productos complementarios.
- **Ejemplo simple (mesas y sillas):** debe obtener utilidad `1800`, con 20 mesas y 60 sillas.
- **Ejemplo con restricción ≥ (requiere dual):** debe obtener utilidad `1750`, con 25 mesas y 50 sillas; la solución final se obtiene con simplex dual.

Los campos numéricos aceptan enteros, decimales con punto o coma y fracciones como `3/2`. Una celda vacía se interpreta como cero.

## Alcance del método

El simplex primal procesa directamente las restricciones `<=` con lado derecho no negativo. Las demás restricciones se incorporan en una etapa dual que parte del óptimo del problema procesado por el primal. Si ese problema inicial no alcanza un óptimo, la etapa dual no puede continuar. Cuando una restricción pendiente hace incompatible el modelo, el resultado se informa como infactible.

El análisis de sensibilidad se calcula a partir de la tabla óptima y puede no estar disponible cuando se necesita continuar con el simplex dual.

## Estructura

```text
main.py                         Inicio de la aplicación
MetodoSimplex/
	core/                         Modelo, estandarización, tablas y solvers
	userInterface/                Formulario, tablas y vistas de resultados
	Utils/                        Formateo de valores para mostrar
```

No se incluye actualmente una suite de pruebas automatizadas; los ejemplos precargados permiten probar los flujos principales desde la interfaz.






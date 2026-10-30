# Proyecto Metodo simplex primjal y dual
## 1. Descripción del proyecto ##
Este proyecto consiste en desarrollar un programa que resuelve problemas de programación lineal (PL) mediante los métodos simplex primal y simplex dual. A partir del modelo matemático del problema, con su función objetivo y sus restricciones, el programa genera una tabla por cada iteración del método hasta alcanzar la solución óptima. Luego presenta al usuario el valor óptimo de la función objetivo y el de cada variable de decisión, y verifica que todas las restricciones se cumplan. Además, el software identifica los casos especiales que pueden presentarse en el modelo, como los problemas infactibles, los no acotados y aquellos con soluciones alternativas.

## 2. Objetivo del proyecto ##
### Objetivo general ###
Resolver, mediante un modelo de programación lineal, el problema de rentabilidad identificado en la empresa DM&E S.A.S., determinando qué cantidad de cada uno de los 8 productos estudiados debe comercializar para maximizar su ganancia total, teniendo en cuenta las restricciones operativas y financieras de la empresa y los supuestos definidos para el modelo.

### Objetivos específicos ###
- Formular el modelo matemático del problema, definiendo las variables de decisión, la función objetivo y las restricciones (límites de demanda, presupuesto de compra, capacidad de despacho, capacidad conjunta de pasta y comercialización mínima de productos complementarios).
- Desarrollar un programa en Python que resuelva el modelo con el método simplex y muestre cada tabla del proceso hasta llegar a la solución óptima.
- Verificar que la solución obtenida cumpla todas las restricciones y comprobar su validez con un software independiente.
- Realizar el análisis de sensibilidad de la solución (precios sombra y rangos de los coeficientes de la función objetivo y de los lados derechos), para identificar qué recursos limitan la ganancia y qué decisiones conviene tomar.
## 3. Tecnologias utilizadas ##
El proyecto se desarrolló en el lenguaje de programación Python, elegido por su claridad, su amplia biblioteca estándar y su facilidad para expresar algoritmos matemáticos. El método simplex se implementó usando únicamente módulos de la biblioteca estándar: fractions para trabajar con aritmética exacta (de modo que las tablas del simplex no acumulen errores de redondeo), dataclasses y enum para modelar el problema (variables, restricciones y tipos de optimización) y typing para documentar los tipos de datos. La interfaz gráfica se construyó con Tkinter y su submódulo ttk, que permiten ingresar el problema, visualizar cada tabla del simplex y presentar la solución final
## 4. Estructura del proyecto ##
## 5. Instrucciones de instalación ##
## 6. Instrucciones de ejecución ##
## 7. Ejecución de prubas unitarias o ejercicios precargados ##
## 8. Evidencias de ejecución del proyecto ##
![Texto alternativo](Sources/Captura%20de%20pantalla%202026-10-29%20210325.png)
![Texto alternativo](Sources/Captura%20de%20pantalla%202026-10-29%20210403.png)
![Texto alternativo](Sources/Captura%20de%20pantalla%202026-10-29%20211415.png)
![Texto alternativo](Sources/Captura%20de%20pantalla%202026-10-29%20211430.png)






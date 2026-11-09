# Vectorización y dibujo de glifos en SVG

Cómo llegar de un dibujo (escaneo, trazo en Affinity o construcción por script) a contornos limpios en el maestro `.sfd`, y cómo revisarlos. Reúne prácticas de diseño tipográfico y métodos de otras disciplinas (diseño industrial, gráficos por computadora, procesamiento de imágenes) que encajan con la automatización del pipeline.

## 1. Reglas de un buen contorno

| Regla | Por qué | Cómo se revisa |
| --- | --- | --- |
| Nodos en los extremos horizontales y verticales | Los rasterizadores y el hinting cuentan con ellos; FontForge y Font Bakery los piden | `12_curvas.py`: *extremo sin nodo* |
| Asas de esos nodos horizontales o verticales | La tangente en un extremo es H o V por definición | *asa casi H/V* (entre 1° y 10°: casi seguro un accidente) |
| Pocos nodos; uno por inflexión | Cada segmento se subdivide igual al rasterizar: segmentos muy desiguales se ven irregulares | número de nodos en `proofs/curvas.md` |
| Un nodo es liso o es esquina, nunca «casi» | Un quiebre de 1°–12° se ve como un bache en tamaños grandes | *quiebre* |
| Curvatura continua (G2) en los nodos lisos | La curva se lee como un solo trazo de herramienta; sin G2 aparece una «rodilla» | *salto de curvatura (G2)* y peines |
| Asas entre ≈ 58 % y 76 % del máximo (≈ 55 % es un círculo) | Rango habitual en tipografía; más tensión en curvas exteriores de pesos gruesos | a ojo, con los peines |

Fuentes: Scannerlicker, *Bézier OCD*; Glyphs, *Harmonization*; Design With FontForge.

## 2. Peines de curvatura (diseño industrial → tipografía)

En el modelado de superficies «clase A» (carrocerías, electrodomésticos) la calidad de una curva se revisa con **peines de curvatura**: dientes perpendiculares a la curva, de largo proporcional a la curvatura. Un peine continuo y suave indica G2; un salto entre dientes vecinos es un cambio brusco que el ojo percibe como reflejo quebrado (Autodesk Alias, Rhino *CurvatureGraph*). En tipografía pasa lo mismo con el contraste de una panza o una gota.

`mise run curvas` → `proofs/curvatura/<familia>.svg` (mismas familias que las hojas de Affinity) y `proofs/curvas.md`. Los círculos rojos marcan extremos sin nodo, quiebres y saltos G2. Se generan en cada build de GitHub Actions (paquete de resultados).

## 3. Armonización G2

Mover solo el nodo liso sobre la recta de sus asas hasta el punto donde la curvatura de los dos segmentos coincide (algoritmo de Simon Cozens, usado por Green Harmony):

```
d  = intersección de las rectas (a1, a2) y (b1, b2)      # asas de los dos segmentos
p0 = |a1 a2| / |a2 d|,  p1 = |d b1| / |b1 b2|
t  = √(p0·p1) / (1 + √(p0·p1))
nodo nuevo = a2 + t · (b1 − a2)
```

`curvas.armonizar()` lo aplica solo si el movimiento es pequeño (≤ 20 % de la distancia entre asas); si no, el problema es de dibujo y se deja para corregir a mano.

**Cuándo se aplica.** La armonización cambia un poco la forma, así que el pipeline la aplica solo donde el dibujo no es de la diseñadora: glifos construidos por script (`LIMPIAR_CURVAS = "bocetos"` en `proyecto.py`) o los que se nombren explícitamente. Los glifos dibujados a mano solo se diagnostican.

**Validación (Sterna, iteración 3).** Sobre los bocetos de cifras y signos:

| Opción | Extremos sin nodo | Saltos G2 | Asas casi H/V | Desviación máx. del contorno |
| --- | --- | --- | --- | --- |
| Sin limpiar | 28 | 28 | 92 | — |
| A. Solo puntos en extremos | 0 | 28 | 92 | 0 (no cambia la forma) |
| B. A + armonización G2 | 0 | 9 | 91 | ≈ 4,5 u |
| C. A + asas H/V + G2 (elegida) | 0 | 10 | 78 | ≈ 5 u |

La desviación incluye ≈ 3,5 u de error de muestreo de la medición. C es la opción por defecto de `curvas.limpiar()`.

## 4. Del escaneo al vector (procesamiento de imágenes)

- **Umbral de Otsu** (Otsu, 1979) con desenfoque gaussiano previo para separar tinta y papel sin fijar un valor a mano (`01_digitalizar.py`).
- **Potrace** (Selinger) traza el mapa de bits con curvas Bézier óptimas. Parámetros en `proyecto.py` › `POTRACE`:

| Parámetro | Por defecto | Efecto | Cuándo cambiarlo |
| --- | --- | --- | --- |
| `alphamax` | 1.0 | umbral de esquina: menor = esquinas más vivas; 0 = polígono | remates rectos y cortes limpios: 0.6–0.8; caligrafía suave: 1.1–1.2 |
| `opttolerance` | 0.2 | cuánto puede desviarse para unir segmentos: mayor = menos nodos | 0.3–0.4 si salen demasiados nodos; 0.1 si se pierden detalles |
| `turdsize` | 10 | manchas menores a n píxeles se descartan | subir con escaneos sucios |

- **Ajuste de curvas por mínimos cuadrados** (Schneider, *An Algorithm for Automatically Fitting Digitized Curves*, Graphics Gems, 1990): el método clásico de gráficos por computadora para pasar de puntos a Bézier; Potrace resuelve lo mismo con otro enfoque. Si un glifo sale con demasiados nodos, la regla de oro es redibujarlo con pocos nodos sobre el trazo automático, no simplificar a ciegas.
- Después de Potrace, `02_importar.py` y `07_a_sfd.py` aplican en FontForge **Remove Overlap**, **Add Extrema**, **Round to Int** y **Correct Direction**.

## 5. SVG desde Affinity

Las hojas (`hojas/*.svg`) y los trazos manuales (`glyphs-svg/*.svg`) se leen con `fontTools.svgLib`. Para que entren bien:

1. **Formas rellenas, no líneas.** Si dibujaste con trazo (stroke), selecciónalo y usa **Layer › Expand Stroke** antes de exportar. El importador ignora los trazos sin relleno (son las guías) y avisa si encuentra uno oscuro.
2. **Contornos cerrados**; los huecos (contraformas) como subtrazos del mismo objeto o con **Layer › Geometry › Subtract**.
3. **No muevas las marcas de registro** ni cambies el tamaño de la mesa de trabajo.
4. **File › Export › SVG**: preset **SVG (for export)**, **Rasterise: Nothing**, **Flatten transforms** activado. Rectángulos, elipses y polígonos se aceptan tal cual.
5. Guarda encima del mismo archivo o con sufijo (`10-cifras-iteracion-2.svg`).

Este preparado sigue la idea de **picosvg** (Google Fonts): un SVG «mínimo» con solo trazados absolutos y transformaciones aplicadas es el que mejor pasa a una fuente.

## Bibliografía y fuentes

- Scannerlicker — *Bézier OCD, or why you should know about point placement* (2014): https://scannerlicker.net/writings/2014/10/01/bezier-ocd-or-why-you-should-know-about-point-placement/
- Glyphs — *Harmonization*: https://glyphsapp.com/learn/harmonization
- Design With FontForge — *Importing glyphs from other programs*: https://designwithfontforge.com
- Potrace, manual: https://potrace.sourceforge.net · https://www.mankier.com/1/potrace
- picosvg (Google Fonts): https://pypi.org/project/picosvg
- Green Harmony (A. Slobzheninov, Apache 2.0) y discusión de algoritmos libres: https://forum.glyphsapp.com/t/free-alternative-to-rmx-harmonizer/4998
- Autodesk Alias — *Curvature continuity in surface modeling*: https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/GUID-9DD73E22-A5EF-4952-BB84-2CEE2109993C.htm
- McNeel Rhino — G0/G2/G3 y peines de curvatura: https://discourse.mcneel.com/t/understanding-g0-g2-g3-in-relation-to-curvature-combs-continuity/146065
- P. J. Schneider, «An Algorithm for Automatically Fitting Digitized Curves», *Graphics Gems*, 1990 (implementación: https://github.com/volkerp/fitCurves)
- N. Otsu, «A Threshold Selection Method from Gray-Level Histograms», *IEEE Trans. SMC*, 1979
- Lucide — guía de exportación SVG en Affinity Designer: https://lucide.dev/contribute/icons/affinity-designer-guide

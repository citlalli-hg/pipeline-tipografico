# Pipeline tipográfico

Método y herramientas compartidas para diseñar las fuentes de la marca Citlallihg: de glifos dibujados a mano (o vectores existentes) a OTF, TTF y WOFF2, con FontForge, Affinity y herramientas open source.

Cada fuente vive en su propio repositorio y usa este pipeline como submódulo en `pipeline/`:

| Fuente | Repositorio | Punto de partida |
| --- | --- | --- |
| Elocaso | `citlalli-hg/elocaso` | Elalba Regular (display → interfaz) |
| Sterna | `citlalli-hg/sterna` | Sterna 2018 (serif display, A–Z a–z) |

Cómo se comparten el pipeline y sus actualizaciones: [docs/proyectos.md](docs/proyectos.md).

## Etapas

| Etapa | Qué pasa | Herramienta | `mise run …` |
| --- | --- | --- | --- |
| 0 Definir | Brief, modelo de trazo, set, métricas | `brief/`, `proyecto.py` | — |
| 1 Dibujar | Plantilla impresa y dibujo a mano | Affinity / navegador | `plantilla` |
| 2 Digitalizar | Endereza escaneos y recorta un PNG por glifo | Python + OpenCV | `digitalizar` |
| 3 Vectorizar | Traza cada glifo y lo importa al maestro | Potrace + FontForge | `importar` |
| — Completar | Base desde vectores existentes + construcciones propias | fontTools | `completar` |
| 4 Limpiar | Nodos, extremos, dirección; correcciones ópticas a mano | FontForge (+ Affinity) | `limpiar` |
| — Curvas | Peines de curvatura y reporte: extremos, quiebres, G2 | fontTools | `curvas` |
| 5 Ensamblar | Maestro `sources/<slug>.sfd` en Git | FontForge | `maestro` |
| 6 Expandir | Acentos como componentes | FontForge | `limpiar` |
| 7 Espaciar y kernear | Espaciado por lados, kerning por perfiles, revisión manual | fontTools, FontForge | `estabilizar` |
| — Corregir | Hojas de familia en Affinity, de ida y vuelta | Affinity | `hojas`, `importar-hojas` |
| 8 OpenType | `sources/features.fea` | FontForge | — |
| 9 Build y QA | OTF, TTF, WOFF2, Font Bakery y PDF de pruebas | FontForge, fontTools, drawbot-skia | `build`, `qa`, `pruebas` |

Metodología y bibliografía: [docs/pipeline.md](docs/pipeline.md). Vectorización y calidad de curvas: [docs/vectorizacion.md](docs/vectorizacion.md). Hojas de Affinity: [docs/hojas.md](docs/hojas.md).

## Estructura

```
scripts/             etapas 00–11, config.py (valores por defecto), contornos.py, ff.py, doctor.py, qa.py,
                     nuevo_proyecto.py, setup-windows.ps1
tareas.toml          tareas de Mise que incluye cada proyecto
.github/actions/     acciones de CI: preparar, build, estabilizar, hojas
plantilla-proyecto/  archivos de partida de una fuente nueva
docs/                método, hojas de Affinity, proyectos compartidos
```

## Reglas

- Ningún script tiene nombres de fuente: todo lo propio sale de `proyecto.py` vía `scripts/config.py`.
- Todo debe funcionar en Windows, macOS y Linux, sin `make` ni comandos solo de Unix.
- Cambios por rama y pull request; anota cada cambio en `CHANGELOG.md`.
- Antes de fusionar un cambio que afecte la salida, pruébalo en al menos una fuente (ver docs/proyectos.md › Probar un cambio).

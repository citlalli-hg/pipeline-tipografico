# Pipeline de diseño tipográfico

Resumen del proceso. La versión completa, con metodología y bibliografía, está en el documento *Pipeline de diseño tipográfico con IA y automatización* (Claude Docs): https://claude.ai/artifact/4apzWuLwyS6EBXpsySwKbi

## Etapas

0. **Definir** — brief, referentes, modelo de trazo (traslación, expansión, rotación), set de caracteres y métricas. → `brief/brief.md`. Qué dibujar para que el pipeline genere la fuente completa: [set-semilla.md](set-semilla.md).
1. **Dibujar** — glifos de control (n, o, H, O), luego palabras de prueba (*adhesion*, *hamburgefonstiv*, *ñandú*) y repertorio de partes.
2. **Digitalizar** — escaneo a 600 dpi, enderezado por marcas de registro, recorte por celda. → `pipeline/scripts/01_digitalizar.py`
3. **Vectorizar** — Potrace por script (parámetros en `proyecto.py` › `POTRACE`); Image Trace de Affinity para glifos difíciles. Reglas de contorno, exportación SVG desde Affinity y bibliografía: [vectorizacion.md](vectorizacion.md). → `pipeline/scripts/02_importar.py`
4. **Limpiar** — limpieza técnica automática y correcciones ópticas a mano: overshoot, horizontales más delgadas, centro óptico, peso de redondos, uniones. → `pipeline/scripts/03_limpiar.py`. Revisión de curvas con peines de curvatura (extremos, quiebres, continuidad G2): `mise run curvas` → `proofs/curvatura/`. En glifos construidos por script, `LIMPIAR_CURVAS` agrega extremos, endereza asas y armoniza.
5. **Ensamblar** — maestro `.sfd` en FontForge, versionado en Git.
6. **Expandir** — acentos como componentes (**Element › Build › Build Accented Glyph**), derivación n→m h u r, o→b d p q, l→i j t.
7. **Espaciar y kernear** — método de Tracy (*HHOHHOOHOO*, *nnonnoonoo*), **Metrics › Auto Width**, **Metrics › Kern By Classes**, pares críticos a mano.
7b. **Revisar a mano (hojas de Affinity)** — ciclo de corrección sobre el maestro, por familias de glifos (→ [hojas.md](hojas.md)):
   1. `mise run hojas` (o el workflow **Estabilizar**, que ya las deja en la rama) → `hojas/NN-familia.svg` desde la fuente compilada.
   2. Rama `importar/<familia>`; abrir la hoja en Affinity (**File › Open**), corregir dentro de cada celda sin mover las marcas de registro.
   3. **File › Export › SVG**, encima del mismo archivo (o con sufijo: `01-redondas-iteracion-2.svg`).
   4. Push: el workflow **Importar hojas al maestro** pasa los cambios al `.sfd`, compila, genera las pruebas y vuelve a exportar las hojas. En local: `mise run importar-hojas`.
   5. Revisar `proofs/pruebas.pdf`, anotar en `brief/bitacora.md` y repetir.
   Desde la primera corrección a mano, el maestro es la fuente de verdad: **Estabilizar** se detiene para no reemplazarlo (salvo con «forzar»).
8. **OpenType** — `sources/features.fea`: `case`, `liga`, `calt`.
9. **Build y QA** — OTF, TTF, WOFF2, Font Bakery y pruebas impresas de cabeza, en espejo y desenfocadas. → `pipeline/scripts/04_build.py`, `pipeline/scripts/05_pruebas.py`

## Bibliografía principal

- Henestrosa, Meseguer y Scaglione — *Cómo crear tipografías: del boceto a la pantalla*
- Karen Cheng — *Designing Type*
- Gerrit Noordzij — *The Stroke: Theory of Writing*
- Fred Smeijers — *Counterpunch*
- Walter Tracy — *Letters of Credit*
- Gerard Unger — *Theory of Type Design*
- Chris Campe y Ulrike Rausch — *Designing Fonts*
- *Design With FontForge* (designwithfontforge.com)

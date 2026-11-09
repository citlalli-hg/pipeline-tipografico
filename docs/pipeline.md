# Pipeline de diseño tipográfico

Resumen del proceso. La versión completa, con metodología y bibliografía, está en el documento *Pipeline de diseño tipográfico con IA y automatización* (Claude Docs): https://claude.ai/artifact/4apzWuLwyS6EBXpsySwKbi

## Etapas

0. **Definir** — brief, referentes, modelo de trazo (traslación, expansión, rotación), set de caracteres y métricas. → `brief/brief.md`
1. **Dibujar** — glifos de control (n, o, H, O), luego palabras de prueba (*adhesion*, *hamburgefonstiv*, *ñandú*) y repertorio de partes.
2. **Digitalizar** — escaneo a 600 dpi, enderezado por marcas de registro, recorte por celda. → `pipeline/scripts/01_digitalizar.py`
3. **Vectorizar** — Potrace por script; Image Trace de Affinity para glifos difíciles. → `pipeline/scripts/02_importar.py`
4. **Limpiar** — limpieza técnica automática y correcciones ópticas a mano: overshoot, horizontales más delgadas, centro óptico, peso de redondos, uniones. → `pipeline/scripts/03_limpiar.py`
5. **Ensamblar** — maestro `.sfd` en FontForge, versionado en Git.
6. **Expandir** — acentos como componentes (**Element › Build › Build Accented Glyph**), derivación n→m h u r, o→b d p q, l→i j t.
7. **Espaciar y kernear** — método de Tracy (*HHOHHOOHOO*, *nnonnoonoo*), **Metrics › Auto Width**, **Metrics › Kern By Classes**, pares críticos a mano.
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

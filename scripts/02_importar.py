"""Etapas 3 y 5 — Vectoriza cada glifo con Potrace y lo importa a FontForge.

Uso (con el Python de FontForge):
    python pipeline/scripts/02_importar.py              # solo glifos vacíos o nuevos
    python pipeline/scripts/02_importar.py a b A_       # solo estos glifos (reemplaza)
    python pipeline/scripts/02_importar.py --todos      # reemplaza todos (¡borra retoques!)

Para cada glifo usa, en este orden:
  1. glyphs-svg/<nombre>.svg  — trazo manual o Image Trace de Affinity
     (exporta la caja eme completa, al tamaño de la celda recortada)
  2. glyphs-png/<nombre>.pbm  — trazado automático con Potrace

Requisitos: FontForge con su módulo de Python, Potrace y fontTools.
En macOS/Windows ejecútalo con el Python que trae FontForge, por ejemplo:
    fontforge -lang=py -script scripts/02_importar.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import fontforge

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from svg_utils import draw_svg  # noqa: E402

PNG_DIR = C.ROOT / "glyphs-png"
SVG_DIR = C.ROOT / "glyphs-svg"


def new_font():
    f = fontforge.font()
    f.familyname = C.FAMILY
    f.fontname = f"{C.FAMILY}-{C.STYLE}"
    f.fullname = f"{C.FAMILY} {C.STYLE}"
    f.weight = C.STYLE
    f.version = C.VERSION
    f.copyright = f"Copyright {C.DESIGNER}"
    f.em = C.UPM
    f.ascent, f.descent = C.ASCENT, C.DESCENT
    f.encoding = "UnicodeFull"
    space = f.createChar(32, "space")
    space.width = 250
    return f


def potrace(pbm):
    out = Path(tempfile.mkdtemp()) / (pbm.stem + ".svg")
    # -s SVG, -a 1.0 suavizado de esquinas, -O 0.2 tolerancia de optimización de curvas,
    # -t 10 descarta manchas menores a 10 px
    p = C.POTRACE
    subprocess.run(["potrace", str(pbm), "-s", "-a", str(p["alphamax"]), "-O", str(p["opttolerance"]),
                    "-t", str(p["turdsize"]),
                    "-o", str(out)], check=True)
    return out


def svg_to_glyph(glyph, svg_path, cell_height_px):
    """Dibuja el SVG en el glifo: la altura de la celda = UPM y la línea base
    queda a DESCENT unidades del borde inferior."""
    s = C.UPM / cell_height_px
    ff_pen = glyph.glyphPen()
    draw_svg(svg_path, ff_pen, (s, 0, 0, -s, 0, cell_height_px * s - C.DESCENT))
    # FontForge escribe el contorno en el glifo cuando se libera la pluma
    ff_pen = None


def import_glyph(font, name):
    stem = C.file_stem(name)
    manual = SVG_DIR / f"{stem}.svg"
    pbm = PNG_DIR / f"{stem}.pbm"
    if manual.exists():
        svg, source = manual, "SVG manual"
    elif pbm.exists():
        svg, source = potrace(pbm), "Potrace"
    else:
        return None
    # La altura de referencia es la de la celda en píxeles a 600 dpi
    # (los SVG de Affinity deben exportarse a ese mismo tamaño).
    cell_h = round(C.EM_MM * C.PX_PER_MM)
    uni = fontforge.unicodeFromName(name)
    g = font.createChar(uni if uni >= 0 else -1, name)
    g.clear()
    svg_to_glyph(g, svg, cell_h)
    g.correctDirection()
    g.left_side_bearing = C.SIDEBEARING
    g.right_side_bearing = C.SIDEBEARING
    return source


def main():
    args = sys.argv[1:]
    force_all = "--todos" in args
    wanted = [a.rstrip("_") if a.endswith("_") and a[:-1].isupper() else a
              for a in args if not a.startswith("--")]
    font = fontforge.open(str(C.SFD)) if C.SFD.exists() else new_font()
    names = wanted or C.DRAWN
    done, skipped, missing = [], [], []
    for name in names:
        has_outline = name in font and len(font[name].foreground) > 0
        if has_outline and not (force_all or wanted):
            skipped.append(name)
            continue
        source = import_glyph(font, name)
        (done if source else missing).append(name)
    C.SFD.parent.mkdir(exist_ok=True)
    font.save(str(C.SFD))
    print(f"importados: {len(done)}  ·  conservados (ya tenían contorno): {len(skipped)}")
    if missing:
        print("sin archivo de origen:", " ".join(missing))
    print(f"guardado en {C.rel(C.SFD)}")


if __name__ == "__main__":
    main()

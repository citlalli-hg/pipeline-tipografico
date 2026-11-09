"""Etapa 1 — Genera la plantilla de dibujo en SVG (una página por hoja).

Uso:  python pipeline/scripts/00_plantilla.py
Salida: template/plantilla-01.svg, plantilla-02.svg, ...

Abre los SVG en Affinity (o en el navegador) e imprímelos al 100 %,
sin "ajustar a página". Las guías van en cian claro y las etiquetas en
gris para que desaparezcan al digitalizar; solo la tinta negra cuenta.
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

GUIDE = "#9ED8F0"
LABEL = "#B0B0B0"


def guide_y(box_y, units):
    """y en mm (desde arriba) de una línea a `units` sobre la línea base."""
    baseline = box_y + (C.ASCENT * C.MM_PER_UNIT)
    return baseline - units * C.MM_PER_UNIT


def page_svg(names, page_no, pages):
    w, h = C.PAGE_W_MM, C.PAGE_H_MM
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" '
        f'viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="white"/>',
    ]
    m, s = C.MARGIN_MM, C.MARKER_MM
    for x, y in [(m, m), (w - m - s, m), (m, h - m - s), (w - m - s, h - m - s)]:
        out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{s}" height="{s}" fill="black"/>')
    out.append(
        f'<text x="{w / 2:.1f}" y="{m + s / 2 + 1.5:.1f}" font-family="sans-serif" '
        f'font-size="3.5" text-anchor="middle" fill="{LABEL}">'
        f'{C.FAMILY} · hoja {page_no} de {pages} · imprimir al 100 %</text>'
    )
    for slot, name in enumerate(names):
        x, y, bw, bh = C.cell_box_mm(slot)
        out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bw:.2f}" height="{bh:.2f}" '
                   f'fill="none" stroke="{GUIDE}" stroke-width="0.2"/>')
        for units, width in [(0, 0.35), (C.X_HEIGHT, 0.2), (C.CAP_HEIGHT, 0.2),
                             (C.ASCENDER, 0.15), (C.DESCENDER, 0.15)]:
            gy = guide_y(y, units)
            out.append(f'<line x1="{x:.2f}" y1="{gy:.2f}" x2="{x + bw:.2f}" y2="{gy:.2f}" '
                       f'stroke="{GUIDE}" stroke-width="{width}"/>')
        out.append(
            f'<text x="{x:.2f}" y="{y - 1.2:.2f}" font-family="sans-serif" font-size="3.2" '
            f'fill="{LABEL}">{escape(C.label(name))}  ·  {name}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


def main():
    per = C.per_page()
    chunks = [C.DRAWN[i:i + per] for i in range(0, len(C.DRAWN), per)]
    outdir = C.ROOT / "template"
    outdir.mkdir(exist_ok=True)
    for i, chunk in enumerate(chunks, 1):
        path = outdir / f"plantilla-{i:02d}.svg"
        path.write_text(page_svg(chunk, i, len(chunks)), encoding="utf-8")
        print(f"{C.rel(path)}: {len(chunk)} glifos")
    cols, rows = C.grid_shape()
    print(f"{len(C.DRAWN)} glifos en {len(chunks)} hojas ({cols}×{rows} por hoja)")


if __name__ == "__main__":
    main()

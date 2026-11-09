"""Hojas de familia para corregir glifos a mano en Affinity.

Exportar (solo fontTools):
    python pipeline/scripts/11_hojas.py exportar [FUENTE.otf]
        FUENTE: por defecto fonts/<Familia>-Regular.otf (mise run build) o,
        si no existe, sources/<slug>-estable.otf
        → hojas/<familia>.svg, una por familia de glifos

Importar (con el Python de FontForge):
    python pipeline/scripts/ff.py 11_hojas.py importar [--sin-acentos] [hojas/arcos.svg ...]
        → actualiza sources/<slug>.sfd solo con los glifos que cambiaron
          y regenera sus acentuadas (á à â ä ã å…) con el cuerpo nuevo

Cómo se reconoce cada glifo al volver de Affinity:
  - Dos marcas de registro (cuadros negros en las esquinas) calibran la escala
    y la posición, aunque Affinity cambie las unidades o mueva la mesa de trabajo.
  - Cada contorno se asigna a la celda que contiene su centro. No depende de
    los nombres de capa (aunque los ids de cada grupo coinciden con el glifo).
  - Se ignoran las guías (solo trazo, sin relleno), los textos y las celdas
    de referencia (en gris).
"""
import importlib
import json
import math
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from pathlib import Path

from fontTools.misc.transform import Identity, Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path.parser import parse_path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from svg_utils import parse_transform  # noqa: E402

HOJAS = C.ROOT / "hojas"
SVG_NS = "http://www.w3.org/2000/svg"

# Familias según la estructura compartida de los glifos (Cheng, Designing Type).
# La primera lista son los glifos editables; "ref" son glifos de control en gris.
FAMILIAS = {
    "01-redondas": {"glifos": ["o", "c", "e", "s"], "ref": ["n"]},
    "02-arcos": {"glifos": ["n", "m", "h", "u", "r"], "ref": ["o"]},
    "03-panzas": {"glifos": ["a", "b", "d", "p", "q", "g"], "ref": ["n", "o"]},
    "04-astas": {"glifos": ["i", "j", "l", "f", "t", "dotlessi"], "ref": ["n"]},
    "05-diagonales": {"glifos": ["v", "w", "x", "y", "k", "z"], "ref": ["n", "o"]},
    "06-mayusculas-rectas": {"glifos": ["H", "I", "L", "E", "F", "T"], "ref": ["O"]},
    "07-mayusculas-redondas": {"glifos": ["O", "C", "G", "Q", "D", "S"], "ref": ["H"]},
    "08-mayusculas-panzas": {"glifos": ["B", "P", "R", "U", "J"], "ref": ["H", "O"]},
    "09-mayusculas-diagonales": {"glifos": ["A", "V", "W", "X", "Y", "K", "M", "N", "Z"], "ref": ["H"]},
    "10-cifras": {"glifos": ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"],
                  "ref": ["H"]},
    "11-signos": {"glifos": ["period", "comma", "colon", "semicolon", "exclam", "question", "exclamdown",
                             "questiondown", "quoteleft", "quoteright", "quotedblleft", "quotedblright",
                             "hyphen", "endash", "emdash", "parenleft", "parenright", "guillemotleft",
                             "guillemotright"], "ref": ["n", "H"]},
    "12-especiales": {"glifos": ["ampersand", "at", "Euro", "dollar", "percent", "numbersign",
                                 "germandbls", "eth", "thorn", "florin", "ae", "oe", "AE", "OE"],
                      "ref": ["n", "H"]},
}
POR_FILA = 6
GAP = 160            # espacio entre celdas (unidades)
TOP, BOTTOM = 960, -300      # zona vertical de cada celda (el texto va debajo)
ROW_H = TOP - BOTTOM + 220
MARGIN = 420
MARK = 60            # lado de las marcas de registro
GRIS = "#B8B8B8"
GUIA = "#4DB6E8"


# --- Utilidades de contornos ---------------------------------------------------------------

def contours_of(rec):
    out, cur = [], []
    for op, args in rec:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur + [("closePath", ())])
    return out


def bounds(cs):
    p = BoundsPen(None)
    for ctr in cs:
        for op, args in ctr:
            getattr(p, op)(*args)
    return p.bounds


def to_d(cs, tx):
    """Contornos (unidades de fuente) → atributo d de SVG, con tx(x, y) → (X, Y)."""
    parts = []
    for ctr in cs:
        for op, args in ctr:
            pts = [tx(*p) for p in args]
            if op == "moveTo":
                parts.append("M{:.1f} {:.1f}".format(*pts[0]))
            elif op == "lineTo":
                parts.append("L{:.1f} {:.1f}".format(*pts[0]))
            elif op == "curveTo":
                parts.append("C" + " ".join("{:.1f} {:.1f}".format(*p) for p in pts))
            elif op == "qCurveTo":
                parts.append("Q" + " ".join("{:.1f} {:.1f}".format(*p) for p in pts))
            elif op == "closePath":
                parts.append("Z")
    return " ".join(parts)


def label(name, cmap_rev):
    u = cmap_rev.get(name)
    ch = chr(u) if u and u > 32 else ""
    return f"{ch}  {name}" if ch and ch != name else name


# --- Distribución de una hoja (compartida por exportar e importar) -----------------------

def layout(familia, adv):
    """Celdas de la hoja: lista de (glifo, es_referencia, x0, baseline_y, ancho)."""
    spec = FAMILIAS[familia]
    items = [(g, True) for g in spec["ref"] if g not in spec["glifos"]] + [(g, False) for g in spec["glifos"]]
    cells, x, row = [], MARGIN, 0
    for i, (g, ref) in enumerate(items):
        if i and i % POR_FILA == 0:
            row += 1
            x = MARGIN
        w = adv.get(g, 600)
        base_y = MARGIN + MARK + 100 + row * ROW_H + TOP
        cells.append((g, ref, x, base_y, w))
        x += w + GAP
    width = max(c[2] + c[4] for c in cells) + MARGIN + 160
    height = cells[-1][3] - BOTTOM + 220 + MARK + MARGIN
    return cells, width, height


def marks(width, height):
    """Centros de las marcas de registro (arriba-izquierda, abajo-derecha) en la hoja."""
    m = MARGIN / 2
    return (m + MARK / 2, m + MARK / 2), (width - m - MARK / 2, height - m - MARK / 2)


# --- Exportar --------------------------------------------------------------------------------

def overshoot(glyphs):
    b = bounds(glyphs["o"])
    return round(b[3] - C.X_HEIGHT), round(-b[1])


def exportar(font_path):
    from fontTools.ttLib import TTFont
    t = TTFont(str(font_path))
    gs = t.getGlyphSet()
    adv = {n: t["hmtx"][n][0] for n in t.getGlyphOrder()}
    cmap_rev = {v: k for k, v in t.getBestCmap().items()}
    glyphs = {}
    for n in t.getGlyphOrder():
        rec = RecordingPen()
        gs[n].draw(rec)
        glyphs[n] = contours_of(rec.value)
    os_top, os_bot = overshoot(glyphs)
    guias = [("línea base", 0, 1.6), (f"altura de x {C.X_HEIGHT}", C.X_HEIGHT, 1.2),
             (f"mayúsculas {C.CAP_HEIGHT}", C.CAP_HEIGHT, 1.2),
             (f"sobresalto +{os_top}", C.X_HEIGHT + os_top, 0.6), (f"sobresalto −{os_bot}", -os_bot, 0.6)]
    if C.ASCENDER != C.CAP_HEIGHT:
        guias.append((f"ascendentes {C.ASCENDER}", C.ASCENDER, 1.0))
    guias.append((f"descendentes {C.DESCENDER}", C.DESCENDER, 1.0))
    HOJAS.mkdir(exist_ok=True)
    manifest = {"fuente": str(Path(font_path).name), "familias": {}}
    for familia in FAMILIAS:
        cells, W, H = layout(familia, adv)
        (ax, ay), (bx, by) = marks(W, H)
        out = [f'<svg xmlns="{SVG_NS}" width="{W}px" height="{H}px" viewBox="0 0 {W} {H}">',
               f'<title>{C.FAMILY} · {familia}</title>',
               f'<rect id="fondo" x="0" y="0" width="{W}" height="{H}" fill="none" stroke="none"/>']
        # guías: solo trazo
        out.append('<g id="guias" fill="none" stroke="%s">' % GUIA)
        for g, ref, x0, by_, w in cells:
            for nombre, y, sw in guias:
                dash = ' stroke-dasharray="12 10"' if "sobresalto" in nombre else ""
                out.append(f'<line x1="{x0 - 40}" y1="{by_ - y}" x2="{x0 + w + 40}" y2="{by_ - y}" '
                           f'stroke-width="{sw * 2}"{dash}/>')
            out.append(f'<rect x="{x0}" y="{by_ - TOP}" width="{w}" height="{TOP - BOTTOM}" stroke-width="2" '
                       f'stroke-dasharray="4 8"/>')
        out.append("</g>")
        # nombres de las guías, a la izquierda de cada fila
        out.append('<g id="nombres-guias" fill="%s" font-family="sans-serif" font-size="34">' % GUIA)
        filas = sorted({c[3] for c in cells})
        for by_ in filas:
            fin = max(c[2] + c[4] for c in cells if c[3] == by_) + 60
            for nombre, y, sw in guias:
                # los sobresaltos van a la derecha para no encimarse con su guía vecina
                if "sobresalto" in nombre:
                    out.append(f'<text x="{fin}" y="{by_ - y + 12}">{nombre}</text>')
                else:
                    out.append(f'<text x="{MARGIN - 40}" y="{by_ - y - 8}" text-anchor="end">{nombre}</text>')
        out.append("</g>")
        # etiquetas (texto, no se importa)
        out.append('<g id="etiquetas" fill="#808080" font-family="sans-serif" font-size="56">')
        for g, ref, x0, by_, w in cells:
            txt = label(g, cmap_rev) + ("  (referencia)" if ref else "")
            out.append(f'<text x="{x0}" y="{by_ - BOTTOM + 90}">{escape(txt)}</text>')
        out.append("</g>")
        # marcas de registro
        out.append('<g id="registro" fill="#000000">')
        for cx, cy in ((ax, ay), (bx, by)):
            out.append(f'<rect x="{cx - MARK / 2}" y="{cy - MARK / 2}" width="{MARK}" height="{MARK}"/>')
        out.append("</g>")
        # referencias en gris
        out.append(f'<g id="referencia" fill="{GRIS}">')
        for g, ref, x0, by_, w in cells:
            if ref and g in glyphs:
                out.append(f'<path id="ref-{g}" d="{to_d(glyphs[g], lambda x, y: (x0 + x, by_ - y))}"/>')
        out.append("</g>")
        # glifos editables: un grupo por glifo
        out.append('<g id="glifos" fill="#000000">')
        hashes = {}
        for g, ref, x0, by_, w in cells:
            if ref or g not in glyphs:
                continue
            out.append(f'<g id="{g}"><path d="{to_d(glyphs[g], lambda x, y: (x0 + x, by_ - y))}"/></g>')
            hashes[g] = signature(glyphs[g])
        out.append("</g></svg>")
        (HOJAS / f"{familia}.svg").write_text("\n".join(out), encoding="utf-8")
        manifest["familias"][familia] = hashes
        print(f"hojas/{familia}.svg: {len(hashes)} glifos")
    (HOJAS / "manifiesto.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")


def signature(cs):
    """Puntos sobre la curva de un glifo, redondeados y ordenados."""
    return sorted({(round(a[-1][0]), round(a[-1][1])) for ctr in cs for op, a in ctr if a})


def same(cs, sig, tol=3):
    """¿El glifo editado es igual al exportado (dentro de una tolerancia)?"""
    if not sig:
        return False
    new = signature(cs)
    sig = [tuple(p) for p in sig]
    return len(new) == len(sig) and all(abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol
                                        for a, b in zip(new, sig))


# --- Leer un SVG exportado por Affinity -----------------------------------------------------

def _style(el, inherited):
    st = dict(inherited)
    for k in ("fill", "stroke", "display"):
        if el.get(k) is not None:
            st[k] = el.get(k).strip()
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            if k.strip() in ("fill", "stroke", "display"):
                st[k.strip()] = v.strip()
    return st


def _shape_d(el, tag):
    f = lambda k: float(el.get(k, 0) or 0)  # noqa: E731
    if tag == "path":
        return el.get("d")
    if tag == "rect":
        x, y, w, h = f("x"), f("y"), f("width"), f("height")
        return f"M{x} {y} H{x + w} V{y + h} H{x} Z"
    if tag in ("polygon", "polyline"):
        pts = (el.get("points") or "").replace(",", " ").split()
        if len(pts) < 4:
            return None
        xy = [f"{pts[i]} {pts[i + 1]}" for i in range(0, len(pts) - 1, 2)]
        return "M" + " L".join(xy) + (" Z" if tag == "polygon" else "")
    if tag in ("circle", "ellipse"):
        cx, cy = f("cx"), f("cy")
        rx = f("r") if tag == "circle" else f("rx")
        ry = f("r") if tag == "circle" else f("ry")
        return (f"M{cx + rx} {cy} A{rx} {ry} 0 1 0 {cx - rx} {cy} A{rx} {ry} 0 1 0 {cx + rx} {cy} Z")
    return None


def leer_svg(path):
    """Contornos rellenos del SVG (en coordenadas de la hoja) con el id del grupo que los contiene."""
    root = ET.parse(str(path)).getroot()
    shapes = []

    def walk(el, tf, st, ids):
        tag = el.tag.rsplit("}", 1)[-1]
        if tag in ("defs", "clipPath", "mask", "title", "desc", "text", "metadata"):
            return
        t2 = tf.transform(parse_transform(el.get("transform")))
        st2 = _style(el, st)
        ids2 = ids + ([el.get("id")] if el.get("id") else [])
        if st2.get("display") == "none":
            return
        d = _shape_d(el, tag)
        if d and st2.get("fill", "#000") not in ("none", "transparent"):
            rec = RecordingPen()
            parse_path(d, TransformPen(rec, t2))
            for ctr in contours_of(rec.value):
                # quita el punto final repetido que añade "Z" al cerrar con una recta
                if len(ctr) > 2 and ctr[-2][0] == "lineTo" and math.dist(ctr[-2][1][0], ctr[0][1][0]) < 0.5:
                    ctr = ctr[:-2] + [ctr[-1]]
                if len(ctr) > 2:
                    shapes.append((ctr, ids2))
        for child in el:
            walk(child, t2, st2, ids2)

    walk(root, Identity, {"fill": "#000"}, [])
    return shapes


def calibrar(shapes, width, height):
    """Encuentra las marcas de registro y devuelve una función hoja-exportada → hoja-original."""
    cands = []
    for ctr, ids in shapes:
        b = bounds([ctr])
        w, h = b[2] - b[0], b[3] - b[1]
        if w > 0 and h > 0 and abs(w - h) / max(w, h) < 0.08:
            cands.append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, w, ctr, ids))
    reg = [c for c in cands if any("registro" in (i or "") for i in c[4])]
    if len(reg) < 2:      # sin ids: los dos cuadros más cercanos a las esquinas opuestas
        reg = [min(cands, key=lambda c: c[0] + c[1]), max(cands, key=lambda c: c[0] + c[1])]
    reg = sorted(reg, key=lambda c: c[0] + c[1])
    (sax, say), (sbx, sby) = (reg[0][0], reg[0][1]), (reg[-1][0], reg[-1][1])
    (ax, ay), (bx, by) = marks(width, height)
    s = math.hypot(bx - ax, by - ay) / math.hypot(sbx - sax, sby - say)
    marks_ids = {id(reg[0][3]), id(reg[-1][3])}
    return (lambda x, y: (ax + (x - sax) * s, ay + (y - say) * s)), s, marks_ids


def leer_hoja(path, adv):
    """Glifos de una hoja editada: {glifo: contornos en unidades de fuente}."""
    familia = Path(path).stem
    cells, W, H = layout(familia, adv)
    shapes = leer_svg(path)
    tf, scale, marks_ids = calibrar(shapes, W, H)
    out = {g: [] for g, ref, *_ in cells if not ref}
    for ctr, ids in shapes:
        if id(ctr) in marks_ids or any(i and (i.startswith("ref-") or i == "referencia") for i in ids):
            continue
        new = [(op, tuple(tf(*p) for p in args)) for op, args in ctr]
        b = bounds([new])
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        for g, ref, x0, by_, w in cells:
            if ref:
                continue
            if x0 - GAP / 2 <= cx <= x0 + w + GAP / 2 and by_ - TOP <= cy <= by_ - BOTTOM:
                out[g].append([(op, tuple((x - x0, by_ - y) for x, y in args)) for op, args in new])
                break
    return out, scale


# --- Importar al maestro (FontForge) --------------------------------------------------------------

def base_of(name, font):
    u = font[name].unicode
    if u is None or u < 0:
        return None
    d = unicodedata.normalize("NFD", chr(u))
    if len(d) < 2:
        return None
    b = ord(d[0])
    return next((g.glyphname for g in font.glyphs() if g.unicode == b), None)


def importar(paths, acentos=True):
    import fontforge
    font = fontforge.open(str(C.SFD))
    adv = {g.glyphname: g.width for g in font.glyphs()}
    manifest = json.loads((HOJAS / "manifiesto.json").read_text(encoding="utf-8"))
    cambiados = []
    for path in paths:
        fam = Path(path).stem
        if fam not in FAMILIAS:
            print(f"omito {path}: no es una hoja de familia")
            continue
        glyphs, scale = leer_hoja(path, adv)
        print(f"{Path(path).name}: escala de Affinity ×{scale:.3f}")
        for g, cs in glyphs.items():
            if not cs:
                print(f"  {g}: la celda está vacía; no lo toco")
                continue
            if same(cs, manifest["familias"].get(fam, {}).get(g)):
                continue
            glyph = font[g]
            width = glyph.width
            glyph.clear()
            pen = glyph.glyphPen()
            for ctr in cs:
                for op, args in ctr:
                    getattr(pen, op)(*args)
            pen = None
            glyph.width = width
            glyph.removeOverlap()
            glyph.correctDirection()
            glyph.round()
            cambiados.append(g)
            print(f"  {g}: actualizado")
    if acentos and cambiados:
        for g in font.glyphs():
            base = base_of(g.glyphname, font)
            if base not in cambiados:
                continue
            ref_top = C.X_HEIGHT if font[base].unicode and chr(font[base].unicode).islower() else C.CAP_HEIGHT
            marcas = [c for c in g.foreground if c.boundingBox()[1] > ref_top - 10 or c.boundingBox()[3] < 5]
            if not marcas:
                print(f"  {g.glyphname}: no pude separar el acento; corrígelo a mano")
                continue
            layer = fontforge.layer()
            for c in font[base].foreground:
                layer += c
            for c in marcas:
                layer += c
            g.foreground = layer
            g.width = font[base].width if g.width == 0 else g.width
            print(f"  {g.glyphname}: regenerada con el nuevo {base}")
    font.save(str(C.SFD))
    print(f"{len(cambiados)} glifos actualizados en {C.rel(C.SFD)}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("exportar", "importar"):
        sys.exit(__doc__)
    if sys.argv[1] == "exportar":
        default = C.ROOT / "fonts" / f"{C.FAMILY}-{C.STYLE}.otf"
        src = Path(sys.argv[2]) if len(sys.argv) > 2 else (default if default.exists()
                                                            else C.ESTABLE_OTF)
        exportar(src)
    else:
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        paths = [Path(a) for a in args] or sorted(HOJAS.glob("[0-9][0-9]-*.svg"))
        importar(paths, acentos="--sin-acentos" not in sys.argv)


if __name__ == "__main__":
    main()

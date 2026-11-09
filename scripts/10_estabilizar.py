"""Estabiliza la altura de x y la línea base de las minúsculas, y calcula el kerning.

Uso:  python pipeline/scripts/10_estabilizar.py [ENTRADA.otf] [SALIDA.otf]
      por defecto: sources/<slug>-base.otf → sources/<slug>-estable.otf

No cambia la forma de ningún glifo: solo mueve en vertical los puntos que
tocan la altura de x o la línea base (y sus manijas, para no deformar curvas).

- Extremos planos (astas, barras, cortes): exactamente en la altura de x y en 0.
- Extremos redondos (curvas con tangente horizontal): con el mismo sobresalto
  que la o, arriba y abajo (Cheng, *Designing Type*: las redondas sobresalen
  para verse del mismo tamaño que las rectas).
- Kerning por perfiles de tinta para los pares críticos, agrupado por letra
  base (Tracy: el kerning corrige excepciones). Se escribe en sources/kern.fea.
"""
import importlib
import math
import sys
import unicodedata
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

G = importlib.import_module("06_completar_set")
ROOT = C.ROOT
SRC = C.BASE_OTF
OUT = C.ESTABLE_OTF
KERN_FEA = C.KERN_FEA
REPORT = C.PROOFS / "estabilizar.md"
BAND = 25          # tolerancia alrededor de la altura de x y la línea base
EXTRA = {"dotlessi", "f_i", "f_l"}


# --- Carga --------------------------------------------------------------------------

def load(path):
    src = TTFont(str(path))
    gs = src.getGlyphSet()
    glyphs, adv = {}, {}
    for name in src.getGlyphOrder():
        rec = RecordingPen()
        gs[name].draw(rec)
        glyphs[name] = G.contours_of(rec.value)
        adv[name] = src["hmtx"][name][0]
    return src, list(src.getGlyphOrder()), dict(src.getBestCmap()), glyphs, adv


def is_lower(name, cmap):
    if name.split(".")[0] in EXTRA:
        return True
    uni = next((u for u, n in cmap.items() if n == name.split(".")[0]), None)
    if not uni:
        return False
    base = unicodedata.normalize("NFD", chr(uni))[0]
    return base.isalpha() and base.islower()


def true_bounds(cs):
    p = BoundsPen(None)
    for ctr in cs:
        for op, args in ctr:
            getattr(p, op)(*args)
    return p.bounds


# --- Altura de x ---------------------------------------------------------------------------

def overshoot(glyphs):
    """Sobresalto de la o arriba y abajo; config.OVERSHOOT lo fija si la o
    del proyecto no sirve de referencia (por ejemplo, si queda por debajo)."""
    if C.OVERSHOOT is not None:
        return C.OVERSHOOT, C.OVERSHOOT
    x0, y0, x1, y1 = true_bounds(glyphs["o"])
    return round(y1 - C.X_HEIGHT), round(-y0)


def _samples(ctr):
    """Muestras (x, y) de la curva real de un contorno, con el tipo de segmento."""
    out, cur, start = [], None, None
    for op, args in ctr:
        if op in ("closePath", "endPath") and cur and start and cur != start:
            op, args = "lineTo", (start,)          # el lado de cierre también cuenta
        if op == "moveTo":
            cur = start = args[0]
        elif op == "lineTo":
            p0, p1 = cur, args[0]
            for i in range(1, 11):
                t = i / 10
                out.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t,
                            "flat" if abs(p1[1] - p0[1]) < 1.5 and abs(p1[0] - p0[0]) > 15 else "line"))
            cur = p1
        elif op == "curveTo":
            p0, (c1, c2, p3) = cur, args
            for i in range(1, 21):
                t = i / 20
                mt = 1 - t
                out.append((mt ** 3 * p0[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t ** 3 * p3[0],
                            mt ** 3 * p0[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t ** 3 * p3[1],
                            "curve"))
            cur = p3
    return out


def _runs(samples, inside):
    """Tramos consecutivos (cíclicos) de muestras que cumplen inside(y)."""
    n = len(samples)
    flags = [inside(s[1]) for s in samples]
    if all(flags) or not any(flags):
        return [samples] if all(flags) else []
    start = flags.index(False)
    runs, cur = [], []
    for k in range(1, n + 1):
        s = samples[(start + k) % n]
        if inside(s[1]):
            cur.append(s)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def snap_glyph(cs, os_top, os_bot):
    """Lleva cada extremo de la zona de x y de la línea base a su altura:
    planos a XH y 0, redondos con el sobresalto de la o. Los puntos de la
    zona se desplazan con una transición suave para no deformar la curva."""
    XH, RAMP = C.X_HEIGHT, 90
    out, moved = [], 0
    for ctr in cs:
        smp = _samples(ctr)
        if not smp:
            out.append(ctr)
            continue
        fixes = []          # (zona, xmin, xmax, dy)
        for zone, inside in (("top", lambda y: XH - 30 <= y <= XH + BAND),
                             ("bot", lambda y: -BAND <= y <= 30)):
            for run in _runs(smp, inside):
                ys = [s[1] for s in run]
                ext = max(ys) if zone == "top" else min(ys)
                # un extremo real entra y sale de la zona por el lado interior;
                # un trazo que solo cruza la zona no es extremo
                if zone == "top" and (run[0][1] > XH - 20 or run[-1][1] > XH - 20) and len(run) < len(smp):
                    if not any(s[2] == "flat" for s in run):
                        continue
                if zone == "bot" and (run[0][1] < 20 or run[-1][1] < 20) and len(run) < len(smp):
                    if not any(s[2] == "flat" for s in run):
                        continue
                # el extremo debe ser un máximo/mínimo local de verdad (no un corte que cruza la zona)
                if zone == "top" and ext < XH - BAND or zone == "bot" and ext > BAND:
                    continue
                flat = any(s[2] == "flat" and abs(s[1] - ext) < 2 for s in run)
                target = (XH if flat else XH + os_top) if zone == "top" else (0 if flat else -os_bot)
                dy = target - ext
                if 0.5 <= abs(dy) <= BAND:
                    xs = [s[0] for s in run]
                    fixes.append((zone, min(xs) - 15, max(xs) + 15, dy))
        if not fixes:
            out.append(ctr)
            continue

        def shift(pt):
            x, y = pt
            for zone, x0, x1, dy in fixes:
                if not x0 <= x <= x1:
                    continue
                if zone == "top" and XH - RAMP <= y <= XH + 40:
                    w = min(1.0, (y - (XH - RAMP)) / (RAMP - 10))
                    return (x, y + dy * w)
                if zone == "bot" and -40 <= y <= RAMP:
                    w = min(1.0, ((RAMP) - y) / (RAMP - 10))
                    return (x, y + dy * w)
            return (x, y)

        out.append([(op, tuple(shift(p) for p in args)) for op, args in ctr])
        moved += len(fixes)
    return out, moved


def estabilizar(order, cmap, glyphs):
    os_top, os_bot = overshoot(glyphs)
    lines = ["# Altura de x estabilizada", "",
             f"Altura de x {C.X_HEIGHT}; sobresalto de redondas: +{os_top} arriba, −{os_bot} abajo "
             f"({'fijado en proyecto.py' if C.OVERSHOOT is not None else 'medido en la o'}).", "",
             "| Glifo | Extremos ajustados |", "| --- | --- |"]
    total = 0
    for g in order:
        if not is_lower(g, cmap) or (g == "o" and C.OVERSHOOT is None):
            continue
        new, moved = snap_glyph(glyphs[g], os_top, os_bot)
        if moved:
            glyphs[g] = new
            total += moved
            lines.append(f"| `{g}` | {moved} |")
    return total, lines


# --- Kerning ------------------------------------------------------------------------------

KERN_LEFT = ["A", "F", "K", "L", "P", "R", "T", "V", "W", "X", "Y", "f", "k", "r", "v", "w", "x", "y",
             "quoteright", "quotedblright", "period", "comma", "hyphen"]
KERN_RIGHT = ["A", "C", "G", "J", "O", "Q", "T", "U", "V", "W", "Y", "a", "c", "d", "e", "g", "o", "q", "s",
              "u", "v", "w", "x", "y", "z", "period", "comma", "hyphen", "quoteleft", "quotedblleft"]
STEP = 4


def profile(cs, y0, y1):
    """Extremos izquierdo y derecho de la tinta por fila (rasterizado)."""
    b = G.bounds(cs)
    if not b:
        return []
    polys = []

    class Flat(BasePen):
        def __init__(self):
            super().__init__(None)
            self.cur = []

        def _moveTo(self, p):
            self.cur = [p]

        def _lineTo(self, p):
            self.cur.append(p)

        def _curveToOne(self, p1, p2, p3):
            p0 = self.cur[-1]
            for t in (i / 8 for i in range(1, 9)):
                mt = 1 - t
                self.cur.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                                 mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))

        def _closePath(self):
            polys.append(self.cur)

    pen = Flat()
    for ctr in cs:
        for op, args in ctr:
            getattr(pen, op)(*args)
    ox = b[0] - 10
    w, h = int((b[2] - ox) / STEP) + 4, int((y1 - y0) / STEP) + 1
    img = Image.new("1", (w, h), 0)
    d = ImageDraw.Draw(img)
    for p in polys:
        if len(p) > 2:
            d.polygon([((x - ox) / STEP, (y1 - y) / STEP) for x, y in p], fill=1)
    px = img.load()
    rows = []
    for j in range(h):
        xs = [i for i in range(w) if px[i, j]]
        rows.append((ox + xs[0] * STEP, ox + (xs[-1] + 1) * STEP) if xs else None)
    return rows


def kernear(order, cmap, glyphs, adv):
    zone = (-150, C.CAP_HEIGHT + 20)
    left = [g for g in KERN_LEFT if g in glyphs and glyphs[g]]
    right = [g for g in KERN_RIGHT if g in glyphs and glyphs[g]]
    names = set(left + right + ["H", "n"])
    prof = {g: profile(glyphs[g], *zone) for g in names}

    def gap(l, r):
        best = None
        for a, b in zip(prof[l], prof[r]):
            if a and b:
                d = (adv[l] - a[1]) + b[0]
                best = d if best is None else min(best, d)
        if best is None:
            best = (adv[l] - G.bounds(glyphs[l])[2]) + G.bounds(glyphs[r])[0]
        return best

    ref_uc, ref_lc = gap("H", "H"), gap("n", "n")
    pairs = {}
    for l in left:
        for r in right:
            if len(l) > 1 and len(r) > 1:
                continue
            reference = ref_lc if (l.islower() or r.islower()) else ref_uc
            k = round(0.65 * (reference - gap(l, r)) / 5) * 5
            k = max(-120, min(0, k))
            if k <= -15:
                pairs[(l, r)] = k
    groups = {}
    for g in order:
        root = g.split(".")[0]
        uni = next((u for u, n in cmap.items() if n == root), None)
        if not uni:
            continue
        base = unicodedata.normalize("NFD", chr(uni))[0]
        head = cmap.get(ord(base))
        if head:
            groups.setdefault(head, set()).add(g)
    lines = ["# Generado por pipeline/scripts/10_estabilizar.py: kerning por perfiles, por clases.", ""]
    used = sorted({n for p in pairs for n in p})
    for name in used:
        members = sorted(m for m in groups.get(name, {name}) if not m.endswith(".case"))
        lines.append(f"@K_{name} = [{' '.join(members)}];")
    lines += ["", "lookup kern_pares {"]
    lines += [f"    pos @K_{l} @K_{r} {k};" for (l, r), k in sorted(pairs.items())]
    lines += ["} kern_pares;", "", "feature kern {", "    lookup kern_pares;", "} kern;", ""]
    KERN_FEA.write_text("\n".join(lines), encoding="utf-8")
    return pairs


# --- Guardado ------------------------------------------------------------------------------

def save(src, order, cmap, glyphs, adv, path):
    cs, metrics = {}, {}
    for name in order:
        pen = T2CharStringPen(adv[name], None)
        for ctr in glyphs[name]:
            for op, args in ctr:
                getattr(pen, op)(*args)
        cs[name] = pen.getCharString()
        b = G.bounds(glyphs[name])
        metrics[name] = (adv[name], round(b[0]) if b else 0)
    fb = FontBuilder(C.UPM, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupCFF(f"{C.FAMILY}-{C.STYLE}", {"FullName": f"{C.FAMILY} {C.STYLE}", "FamilyName": C.FAMILY, "Weight": C.STYLE},
                cs, {})
    fb.setupHorizontalMetrics(metrics)
    fb.font["hhea"] = src["hhea"]
    fb.font["OS/2"] = src["OS/2"]
    fb.font["name"] = src["name"]
    fb.setupPost()
    fea = C.FEATURES.read_text(encoding="utf-8")
    if "include(kern.fea);" not in fea:
        fea += "\ninclude(kern.fea);\n"
        C.FEATURES.write_text(fea, encoding="utf-8")
    addOpenTypeFeaturesFromString(fb.font, fea.replace("include(kern.fea);", KERN_FEA.read_text(encoding="utf-8")),
                                  tables=["GSUB", "GPOS", "name"])
    fb.font["hhea"].numberOfHMetrics = len(order)
    fb.save(str(path))


def main():
    src_path = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    src, order, cmap, glyphs, adv = load(src_path)
    total, lines = estabilizar(order, cmap, glyphs)
    pairs = kernear(order, cmap, glyphs, adv)
    save(src, order, cmap, glyphs, adv, out_path)
    lines += ["", f"Kerning: {len(pairs)} pares por clases en `sources/kern.fea`."]
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"altura de x: {total} puntos ajustados · kerning: {len(pairs)} pares → {out_path}")


if __name__ == "__main__":
    main()

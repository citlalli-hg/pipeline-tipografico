"""Construye la base del proyecto a partir de una fuente de partida y completa el set.

Uso:  python pipeline/scripts/06_completar_set.py      (o `mise run completar`)
Entrada: config.FUENTE_BASE (en proyecto.py)
Salida:  sources/<slug>-base.otf, sources/features.fea y proofs/set-generado.md

Pasos:
  1. Copia todos los glifos de la fuente de partida SIN cambiar su forma y
     corrige la línea base (config.BASELINE_SHIFT).
  2. Si existe proyecto/completar.py, llama a su función `construir(f)`:
     ahí cada fuente construye lo que le falta (glifos derivados, variantes,
     ligaduras). Puede devolver el texto de features.fea.
  3. Si config.ESPACIADO tiene valores, aplica el espaciado provisional por
     lados (método de Tracy): solo mueve los glifos en horizontal.

Utilidades para proyecto/completar.py: el objeto `f` (Draft) y el módulo
`contornos` (move, transform, bounds, rect, line, arc, disk, above...).

Solo requiere fontTools: funciona igual en Windows, macOS y Linux.
"""
import importlib.util
import sys
from pathlib import Path

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from contornos import *  # noqa: E402,F401,F403  (los scripts 10 y 11 importan las utilidades desde aquí)
from contornos import bounds, contours_of, move  # noqa: E402

ROOT = C.ROOT
OUT = C.BASE_OTF
REPORT = C.PROOFS / "set-generado.md"
FEA = C.FEATURES
SB = C.SIDEBEARING

FEATURES_MINIMAS = """\
# Generado por pipeline/scripts/06_completar_set.py
languagesystem DFLT dflt;
languagesystem latn dflt;
languagesystem latn ESP;
"""


# --- Fuente --------------------------------------------------------------------

class Draft:
    def __init__(self, path, shift=0):
        self.src = TTFont(path)
        gs = self.src.getGlyphSet()
        hm = self.src["hmtx"]
        self.order = list(self.src.getGlyphOrder())
        self.cmap = dict(self.src.getBestCmap())
        self.glyphs, self.adv = {}, {}
        for name in self.order:
            rec = RecordingPen()
            gs[name].draw(rec)
            self.glyphs[name] = move(contours_of(rec.value), dy=shift)
            self.adv[name] = hm[name][0]
        self.new = []      # (nombre, carácter, descripción)
        self.notas = []    # líneas extra para el reporte
        self.sb = SB       # margen de add(fit=True); el proyecto puede cambiarlo

    def get(self, name):
        return [list(c) for c in self.glyphs[name]]

    def add(self, name, cs, adv=None, uni=None, note="", fit=True):
        """Añade un glifo. Con fit=True coloca la tinta a self.sb del origen y
        calcula el avance con el mismo margen a la derecha."""
        if cs and fit:
            x0, _, x1, _ = bounds(cs)
            cs = move(cs, dx=self.sb - x0)
            adv = adv or round(x1 - x0 + 2 * self.sb)
        if name not in self.glyphs:
            self.order.append(name)
        self.glyphs[name] = cs
        self.adv[name] = adv if adv is not None else self.adv.get(name, 500)
        if uni is not None:
            self.cmap[uni] = name
        self.new.append((name, chr(uni) if uni and uni > 32 else "", note))

    def ink(self, name):
        return bounds(self.glyphs[name])

    def center_x(self, name):
        x0, _, x1, _ = self.ink(name)
        return (x0 + x1) / 2


# --- Espaciado provisional ----------------------------------------------------------

def side_value(name, side):
    """Margen de un lado según config.ESPACIADO (clase o número)."""
    spec = C.ESPACIADO.get(name)
    if spec is None:
        return None
    v = spec[0 if side == "L" else 1]
    if isinstance(v, (int, float)):
        return v
    table = C.LADOS_MAY if name[:1].isupper() else C.LADOS_MIN
    return table[v]


def respace(f):
    """Coloca la tinta con el margen izquierdo y fija el avance con el derecho.
    Solo mueve el glifo en horizontal: la forma no cambia."""
    n = 0
    for name in list(f.glyphs):
        cs = f.glyphs[name]
        lsb, rsb = side_value(name, "L"), side_value(name, "R")
        if not cs or lsb is None:
            continue
        x0, _, x1, _ = bounds(cs)
        f.glyphs[name] = move(cs, dx=lsb - x0)
        f.adv[name] = round(x1 - x0 + lsb + rsb)
        n += 1
    return n


# --- Proyecto -------------------------------------------------------------------------

def run_hook(f):
    if not C.COMPLETAR.is_file():
        return None
    spec = importlib.util.spec_from_file_location("completar_proyecto", C.COMPLETAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.construir(f)


def limpiar_curvas(f, nombres=None, que="glifos construidos"):
    """Puntos en extremos, (quiebres,) asas H/V y armonización G2 en los glifos
    elegidos (config.LIMPIAR_CURVAS, config.LIMPIAR_QUIEBRES)."""
    sel = C.LIMPIAR_CURVAS
    if not sel:
        return
    import curvas as K
    if nombres is None:
        if sel == "bocetos":
            nombres = [n for n, _, note in f.new if "boceto" in note]
        elif sel == "todo":
            nombres = [n for n, _, _ in f.new]
        else:
            nombres = list(sel)
    total, hechos = 0, 0
    for n in dict.fromkeys(nombres):
        if f.glyphs.get(n):
            f.glyphs[n], movidos = K.limpiar(f.glyphs[n], quiebres=C.LIMPIAR_QUIEBRES)
            total += movidos
            hechos += 1
    f.notas.append(f"Curvas limpiadas en {hechos} {que} (extremos, "
                   f"{'quiebres, ' if C.LIMPIAR_QUIEBRES else ''}asas H/V, G2): {total} nodos ajustados.")


def save(f, features):
    order = [".notdef"] + [g for g in f.order if g != ".notdef"]
    charstrings = {}
    for name in order:
        pen = T2CharStringPen(f.adv[name], None)
        for ctr in f.glyphs.get(name, []):
            for op, args in ctr:
                getattr(pen, op)(*args)
        charstrings[name] = pen.getCharString()
    metrics = {}
    for name in order:
        b = bounds(f.glyphs.get(name, []))
        metrics[name] = (f.adv[name], round(b[0]) if b else 0)

    ps = f"{C.FAMILY}-{C.STYLE}"
    fb = FontBuilder(C.UPM, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(f.cmap)
    fb.setupCFF(ps, {"FullName": f"{C.FAMILY} {C.STYLE}", "FamilyName": C.FAMILY, "Weight": C.STYLE},
                charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=C.ASCENT, descent=-C.DESCENT, lineGap=0)
    fb.setupNameTable({
        "familyName": C.FAMILY, "styleName": C.STYLE,
        "uniqueFontIdentifier": f"{ps}-{C.VERSION}", "fullName": f"{C.FAMILY} {C.STYLE}",
        "psName": ps, "version": f"Version {C.VERSION}",
        "copyright": C.COPYRIGHT, "designer": C.DESIGNER,
    })
    fb.setupOS2(sTypoAscender=C.ASCENT, sTypoDescender=-C.DESCENT, sTypoLineGap=0,
                usWinAscent=C.ASCENT + 50, usWinDescent=C.DESCENT + 50, sxHeight=C.X_HEIGHT,
                sCapHeight=C.CAP_HEIGHT, usWeightClass=400, achVendID=C.VENDOR)
    fb.setupPost()
    FEA.parent.mkdir(exist_ok=True)
    FEA.write_text(features, encoding="utf-8")
    addOpenTypeFeaturesFromString(fb.font, features)
    OUT.parent.mkdir(exist_ok=True)
    fb.save(str(OUT))


def report(f, spaced):
    lines = [f"# Set generado para {C.FAMILY}", "",
             f"Base: `{C.FUENTE_BASE}`, línea base corregida ({C.BASELINE_SHIFT} unidades).", ""]
    if spaced:
        lines += [f"Espaciado provisional por lados en {spaced} glifos (`ESPACIADO` en `proyecto.py`).", ""]
    lines += [f"{len(f.new)} glifos nuevos o modificados. Revisa los marcados como **boceto**: su forma es una propuesta.", "",
              "| Glifo | Carácter | Origen |", "| --- | --- | --- |"]
    for name, ch, note in f.new:
        note = f"**{note}**" if "boceto" in note else note
        lines.append(f"| `{name}` | {ch} | {note} |")
    if f.notas:
        lines += [""] + f.notas
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if not C.FUENTE_BASE:
        sys.exit("proyecto.py no define FUENTE_BASE: esta etapa necesita una fuente de partida.")
    f = Draft(ROOT / C.FUENTE_BASE, C.BASELINE_SHIFT)
    if C.LIMPIAR_CURVAS == "todo":
        limpiar_curvas(f, list(f.glyphs), "glifos de partida")
    features = run_hook(f) or FEATURES_MINIMAS
    limpiar_curvas(f)
    spaced = respace(f) if C.ESPACIADO else 0
    save(f, features)
    report(f, spaced)
    print(f"{len(f.new)} glifos nuevos · {len(f.order)} en total → {C.rel(OUT)}")
    print(f"reporte: {C.rel(REPORT)}")


if __name__ == "__main__":
    main()

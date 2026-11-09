"""Revisión de curvas: reporte y peines de curvatura por familia de glifos.

Uso:  python pipeline/scripts/12_curvas.py [FUENTE.otf]      (o `mise run curvas`)
      FUENTE: por defecto fonts/<Familia>-Regular.otf o, si no existe, sources/<slug>-estable.otf
Salida:
  proofs/curvas.md               problemas por glifo (extremos sin nodo, quiebres,
                                 asas casi H/V, saltos de curvatura G2)
  proofs/curvatura/<familia>.svg  peines de curvatura (como en el diseño industrial:
                                 Autodesk Alias, Rhino) con los problemas marcados

Cómo leer un peine: cada diente mide la curvatura en ese punto. Un peine que
crece y decrece suave es una curva tensa y continua; un salto entre dientes
vecinos en un nodo es un cambio brusco de curvatura (se ve como un «bache»);
un peine que cambia de lado es una inflexión. Ábrelo en Affinity o en el
navegador junto a la hoja de la misma familia.

Solo requiere fontTools: funciona en Windows, macOS y Linux.
"""
import importlib
import sys
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import curvas as K  # noqa: E402
from contornos import bounds, contours_of  # noqa: E402

H = importlib.import_module("11_hojas")
SALIDA = C.PROOFS / "curvatura"
GRIS, PEINE, ALERTA = "#C8C8C8", "#D0338A", "#E5331A"


def _d(cs, tf):
    out = []
    for ctr in cs:
        for op, args in ctr:
            pts = [tf(*p) for p in args]
            cmd = {"moveTo": "M", "lineTo": "L", "curveTo": "C", "closePath": "Z"}.get(op)
            if cmd == "Z":
                out.append("Z")
            elif cmd:
                out.append(cmd + " ".join(f"{x:.1f} {y:.1f}" for x, y in pts))
    return " ".join(out)


def _marcas(cs):
    """Puntos donde hay problemas: [(x, y, tipo)]."""
    m = []
    for ctr in cs:
        segs = K.a_segmentos(ctr)
        n = len(segs)
        for i, s in enumerate(segs):
            for t in K.extremos_interiores(s):
                m.append((*K.punto(s, t), "extremo"))
            b = segs[(i + 1) % n]
            ta, tb = K.tangente_llegada(s), K.tangente_salida(b)
            if ta is None or tb is None:
                continue
            dang = K._diff(K._ang(ta), K._ang(tb))
            if K.ANG_LISO <= dang < K.ANG_QUIEBRE:
                m.append((*s[-1], "quiebre"))
            elif len(s) == 4 and len(b) == 4 and dang < K.ANG_LISO:
                k1, k2 = K.curvatura(s, 1), K.curvatura(b, 0)
                mx = max(abs(k1), abs(k2))
                if mx > 1e-4 and abs(k1 - k2) / mx > K.G2_TOL:
                    m.append((*s[-1], "G2"))
    return m


def hoja(familia, glyphs, adv):
    spec = H.FAMILIAS[familia]
    nombres = [g for g in spec["glifos"] if g in glyphs and glyphs[g]]
    if not nombres:
        return None
    pad, top = 80, C.ASCENT + 120
    x = pad
    cuerpo = []
    for g in nombres:
        w = adv.get(g, 600)
        base = top

        def tf(px, py, x=x, base=base):
            return (x + px, base - py)
        cuerpo.append(f'<g id="{g}"><path d="{_d(glyphs[g], tf)}" fill="{GRIS}"/>')
        dientes, env = K.peine(glyphs[g])
        lines = " ".join(f"M{tf(*p)[0]:.1f} {tf(*p)[1]:.1f}L{tf(*q)[0]:.1f} {tf(*q)[1]:.1f}" for p, q in dientes)
        cuerpo.append(f'<path d="{lines}" stroke="{PEINE}" stroke-width="0.8" fill="none" opacity="0.7"/>')
        for tramo in env:
            pts = " ".join(f"{tf(*q)[0]:.1f},{tf(*q)[1]:.1f}" for q in tramo)
            cuerpo.append(f'<polyline points="{pts}" stroke="{PEINE}" stroke-width="1.6" fill="none"/>')
        for mx, my, tipo in _marcas(glyphs[g]):
            cx, cy = tf(mx, my)
            cuerpo.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="none" stroke="{ALERTA}" stroke-width="2.5">'
                          f'<title>{tipo}</title></circle>')
        cuerpo.append(f'<text x="{x}" y="{top + 260}" font-family="sans-serif" font-size="28" fill="#777">{g}</text></g>')
        x += w + pad
    W, Hh = x + pad, top + 320
    ley = (f'<text x="{pad}" y="50" font-family="sans-serif" font-size="30" fill="#555">{C.FAMILY} · {familia} · '
           f'peine de curvatura (magenta) · círculos: extremo sin nodo, quiebre o salto G2</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}">'
            f'<rect width="{W}" height="{Hh}" fill="white"/>{ley}{"".join(cuerpo)}</svg>')


def main():
    default = C.FONTS / f"{C.FAMILY}-{C.STYLE}.otf"
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else (default if default.exists() else C.ESTABLE_OTF)
    t = TTFont(str(src))
    gs = t.getGlyphSet()
    glyphs, adv = {}, {}
    for n in t.getGlyphOrder():
        rec = RecordingPen()
        gs[n].draw(rec)
        glyphs[n] = contours_of(rec.value)
        adv[n] = t["hmtx"][n][0]
    # familias de las hojas (+ «14-otros» si el manifiesto la tiene)
    man = C.ROOT / "hojas" / "manifiesto.json"
    if man.exists():
        import json
        H._cargar_extras(json.loads(man.read_text(encoding="utf-8")))

    filas, tot = [], {}
    for n, cs in glyphs.items():
        if not cs:
            continue
        p, nodos = K.diagnosticar(cs)
        for k, v in p.items():
            tot[k] = tot.get(k, 0) + v
        if sum(p.values()):
            filas.append((sum(p.values()), n, nodos, p))
    filas.sort(reverse=True)
    tipos = list(tot)
    lines = [f"# Curvas de {C.FAMILY}", "", f"Fuente: `{C.rel(src)}`", "",
             "Totales: " + " · ".join(f"{k}: {v}" for k, v in tot.items()), "",
             "Qué hacer: *extremo sin nodo* → **Element › Add Extrema**; *quiebre* → decidir si es esquina "
             "o nodo liso (**Point › Curve**); *asa casi H/V* → enderezar con Shift; *salto G2* → mover el "
             "nodo sobre sus asas o ajustar el largo de las asas (ver `pipeline/docs/vectorizacion.md`).", "",
             "| Glifo | Nodos | " + " | ".join(tipos) + " |", "| --- | --- | " + " | ".join("---" for _ in tipos) + " |"]
    for _, n, nodos, p in filas:
        lines.append(f"| `{n}` | {nodos} | " + " | ".join(str(p[k]) for k in tipos) + " |")
    C.PROOFS.mkdir(exist_ok=True)
    (C.PROOFS / "curvas.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    SALIDA.mkdir(parents=True, exist_ok=True)
    hechas = 0
    for fam in H.FAMILIAS:
        svg = hoja(fam, glyphs, adv)
        if svg:
            (SALIDA / f"{fam}.svg").write_text(svg, encoding="utf-8")
            hechas += 1
    print(f"curvas: {sum(tot.values())} avisos en {len(filas)} glifos → {C.rel(C.PROOFS / 'curvas.md')}")
    print(f"peines: {hechas} hojas en {C.rel(SALIDA)}")


if __name__ == "__main__":
    main()

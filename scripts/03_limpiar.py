"""Etapas 4 y 6 — Limpieza técnica, componentes con acento y reporte de problemas.

Uso (con el Python de FontForge):
    python pipeline/scripts/03_limpiar.py            # limpia todos los glifos dibujados
    python pipeline/scripts/03_limpiar.py a n o      # solo estos
    python pipeline/scripts/03_limpiar.py --sin-limpiar   # solo componentes y reporte

La limpieza modifica contornos: córrela ANTES de retocar a mano. Después de
retocar en FontForge o Affinity, usa --sin-limpiar o limita los glifos.

Las correcciones ópticas (overshoot, peso de redondos, centro óptico) no se
automatizan: se hacen a mano siguiendo la etapa 4 del pipeline.
"""
import sys
import unicodedata
from pathlib import Path

import fontforge

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

# Bits de glyph.validate() que vale la pena reportar
CHECKS = {
    0x2: "contorno abierto",
    0x4: "se interseca a sí mismo",
    0x8: "dirección incorrecta",
    0x20: "faltan puntos en extremos",
    0x40000: "coordenadas no enteras",
}


def clean(g):
    g.removeOverlap()
    g.simplify(1.0, ("mergelines", "smoothcurves", "setstarttoextremum"))
    g.addExtrema("all")
    g.round()
    g.correctDirection()
    g.canonicalContours()
    g.canonicalStart()


# Marca combinante (NFD) → acento suelto (espaciado) que se dibuja en la fuente
MARCA = {0x0301: "acute", 0x0300: "grave", 0x0308: "dieresis", 0x0303: "tilde",
         0x0302: "circumflex", 0x0327: "cedilla", 0x030A: "ring", 0x030C: "caron"}
SIN_PUNTO = {"i": "dotlessi", "j": "dotlessj"}


def _ink(g):
    xmin, ymin, xmax, ymax = g.boundingBox()
    return xmin, ymin, xmax, ymax


def _por_referencias(font, g, uni):
    """Arma la acentuada como base + acento (referencias), sin depender de las
    tablas de acentos de FontForge: el acento se centra sobre la tinta de la
    base y, en mayúsculas, sube lo que va de la altura de x a la de mayúsculas."""
    import psMat
    nfd = unicodedata.normalize("NFD", chr(uni))
    if len(nfd) != 2 or ord(nfd[1]) not in MARCA:
        return False
    base_ch, mark = nfd[0], MARCA[ord(nfd[1])]
    base = next((x.glyphname for x in font.glyphs() if x.unicode == ord(base_ch)), None)
    if base_ch in SIN_PUNTO and SIN_PUNTO[base_ch] in font:
        base = SIN_PUNTO[base_ch]
    if not base or mark not in font or not len(font[base].foreground) or not len(font[mark].foreground):
        return False
    bx0, _, bx1, _ = _ink(font[base])
    mx0, my0, mx1, _ = _ink(font[mark])
    dx = (bx0 + bx1) / 2 - (mx0 + mx1) / 2
    dy = 0
    if base_ch.isupper() and my0 > 0:      # acento sobre la letra, no cedilla
        dy = C.CAP_HEIGHT - C.X_HEIGHT
    g.addReference(base)
    g.addReference(mark, psMat.translate(round(dx), round(dy)))
    g.width = font[base].width
    return True


def build_composites(font):
    built, failed = [], []
    for uni in C.COMPOSITES:
        g = font.createChar(uni)
        if len(g.references) or len(g.foreground):
            continue  # ya existe: no se reconstruye
        g.build()
        if not len(g.references):
            _por_referencias(font, g, uni)
        (built if len(g.references) else failed).append(g.glyphname)
    return built, failed


def report(font):
    lines = ["# Reporte de limpieza", "", "| Glifo | Problemas |", "| --- | --- |"]
    nombres = list(dict.fromkeys(list(C.DRAWN) + [g.glyphname for g in font.glyphs()]))
    for name in nombres:
        if name not in font:
            lines.append(f"| {name} | no existe |")
            continue
        g = font[name]
        if not len(g.foreground):
            lines.append(f"| {name} | vacío |")
            continue
        flags = g.validate(True)
        problems = [label for bit, label in CHECKS.items() if flags & bit]
        if problems:
            lines.append(f"| {name} | {', '.join(problems)} |")
    if len(lines) == 4:
        lines.append("| — | sin problemas técnicos |")
    return "\n".join(lines) + "\n"


def main():
    args = sys.argv[1:]
    if not C.SFD.exists():
        sys.exit(f"no existe {C.rel(C.SFD)}; corre primero 02_importar.py o 07_a_sfd.py")
    font = fontforge.open(str(C.SFD))
    names = [a for a in args if not a.startswith("--")] or C.DRAWN
    if "--sin-limpiar" not in args:
        n = 0
        for name in names:
            if name in font and len(font[name].foreground):
                clean(font[name])
                n += 1
        print(f"limpiados: {n} glifos")
    built, failed = build_composites(font)
    print(f"componentes creados: {len(built)}")
    if failed:
        print("no se pudieron construir (¿falta la base o el acento?):", " ".join(failed))
    font.save(str(C.SFD))
    out = C.PROOFS / "reporte-limpieza.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report(font), encoding="utf-8")
    print(f"reporte: {C.rel(out)}")


if __name__ == "__main__":
    main()

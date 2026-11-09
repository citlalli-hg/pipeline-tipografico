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


def build_composites(font):
    built, failed = [], []
    for uni in C.COMPOSITES:
        g = font.createChar(uni)
        if len(g.references) or len(g.foreground):
            continue  # ya existe: no se reconstruye
        g.build()
        (built if len(g.references) else failed).append(g.glyphname)
    return built, failed


def report(font):
    lines = ["# Reporte de limpieza", "", "| Glifo | Problemas |", "| --- | --- |"]
    for name in C.DRAWN:
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

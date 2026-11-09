"""Convierte sources/<slug>-base.otf en el maestro de FontForge.

Uso:  python pipeline/scripts/ff.py 07_a_sfd.py [FUENTE.otf] [--forzar]   (o `mise run maestro`)
      FUENTE.otf: por defecto sources/<slug>-base.otf
      --estable: usa sources/<slug>-estable.otf (salida de 10_estabilizar.py)
      --forzar: reemplaza un <slug>.sfd existente

- Une las piezas superpuestas de los glifos construidos (Remove Overlap).
- Añade puntos en extremos, redondea coordenadas y corrige direcciones.
- Quita las tablas OpenType importadas: la única fuente de verdad de las
  funciones es sources/features.fea, que se aplica al compilar.
- Guarda sources/<slug>.sfd. Si ya existe, no lo toca (puede tener retoques
  manuales) salvo con --forzar.
"""
import sys
from pathlib import Path

import fontforge

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

BASE = C.BASE_OTF


def main():
    if C.SFD.exists() and "--forzar" not in sys.argv:
        sys.exit(f"{C.rel(C.SFD)} ya existe; no lo reemplazo. Usa --forzar si de verdad quieres regenerarlo.")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = Path(args[0]) if args else (C.ESTABLE_OTF if "--estable" in sys.argv else BASE)
    font = fontforge.open(str(src))
    for lookup in list(font.gsub_lookups) + list(font.gpos_lookups):
        font.removeLookup(lookup)
    for g in font.glyphs():
        if len(g.foreground):
            g.removeOverlap()
            g.addExtrema("all")
            g.round()
            g.correctDirection()
    font.familyname = C.FAMILY
    font.fontname = f"{C.FAMILY}-{C.STYLE}"
    font.fullname = f"{C.FAMILY} {C.STYLE}"
    font.version = C.VERSION
    font.save(str(C.SFD))
    print(f"guardado {C.rel(C.SFD)} ({sum(1 for _ in font.glyphs())} glifos)")


if __name__ == "__main__":
    main()

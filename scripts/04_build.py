"""Etapa 9 — Genera OTF, TTF y WOFF2 desde el maestro .sfd.

Uso (con el Python de FontForge):  python pipeline/scripts/ff.py 04_build.py   (o `mise run build`)

- FontForge exporta los contornos (CFF en el OTF, TrueType en el TTF) y el
  kerning que tenga el maestro.
- fontTools fija las métricas verticales de scripts/config.py y compila
  sources/features.fea (sustituciones: liga, tnum, case, ss01).
- ttfautohint aplica hinting al TTF, si está instalado.
- fontTools genera el WOFF2 (requiere el paquete brotli).
La fuente variable se añadirá con fontmake cuando existan dos masters.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import fontforge
from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

OUT = C.FONTS


def finish(path):
    """Métricas verticales y funciones OpenType sobre el archivo exportado."""
    f = TTFont(str(path))
    os2, hhea = f["OS/2"], f["hhea"]
    # Métricas verticales: typo y hhea iguales, sin interlineado extra
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = C.ASCENT, -C.DESCENT, 0
    hhea.ascent, hhea.descent, hhea.lineGap = C.ASCENT, -C.DESCENT, 0
    if os2.version >= 2:
        os2.version = max(os2.version, 4)      # v4: bit de métricas typo
        os2.sxHeight, os2.sCapHeight = C.X_HEIGHT, C.CAP_HEIGHT
    # Estilo Regular: bit 6 encendido; itálica (0) y negrita (5) apagados; bit 7 = usar métricas typo
    os2.fsSelection = (os2.fsSelection & ~0b100001) | (1 << 6) | (1 << 7)
    f["head"].macStyle = 0
    os2.recalcCodePageRanges(f)
    # Versión: la de config.py en head y en el nombre
    f["head"].fontRevision = float(C.VERSION)
    f["name"].removeNames(platformID=1)          # nombres de Mac: obsoletos
    f["name"].setName(f"Version {C.VERSION}", 5, 3, 1, 0x409)
    if C.FEATURES.exists() and C.FEATURES.read_text(encoding="utf-8").strip():
        addOpenTypeFeatures(f, str(C.FEATURES), tables=["GSUB", "GPOS", "name"])
    f.save(str(path))


def main():
    if not C.SFD.exists():
        sys.exit(f"no existe {C.rel(C.SFD)}")
    font = fontforge.open(str(C.SFD))
    if hasattr(font, "os2_version"):
        font.os2_version = max(font.os2_version, 4)   # versión 4: incluye altura de x y de mayúsculas
    OUT.mkdir(exist_ok=True)
    base = OUT / f"{C.FAMILY}-{C.STYLE}"
    otf, ttf = base.with_suffix(".otf"), base.with_suffix(".ttf")
    font.generate(str(otf), flags=("opentype", "round"))
    font.generate(str(ttf), flags=("opentype", "round"))
    for path in (otf, ttf):
        finish(path)
    print(f"generados: {otf.name}, {ttf.name}")

    if shutil.which("ttfautohint"):
        hinted = ttf.with_name(ttf.stem + "-hinted.ttf")
        subprocess.run(["ttfautohint", str(ttf), str(hinted)], check=True)
        hinted.replace(ttf)
        print("hinting: ttfautohint aplicado")
    else:
        print("hinting: ttfautohint no está instalado (opcional)")

    try:
        f = TTFont(str(ttf))
        f.flavor = "woff2"
        f.save(str(base.with_suffix(".woff2")))
        print(f"generado: {base.name}.woff2")
    except Exception as e:  # sin brotli
        print(f"WOFF2 no generado ({e}); instala fonttools y brotli")


if __name__ == "__main__":
    main()

"""Etapa 9 — PDF de pruebas de lectura con drawbot-skia.

Uso:  python pipeline/scripts/05_pruebas.py   →  proofs/pruebas.pdf

Páginas: set de glifos, cadenas de espaciado (método de Tracy), pares de
kerning críticos y texto corrido en cascada de tamaños. Imprime al 100 % y
revisa también de cabeza, en espejo y entrecerrando los ojos.
"""
import sys
from pathlib import Path

from drawbot_skia.drawbot import fill, font, newPage, saveImage, text

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

FONT = C.FONT_OTF
W, H, M = 612, 792, 48   # carta en puntos

GLIFOS = ["ABCDEFGHIJKLMN", "OPQRSTUVWXYZ", "abcdefghijklmn", "opqrstuvwxyz",
          "0123456789", "áéíóúüñ ÁÉÍÓÚÜÑ", ".,:;¡!¿?-–—()‘’“”«»&@#$%/*"]
ESPACIADO = ["HHOHHOOHOO", "HHAHHBHHCHHDHHEHHFHHG", "nnonnoonoo",
             "nnanbncndnenfngnhninjn", "oooaobocodoeofogohoi", "0010203040506070809"]
KERNING = ["AV AT AY LT LY To Ta Ty Te Vo Va Ya Yo", "r. r, y. f) ¿A ¡T «A “A",
           "FA PA P. F. AVA TAT LYT", "ñandú pingüino ¿Qué? ¡Vaya! «Tú»"]
TEXTO = C.TEXTO_PRUEBAS


def header(title):
    font(str(FONT), 9)   # la propia fuente: Helvetica no existe en Linux ni en todos los Windows
    fill(0.5)
    text(f"{C.FAMILY} {C.STYLE} v{C.VERSION} · {title}", (M, H - M + 20))
    fill(0)


def page_lines(title, lines, size, leading=1.5):
    newPage(W, H)
    header(title)
    y = H - M - size
    for line in lines:
        font(str(FONT), size)
        text(line, (M, y))
        y -= size * leading


def cascade():
    newPage(W, H)
    header("cascada de tamaños")
    y = H - M - 12
    for size in [8, 10, 12, 14, 18, 24, 36, 48, 72]:
        font(str(FONT), size)
        text(TEXTO[: int(1100 / size)], (M, y))
        y -= size * 1.6 + 6


def main():
    if not FONT.exists():
        sys.exit(f"no existe {C.rel(FONT)}; corre primero 04_build.py")
    page_lines("set de glifos", GLIFOS, 40)
    page_lines("espaciado (Tracy)", ESPACIADO, 30)
    page_lines("pares de kerning", KERNING, 30)
    cascade()
    out = C.PROOFS / "pruebas.pdf"
    out.parent.mkdir(exist_ok=True)
    saveImage(str(out))
    print(f"pruebas: {C.rel(out)}")


if __name__ == "__main__":
    main()

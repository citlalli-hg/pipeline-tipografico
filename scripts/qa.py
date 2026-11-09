"""Etapa 9 — Revisión técnica con Font Bakery.

Uso:  python pipeline/scripts/qa.py   (o `mise run qa`)  →  proofs/fontbakery.md
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402


def main():
    ttf = C.FONTS / f"{C.FAMILY}-{C.STYLE}.ttf"
    if not ttf.exists():
        sys.exit(f"no existe {C.rel(ttf)}; corre primero `mise run build`")
    exe = shutil.which("fontbakery")
    cmd = [exe] if exe else [sys.executable, "-m", "fontbakery"]
    C.PROOFS.mkdir(exist_ok=True)
    out = C.PROOFS / "fontbakery.md"
    sys.exit(subprocess.call(cmd + ["check-universal", str(ttf), "--ghmarkdown", str(out)], cwd=C.ROOT))


if __name__ == "__main__":
    main()

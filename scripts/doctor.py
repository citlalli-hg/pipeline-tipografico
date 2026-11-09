"""Verifica que el equipo tenga todo lo necesario para el pipeline.

Uso:  python pipeline/scripts/doctor.py   (o `mise run doctor`)
"""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

ROOT = C.ROOT

ok = True


def check(label, passed, hint=""):
    global ok
    mark = "OK " if passed else "FALTA"
    print(f"[{mark}] {label}" + ("" if passed else f"  → {hint}"))
    ok = ok and passed


check("git", shutil.which("git"), "winget install --id Git.Git -e")
check("GitHub CLI (gh)", shutil.which("gh"), "winget install --id GitHub.cli -e")
check("Python >= 3.10", sys.version_info >= (3, 10), "mise install")
for mod, pkg in [("cv2", "opencv-python-headless"), ("numpy", "numpy"),
                 ("fontTools", "fonttools"), ("drawbot_skia", "drawbot-skia")]:
    check(f"módulo {pkg}", importlib.util.find_spec(mod), "mise run setup")
check("Potrace", shutil.which("potrace"), "ver README › Instalación")
print(f"[{'OK ' if shutil.which('ttfautohint') else 'opcional'}] ttfautohint (hinting del TTF)")
check("fontTools para FontForge (.ffdeps)", (ROOT / ".ffdeps" / "fontTools").is_dir(), "mise run setup")

try:
    import ff
    cmd = ff.interpreter()
    probe = subprocess.run(cmd[:1] + (["-c", "import fontforge; print(fontforge.version())"]
                                      if len(cmd) == 1 else ["-lang=py", "-c",
                                      "import fontforge; print(fontforge.version())"]),
                           capture_output=True, text=True, timeout=60)
    check(f"FontForge ({cmd[0]})", probe.returncode == 0,
          "winget install --id FontForge.FontForge -e")
except SystemExit as e:
    check("FontForge", False, str(e))

check("proyecto.py en la raíz del proyecto", (ROOT / "proyecto.py").is_file(),
      "corre los comandos desde la carpeta de la fuente, no desde pipeline/")
check("submódulo pipeline/ descargado", (ROOT / "pipeline" / "scripts" / "config.py").is_file(),
      "git submodule update --init")
print(f"\nProyecto: {C.FAMILY} ({ROOT})")
print("\nTodo listo." if ok else "\nInstala lo que falta y vuelve a correr `mise run doctor`.")
sys.exit(0 if ok else 1)

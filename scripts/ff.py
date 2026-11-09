"""Ejecuta un script del pipeline con el Python que trae FontForge.

Uso:  python pipeline/scripts/ff.py 02_importar.py [argumentos...]

Busca, en este orden:
  1. La variable de entorno FONTFORGE_PYTHON (ruta a ffpython o similar).
  2. El Python actual, si ya puede `import fontforge` (Linux con python3-fontforge).
  3. ffpython en el PATH o en la instalación estándar de Windows.
  4. `fontforge -lang=py -script` (macOS y Linux).
Añade .ffdeps/ (fontTools instalado por `mise run setup`) al PYTHONPATH.
El script corre con la raíz del proyecto (la carpeta que contiene a
pipeline/) como directorio de trabajo y en la variable TIPO_PROYECTO.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import config as C  # noqa: E402

ROOT = C.ROOT

WINDOWS_CANDIDATES = [
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "FontForge" / "bin" / "ffpython.exe",
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "FontForgeBuilds" / "bin" / "ffpython.exe",
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "FontForgeBuilds" / "bin" / "ffpython.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "FontForge" / "bin" / "ffpython.exe",
]
MAC_CANDIDATE = Path("/Applications/FontForge.app/Contents/Resources/opt/local/bin/fontforge")


def interpreter():
    env = os.environ.get("FONTFORGE_PYTHON")
    if env:
        return [env]
    if importlib.util.find_spec("fontforge"):
        return [sys.executable]
    found = shutil.which("ffpython")
    if found:
        return [found]
    for path in WINDOWS_CANDIDATES:
        if path.is_file():
            return [str(path)]
    ff = shutil.which("fontforge") or (str(MAC_CANDIDATE) if MAC_CANDIDATE.is_file() else None)
    if ff:
        return [ff, "-lang=py", "-script"]
    sys.exit("No encontré FontForge. Instálalo o define FONTFORGE_PYTHON con la ruta a ffpython.")


def main():
    if len(sys.argv) < 2:
        sys.exit("uso: python pipeline/scripts/ff.py <script.py> [argumentos]")
    script = SCRIPTS / sys.argv[1]
    env = dict(os.environ)
    deps = ROOT / ".ffdeps"
    if deps.is_dir():
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(deps), env.get("PYTHONPATH")]))
    # El Python de FontForge no debe heredar el entorno virtual del proyecto
    env.pop("PYTHONHOME", None)
    env["TIPO_PROYECTO"] = str(ROOT)
    cmd = interpreter() + [str(script)] + sys.argv[2:]
    sys.exit(subprocess.call(cmd, cwd=ROOT, env=env))


if __name__ == "__main__":
    main()

"""Crea un proyecto tipográfico nuevo que usa este pipeline.

Uso (desde cualquier carpeta, con el pipeline clonado o como submódulo de otro proyecto):
    python pipeline/scripts/nuevo_proyecto.py "Nombre" [--destino CARPETA] [--github]

- Copia plantilla-proyecto/ en CARPETA/<slug> (por defecto, junto al proyecto actual)
  y pone el nombre de la familia en proyecto.py, README.md, CLAUDE.md y el brief.
- Inicia Git y agrega el pipeline común como submódulo en pipeline/.
- Con --github crea el repositorio privado citlalli-hg/<slug> con GitHub CLI y sube main.

Después: llena proyecto.py y brief/brief.md, y sigue con `mise run doctor`.
"""
import argparse
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent.parent
PLANTILLA = PIPELINE / "plantilla-proyecto"
REMOTO = "https://github.com/citlalli-hg/pipeline-tipografico.git"
OWNER = "citlalli-hg"


def slugify(nombre):
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def run(cmd, cwd):
    print("  $", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("nombre", help="nombre de la familia, p. ej. Sterna")
    ap.add_argument("--destino", type=Path, default=None, help="carpeta donde crear el proyecto")
    ap.add_argument("--github", action="store_true", help="crear el repo privado en GitHub y subirlo")
    a = ap.parse_args()

    slug = slugify(a.nombre)
    base = a.destino or (PIPELINE.parent.parent if (PIPELINE.parent / "proyecto.py").exists() else PIPELINE.parent)
    dest = base / slug
    if dest.exists():
        sys.exit(f"{dest} ya existe")
    shutil.copytree(PLANTILLA, dest)
    for p in dest.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".md", ".toml", ".yml"}:
            t = p.read_text(encoding="utf-8")
            if "{{" in t:
                p.write_text(t.replace("{{FAMILIA}}", a.nombre).replace("{{SLUG}}", slug), encoding="utf-8")
    print(f"proyecto creado en {dest}")

    run(["git", "init", "-q", "-b", "main"], dest)
    run(["git", "submodule", "add", REMOTO, "pipeline"], dest)
    run(["git", "add", "-A"], dest)
    run(["git", "commit", "-q", "-m", f"{a.nombre}: proyecto creado con el pipeline común"], dest)
    if a.github:
        run(["gh", "repo", "create", f"{OWNER}/{slug}", "--private", "--source", ".", "--push",
             "--description", f"Fuente tipográfica {a.nombre} — Citlallihg"], dest)
    print("\nSiguiente: llena proyecto.py y brief/brief.md; luego `mise trust && mise install && mise run setup`.")


if __name__ == "__main__":
    main()

"""Construcciones propias del proyecto (opcional).

La llama `pipeline/scripts/06_completar_set.py` (`mise run completar`) después
de copiar FUENTE_BASE y corregir su línea base. Borra este archivo si la fuente
no necesita construcciones: el pipeline funciona sin él.

`f` tiene: f.get(nombre), f.add(nombre, contornos, adv=, uni=, note=, fit=),
f.ink(nombre), f.center_x(nombre), f.glyphs, f.adv, f.cmap, f.notas (reporte).
Utilidades de contornos: pipeline/scripts/contornos.py.
"""
from contornos import bounds, move  # noqa: F401


def construir(f):
    # Ejemplo: espacio de no separación igual al espacio
    # f.add("uni00A0", [], adv=f.adv["space"], uni=0x00A0, note="espacio de no separación", fit=False)
    return None   # o el texto de sources/features.fea

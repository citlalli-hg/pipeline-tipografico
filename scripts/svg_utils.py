"""Dibuja los contornos de un SVG en una pluma de fontTools aplicando las
transformaciones de cada grupo (Potrace y Affinity las usan; el SVGPath de
fontTools las ignora)."""
import re
import xml.etree.ElementTree as ET

from fontTools.misc.transform import Identity, Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path.parser import parse_path

_FUNC = re.compile(r"(matrix|translate|scale|rotate)\s*\(([^)]*)\)")


def parse_transform(value):
    t = Identity
    for name, args in _FUNC.findall(value or ""):
        n = [float(v) for v in re.split(r"[\s,]+", args.strip()) if v]
        if name == "matrix":
            t = t.transform(n)
        elif name == "translate":
            t = t.translate(n[0], n[1] if len(n) > 1 else 0)
        elif name == "scale":
            t = t.scale(n[0], n[1] if len(n) > 1 else n[0])
        elif name == "rotate":
            import math
            t = t.rotate(math.radians(n[0]))
    return t


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _walk(el, transform, pen):
    t = transform.transform(parse_transform(el.get("transform")))
    if _local(el.tag) == "path" and el.get("d"):
        parse_path(el.get("d"), TransformPen(pen, t))
    for child in el:
        if _local(child.tag) not in {"defs", "clipPath", "mask", "title", "desc"}:
            _walk(child, t, pen)


def draw_svg(path, pen, transform=Identity):
    """Dibuja `path` en `pen`; `transform` va de coordenadas SVG a unidades de fuente."""
    root = ET.parse(str(path)).getroot()
    _walk(root, Transform(*transform), pen)

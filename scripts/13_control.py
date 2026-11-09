"""Control de calidad de contornos y SVG: nada abierto, nada roto.

Uso:  python pipeline/scripts/13_control.py [FUENTE.otf] [--estricto]   (o `mise run control`)
      FUENTE: por defecto fonts/<Familia>-Regular.otf o sources/<slug>-estable.otf
Salida: proofs/control.md. Con --estricto termina con error si hay fallas
        graves: contornos abiertos o SVG rotos (lo usa GitHub Actions para no
        publicar una fuente rota). Contornos degenerados o sin área son avisos.

Revisa:
  Fuente   cada contorno cerrado; sin contornos degenerados (menos de 3 puntos
           o área casi nula); sin puntos repetidos seguidos; dirección de los
           contornos exteriores coherente.
  Hojas    hojas/*.svg y glyphs-svg/*.svg: XML válido; cada subtrazo relleno
           cerrado con Z; sin imágenes incrustadas; marcas de registro presentes
           (hojas); un grupo por glifo del manifiesto; sin trazos oscuros sin
           relleno (dibujo con línea que no se importaría).

Solo requiere fontTools: funciona en Windows, macOS y Linux.
"""
import importlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

H = importlib.import_module("11_hojas")
AREA_MIN = 4.0          # unidades²: menos que esto es un contorno degenerado


def _area(pts):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])) / 2


def control_fuente(path):
    t = TTFont(str(path))
    gs = t.getGlyphSet()
    errores, avisos = [], []
    for n in t.getGlyphOrder():
        rec = RecordingPen()
        gs[n].draw(rec)
        pts, abierto = [], False
        areas = []
        for op, args in rec.value:
            if op == "moveTo":
                if pts:
                    errores.append(f"`{n}`: contorno sin cerrar")
                pts = [args[0]]
            elif op in ("lineTo", "curveTo", "qCurveTo"):
                if args and pts and tuple(args[-1]) == tuple(pts[-1]):
                    avisos.append(f"`{n}`: punto repetido en ({args[-1][0]:.0f}, {args[-1][1]:.0f})")
                pts += list(args)
            elif op == "closePath":
                if len(pts) < 3:
                    avisos.append(f"`{n}`: contorno degenerado ({len(pts)} puntos); bórralo en FontForge")
                else:
                    a = _area(pts)
                    if abs(a) < AREA_MIN:
                        avisos.append(f"`{n}`: contorno sin área; bórralo en FontForge")
                    areas.append(a)
                pts = []
            elif op == "endPath":
                abierto = True
                pts = []
        if pts or abierto:
            errores.append(f"`{n}`: contorno abierto")
        if areas:
            mayor = max(areas, key=abs)
            # CFF: exteriores en sentido antihorario (área positiva)
            if mayor < 0 and t.has_key("CFF "):
                avisos.append(f"`{n}`: el contorno exterior va en sentido horario")
    return errores, avisos, len(t.getGlyphOrder())


_SUBPATH = re.compile(r"[Mm][^Mm]*")


def control_svg(path, es_hoja):
    errores, avisos = [], []
    try:
        root = ET.parse(str(path)).getroot()
    except ET.ParseError as e:
        return [f"{path.name}: XML inválido ({e})"], []
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "image":
            errores.append(f"{path.name}: tiene una imagen incrustada; exporta con Rasterise: Nothing")
        if tag == "path":
            st = H._style(el, {"fill": "#000"})
            if st.get("fill") in ("none", "transparent"):
                continue
            for sub in _SUBPATH.findall(el.get("d") or ""):
                if not re.search(r"[Zz]\s*$", sub.strip()):
                    gid = el.get("id") or (el.get("class") or "")
                    errores.append(f"{path.name}: subtrazo relleno sin cerrar (Z) {gid}".strip())
                    break
    H.AVISOS.clear()
    shapes = H.leer_svg(path)
    avisos += list(dict.fromkeys(H.AVISOS))
    if es_hoja:
        ids = {el.get("id") for el in root.iter() if el.get("id")}
        if not any("registro" in (i or "") for i in ids):
            errores.append(f"{path.name}: faltan las marcas de registro")
        try:
            man = H._manifiesto_de(path)
        except FileNotFoundError:
            man = None
        fam = H.familia_de(path)
        if fam is None:
            errores.append(f"{path.name}: el nombre no corresponde a ninguna hoja")
        if fam and man:
            esperados = man["familias"].get(fam, {})
            faltan = [g for g in esperados if g not in ids]
            if faltan:
                errores.append(f"{path.name}: faltan los grupos de {', '.join(faltan)}")
    return errores, avisos, len(shapes)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    default = C.FONTS / f"{C.FAMILY}-{C.STYLE}.otf"
    src = Path(args[0]) if args else (default if default.exists() else C.ESTABLE_OTF)
    man = C.ROOT / "hojas" / "manifiesto.json"
    if man.exists():
        H._cargar_extras(json.loads(man.read_text(encoding="utf-8")))

    lines = [f"# Control de calidad de {C.FAMILY}", ""]
    total_err = 0
    if src.exists():
        e, a, n = control_fuente(src)
        total_err += len(e)
        lines += [f"## Fuente `{C.rel(src)}`", "", f"{n} glifos · {len(e)} errores · {len(a)} avisos", ""]
        lines += [f"- ERROR {x}" for x in e] + [f"- aviso {x}" for x in a[:60]]
        if len(a) > 60:
            lines.append(f"- … y {len(a) - 60} avisos más")
        lines.append("")
    for carpeta, es_hoja in ((C.ROOT / "hojas", True), (C.ROOT / "hojas" / "semilla", True),
                             (C.ROOT / "template" / "semilla", True), (C.ROOT / "glyphs-svg", False)):
        svgs = sorted(carpeta.glob("*.svg")) if carpeta.is_dir() else []
        if not svgs:
            continue
        lines += [f"## `{C.rel(carpeta)}/` ({len(svgs)} SVG)", "", "| Archivo | Contornos | Errores | Avisos |",
                  "| --- | --- | --- | --- |"]
        detalle = []
        for p in svgs:
            e, a, n = control_svg(p, es_hoja)
            total_err += len(e)
            lines.append(f"| {p.name} | {n} | {len(e)} | {len(a)} |")
            detalle += [f"- ERROR {x}" for x in e] + [f"- aviso {x}" for x in a]
        lines += [""] + detalle + [""]
    lines.insert(2, f"**{'Sin errores' if not total_err else f'{total_err} errores'}.** Contornos cerrados, "
                    "sin degenerados; SVG válidos, cerrados y con marcas de registro.\n" if not total_err else
                    f"**{total_err} errores.** Revisa la lista.\n")
    C.PROOFS.mkdir(exist_ok=True)
    (C.PROOFS / "control.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"control: {total_err} errores → {C.rel(C.PROOFS / 'control.md')}")
    if total_err and "--estricto" in sys.argv:
        sys.exit(1)


if __name__ == "__main__":
    main()

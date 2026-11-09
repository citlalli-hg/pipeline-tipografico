"""Etapa 2 — Digitaliza las hojas escaneadas y recorta un archivo por glifo.

Uso:  python pipeline/scripts/01_digitalizar.py [scans/hoja-01.png ...]
      (sin argumentos procesa todos los PNG/JPG/TIF de scans/ en orden)

Las hojas deben llamarse en orden (hoja-01, hoja-02...) porque la hoja N
contiene los glifos de la plantilla N. Escanea a 600 dpi en escala de grises.

Salida por glifo en glyphs-png/:  <nombre>.png (para revisar) y <nombre>.pbm
(entrada de Potrace). También genera proofs/hoja-contacto.png.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

INK_THRESHOLD = 140   # más bajo = solo tinta muy oscura; sube si se pierden trazos finos


def find_markers(gray):
    """Devuelve los centros de las 4 marcas de registro: sup-izq, sup-der, inf-izq, inf-der."""
    h, w = gray.shape
    _, binv = cv2.threshold(cv2.GaussianBlur(gray, (5, 5), 0), 0, 255,
                            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    expected = (C.MARKER_MM * w / C.PAGE_W_MM) ** 2
    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        if not (0.3 * expected < area < 3 * expected):
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        if 0.75 < bw / bh < 1.33 and area / (bw * bh) > 0.85:
            candidates.append((x + bw / 2, y + bh / 2))
    if len(candidates) < 4:
        raise RuntimeError("no encontré las 4 marcas de registro; revisa que la hoja esté completa")
    corners = [(0, 0), (w, 0), (0, h), (w, h)]
    return np.float32([min(candidates, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
                       for cx, cy in corners])


def rectify(gray):
    """Endereza la hoja y la lleva a la resolución nominal de la plantilla."""
    src = find_markers(gray)
    m, s, k = C.MARGIN_MM, C.MARKER_MM, C.PX_PER_MM
    W, H = C.PAGE_W_MM, C.PAGE_H_MM
    dst = np.float32([[(m + s / 2) * k, (m + s / 2) * k],
                      [(W - m - s / 2) * k, (m + s / 2) * k],
                      [(m + s / 2) * k, (H - m - s / 2) * k],
                      [(W - m - s / 2) * k, (H - m - s / 2) * k]])
    size = (round(W * k), round(H * k))
    return cv2.warpPerspective(gray, cv2.getPerspectiveTransform(src, dst), size,
                               borderValue=255)


def clean(crop):
    """Blanco y negro puro, sin guías ni manchas pequeñas."""
    _, bw = cv2.threshold(crop, INK_THRESHOLD, 255, cv2.THRESH_BINARY)
    inv = 255 - bw
    n, labels, stats, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)
    min_area = (0.4 * C.PX_PER_MM) ** 2          # manchas de menos de ~0.4 mm
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < min_area:
            inv[labels == i] = 0
    return 255 - inv


def process_page(path, names, outdir):
    gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise RuntimeError(f"no pude leer {path}")
    page = rectify(gray)
    k = C.PX_PER_MM
    pad = round(0.6 * k)   # recorta 0.6 mm hacia dentro para no arrastrar el marco
    crops = []
    for slot, name in enumerate(names):
        x, y, w, h = C.cell_box_mm(slot)
        x0, y0, x1, y1 = round(x * k), round(y * k), round((x + w) * k), round((y + h) * k)
        crop = page[y0:y1, x0:x1].copy()
        crop[:pad, :] = 255
        crop[-pad:, :] = 255
        crop[:, :pad] = 255
        crop[:, -pad:] = 255
        glyph = clean(crop)
        stem = C.file_stem(name)
        cv2.imwrite(str(outdir / f"{stem}.png"), glyph)
        cv2.imwrite(str(outdir / f"{stem}.pbm"), glyph)
        empty = int((glyph < 128).sum()) == 0
        crops.append((name, glyph, empty))
    return crops


def contact_sheet(crops, path):
    thumb_h = 120
    tiles = []
    for name, img, empty in crops:
        scale = thumb_h / img.shape[0]
        t = cv2.resize(img, (round(img.shape[1] * scale), thumb_h), interpolation=cv2.INTER_AREA)
        t = cv2.cvtColor(t, cv2.COLOR_GRAY2BGR)
        cv2.rectangle(t, (0, 0), (t.shape[1] - 1, t.shape[0] - 1),
                      (0, 0, 255) if empty else (200, 200, 200), 2)
        cv2.putText(t, name, (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1)
        tiles.append(t)
    per_row = 8
    w = max(t.shape[1] for t in tiles)
    rows = []
    for i in range(0, len(tiles), per_row):
        row = [cv2.copyMakeBorder(t, 4, 4, 4, 4 + w - t.shape[1], cv2.BORDER_CONSTANT,
                                  value=(255, 255, 255)) for t in tiles[i:i + per_row]]
        while len(row) < per_row:
            row.append(np.full_like(row[0], 255))
        rows.append(np.hstack(row))
    cv2.imwrite(str(path), np.vstack(rows))


def main():
    args = [Path(a) for a in sys.argv[1:]]
    scans = args or sorted(p for p in (C.ROOT / "scans").iterdir()
                           if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"})
    if not scans:
        sys.exit("no hay escaneos en scans/")
    outdir = C.ROOT / "glyphs-png"
    outdir.mkdir(exist_ok=True)
    per = C.per_page()
    all_crops = []
    for i, path in enumerate(scans):
        names = C.DRAWN[i * per:(i + 1) * per]
        crops = process_page(path, names, outdir)
        missing = [n for n, _, e in crops if e]
        print(f"{path.name}: {len(crops)} glifos" + (f", vacíos: {' '.join(missing)}" if missing else ""))
        all_crops += crops
    (C.ROOT / "proofs").mkdir(exist_ok=True)
    contact_sheet(all_crops, C.ROOT / "proofs" / "hoja-contacto.png")
    print("hoja de contacto: proofs/hoja-contacto.png (marco rojo = celda vacía)")


if __name__ == "__main__":
    main()

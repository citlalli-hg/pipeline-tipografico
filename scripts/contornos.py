"""Utilidades de contornos compartidas por los scripts y por proyecto/completar.py.

Un contorno es una lista de operaciones de RecordingPen: (op, puntos).
Los ayudantes de trazo (line, slant, arc, disk, ring, rect) usan un grosor
`w` explícito; el valor por defecto W solo existe por compatibilidad.
"""
import math

W = 62                   # grosor por defecto de los ayudantes de trazo
K = 0.5522847498         # constante para aproximar un cuarto de círculo con una curva


def contours_of(rec):
    out, cur = [], []
    for op, args in rec:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            out.append(cur)
            cur = []
    return out


def transform(cs, a=1, b=0, c=0, d=1, dx=0, dy=0):
    def tp(p):
        x, y = p
        return (a * x + c * y + dx, b * x + d * y + dy)
    flip = a * d - b * c < 0
    out = []
    for ctr in cs:
        new = [(op, tuple(tp(p) for p in args)) for op, args in ctr]
        out.append(reverse(new) if flip else new)
    return out


def move(cs, dx=0, dy=0):
    return transform(cs, dx=dx, dy=dy)


def reverse(ctr):
    """Invierte la dirección de un contorno (necesario tras un espejo)."""
    start = ctr[0][1][0]
    segs, cur = [], start
    for op, args in ctr[1:]:
        if op in ("closePath", "endPath"):
            break
        segs.append((op, cur, args))
        cur = args[-1]
    out = [("moveTo", (cur,))]
    for op, p0, args in reversed(segs):
        if op == "lineTo":
            out.append(("lineTo", (p0,)))
        elif op == "curveTo":
            c1, c2, _ = args
            out.append(("curveTo", (c2, c1, p0)))
        elif op == "qCurveTo":
            out.append(("qCurveTo", tuple(reversed(args[:-1])) + (p0,)))
    out.append(("closePath", ()))
    return out


def bounds(cs):
    xs, ys = [], []
    for ctr in cs:
        for _, args in ctr:
            for x, y in args:
                xs.append(x)
                ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def polygon(pts):
    """Contorno cerrado de segmentos rectos, en sentido antihorario (exterior)."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts = list(reversed(pts))
    return [("moveTo", (pts[0],))] + [("lineTo", (p,)) for p in pts[1:]] + [("closePath", ())]


def rect(x0, y0, x1, y1):
    return polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def line(p0, p1, w=W):
    """Trazo recto de grosor w con cortes perpendiculares."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L * w / 2, (x1 - x0) / L * w / 2
    return polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])


def slant(xb, xt, y0, y1, w=W):
    """Trazo diagonal con cortes horizontales (como las astas de A, V, W de Elalba).
    xb, xt: centro del trazo abajo y arriba."""
    hw = w / math.sin(math.atan2(y1 - y0, abs(xt - xb))) / 2
    return polygon([(xb - hw, y0), (xb + hw, y0), (xt + hw, y1), (xt - hw, y1)])


def _arc_pts(cx, cy, r, a0, a1):
    """Curvas Bézier que aproximan un arco (ángulos en grados, a0 -> a1)."""
    n = max(1, math.ceil(abs(a1 - a0) / 90))
    step = math.radians((a1 - a0) / n)
    k = 4 / 3 * math.tan(step / 4)
    segs, a = [], math.radians(a0)
    for _ in range(n):
        b = a + step
        p0 = (cx + r * math.cos(a), cy + r * math.sin(a))
        p3 = (cx + r * math.cos(b), cy + r * math.sin(b))
        c1 = (p0[0] - k * r * math.sin(a), p0[1] + k * r * math.cos(a))
        c2 = (p3[0] + k * r * math.sin(b), p3[1] - k * r * math.cos(b))
        segs.append((c1, c2, p3))
        a = b
    return segs


def arc(cx, cy, r, a0, a1, w=W):
    """Trazo curvo: anillo parcial de radio medio r entre los ángulos a0 y a1."""
    ro, ri = r + w / 2, r - w / 2
    lo, hi = min(a0, a1), max(a0, a1)
    outer = _arc_pts(cx, cy, ro, lo, hi)
    inner = _arc_pts(cx, cy, ri, hi, lo)
    start = (cx + ro * math.cos(math.radians(lo)), cy + ro * math.sin(math.radians(lo)))
    ctr = [("moveTo", (start,))]
    ctr += [("curveTo", s) for s in outer]
    p = (cx + ri * math.cos(math.radians(hi)), cy + ri * math.sin(math.radians(hi)))
    ctr.append(("lineTo", (p,)))
    ctr += [("curveTo", s) for s in inner]
    ctr.append(("closePath", ()))
    return ctr


def disk(cx, cy, r):
    segs = _arc_pts(cx, cy, r, 0, 360)
    return [("moveTo", ((cx + r, cy),))] + [("curveTo", s) for s in segs] + [("closePath", ())]


def ring(cx, cy, r, w=W):
    outer = disk(cx, cy, r + w / 2)
    inner = reverse(disk(cx, cy, r - w / 2))
    return [outer, inner]



def above(cs, y):
    """Contornos que están por encima de y (acentos). Se compara con margen
    porque los puntos de control de una curva pueden bajar un poco."""
    return [c for c in cs if bounds([c])[1] >= y - 40 and bounds([c])[3] > y + 40]


def below(cs, y):
    return [c for c in cs if bounds([c])[3] < y]


def accent_on(f, base, accent_cs, extra=()):
    """Base + acento centrado sobre la tinta de la base."""
    ax0, _, ax1, _ = bounds(accent_cs)
    dx = f.center_x(base) - (ax0 + ax1) / 2
    return f.get(base) + move(accent_cs, dx=dx) + list(extra)



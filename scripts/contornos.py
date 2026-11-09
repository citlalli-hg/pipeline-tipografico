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




# --- Recortes y transformaciones para construir glifos con partes de otros ----------

def rotate(cs, deg, cx=0, cy=0):
    """Gira los contornos `deg` grados (antihorario) alrededor de (cx, cy)."""
    r = math.radians(deg)
    co, si = math.cos(r), math.sin(r)
    moved = transform(cs, dx=-cx, dy=-cy)
    return transform(moved, a=co, b=si, c=-si, d=co, dx=cx, dy=cy)


def scale(cs, sx, sy=None, cx=0, cy=0):
    """Escala alrededor de (cx, cy). Ojo: escalar cambia los grosores; para
    conservar el trazo, recorta y desplaza partes en vez de escalar."""
    sy = sx if sy is None else sy
    return transform(move(cs, dx=-cx, dy=-cy), a=sx, d=sy, dx=cx, dy=cy)


def mirror_x(cs, axis=None):
    """Espejo horizontal sobre la vertical x = axis (por defecto, el centro de la tinta)."""
    if axis is None:
        x0, _, x1, _ = bounds(cs)
        axis = (x0 + x1) / 2
    return transform(cs, a=-1, dx=2 * axis)


def _segments(ctr):
    """Contorno → lista de segmentos [p0, ..., pN] (2 puntos = recta, 4 = cúbica)."""
    segs, cur, start = [], None, None
    for op, args in ctr:
        if op == "moveTo":
            cur = start = args[0]
        elif op == "lineTo":
            segs.append([cur, args[0]])
            cur = args[0]
        elif op == "curveTo":
            segs.append([cur, *args])
            cur = args[-1]
        elif op == "qCurveTo":
            # cuadrática → cúbica (solo el caso de un punto de control)
            q = args[0]
            p3 = args[-1]
            c1 = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
            c2 = (p3[0] + 2 / 3 * (q[0] - p3[0]), p3[1] + 2 / 3 * (q[1] - p3[1]))
            segs.append([cur, c1, c2, p3])
            cur = p3
        elif op in ("closePath", "endPath"):
            if cur != start:
                segs.append([cur, start])
    return segs


def _split(seg, f):
    """Parte un segmento donde f(punto) = 0 (f lineal)."""
    from fontTools.misc.bezierTools import solveCubic, splitCubicAtT
    if len(seg) == 2:
        a, b = f(seg[0]), f(seg[1])
        if (a < 0 < b or b < 0 < a):
            t = a / (a - b)
            p = (seg[0][0] + t * (seg[1][0] - seg[0][0]), seg[0][1] + t * (seg[1][1] - seg[0][1]))
            return [[seg[0], p], [p, seg[1]]]
        return [seg]
    v = [f(p) for p in seg]
    # f(B(t)) como polinomio cúbico en t
    a = -v[0] + 3 * v[1] - 3 * v[2] + v[3]
    b = 3 * v[0] - 6 * v[1] + 3 * v[2]
    c = -3 * v[0] + 3 * v[1]
    d = v[0]
    ts = sorted(t for t in solveCubic(a, b, c, d) if 1e-6 < t < 1 - 1e-6) if abs(a) > 1e-12 else None
    if ts is None:
        from fontTools.misc.bezierTools import solveQuadratic
        ts = sorted(t for t in solveQuadratic(b, c, d) if 1e-6 < t < 1 - 1e-6)
    if not ts:
        return [seg]
    parts = splitCubicAtT(*seg, *ts)
    return [list(p) for p in parts]


def recortar(cs, a, b, c):
    """Conserva la parte de los contornos donde a·x + b·y + c >= 0 y cierra el
    corte con una recta. Sirve para tomar partes de un glifo (el asta de una l,
    las panzas de una B, la parte alta de una S...). Los puentes que quedan
    sobre la línea de corte no tienen área; FontForge los limpia con
    Remove Overlap (07_a_sfd.py)."""
    def f(p):
        return a * p[0] + b * p[1] + c

    out = []
    for ctr in cs:
        segs = []
        for s in _segments(ctr):
            segs += _split(s, f)
        if not segs:
            continue

        def inside(s):
            if len(s) == 2:
                m = ((s[0][0] + s[1][0]) / 2, (s[0][1] + s[1][1]) / 2)
            else:
                from fontTools.misc.bezierTools import splitCubicAtT
                m = splitCubicAtT(*s, 0.5)[0][-1]
            return f(m) >= -1e-9

        flags = [inside(s) for s in segs]
        if all(flags):
            out.append(ctr)
            continue
        if not any(flags):
            continue
        k = flags.index(False)            # empieza después de un tramo fuera
        order = segs[k:] + segs[:k]
        oflags = flags[k:] + flags[:k]
        new, last = [], None
        for s, ok in zip(order, oflags):
            if not ok:
                continue
            if last is None:
                new.append(("moveTo", (s[0],)))
            elif last != s[0]:
                new.append(("lineTo", (s[0],)))
            new.append(("lineTo", (s[1],)) if len(s) == 2 else ("curveTo", tuple(s[1:])))
            last = s[-1]
        if new:
            new.append(("closePath", ()))
            out.append(new)
    return out


def recortar_x(cs, x, conservar="izq"):
    """Recorta por la vertical x: conserva la izquierda ('izq') o la derecha ('der')."""
    return recortar(cs, -1, 0, x) if conservar == "izq" else recortar(cs, 1, 0, -x)


def recortar_y(cs, y, conservar="abajo"):
    """Recorta por la horizontal y: conserva abajo ('abajo') o arriba ('arriba')."""
    return recortar(cs, 0, -1, y) if conservar == "abajo" else recortar(cs, 0, 1, -y)


def caja(cs, x0, y0, x1, y1):
    """Conserva solo lo que cae dentro del rectángulo."""
    return recortar_y(recortar_y(recortar_x(recortar_x(cs, x0, "der"), x1, "izq"), y0, "arriba"), y1, "abajo")


def estrechar(cs, x, d):
    """Angosta un glifo `d` unidades sin cambiar sus grosores: quita la franja
    vertical de ancho d centrada en x y junta las dos mitades. El corte debe cruzar solo trazos
    horizontales (arriba y abajo de una O, por ejemplo)."""
    return recortar_x(cs, x - d / 2, "izq") + move(recortar_x(cs, x + d / 2, "der"), dx=-d)


def achatar(cs, y, d):
    """Reduce la altura `d` unidades sin cambiar grosores: quita la franja
    horizontal de alto d centrada en y y junta las dos mitades. El corte debe cruzar solo trazos verticales."""
    return recortar_y(cs, y - d / 2, "abajo") + move(recortar_y(cs, y + d / 2, "arriba"), dy=-d)

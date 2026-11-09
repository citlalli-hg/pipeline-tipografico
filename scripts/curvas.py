"""Calidad de curvas: diagnóstico, puntos en extremos, armonización G2 y peines de curvatura.

Se usa como módulo (06_completar_set.py, 02_importar.py, 11_hojas.py) y desde
12_curvas.py. Solo requiere fontTools: funciona en Windows, macOS y Linux.

Reglas de dibujo que revisa (Scannerlicker, *Bézier OCD*; Glyphs, *Harmonization*;
Design With FontForge):
  - Nodos en los extremos horizontales y verticales, con asas horizontales o verticales.
  - Sin quiebres accidentales: un nodo es liso (asas alineadas) o es esquina clara.
  - Continuidad de curvatura (G2) en los nodos lisos: la curvatura no salta al
    pasar de un segmento al siguiente. Es el criterio de las superficies «clase A»
    del diseño industrial (Autodesk Alias, Rhino), que se revisa con peines de
    curvatura; aquí se usan igual.

Armonizar mueve solo el nodo liso sobre la recta de sus asas, al punto que
iguala la curvatura a ambos lados (algoritmo de Simon Cozens, el mismo de
Green Harmony). La forma cambia muy poco, pero cambia: el pipeline solo lo
aplica a glifos construidos o trazados por máquina, o cuando se pide.
"""
import math

from fontTools.misc.bezierTools import splitCubicAtT, solveQuadratic

# Umbrales (unidades de fuente y grados)
ANG_LISO = 0.6          # asas alineadas: nodo liso
ANG_QUIEBRE = 12        # entre ANG_LISO y esto: quiebre accidental
ANG_HV = 1.0            # asa «horizontal/vertical»
ANG_CASI_HV = 10        # asa casi H/V (probablemente accidental)
G2_TOL = 0.25           # diferencia relativa de curvatura tolerada en un nodo liso
EXTREMO_MIN = 2.0       # un extremo interior cuenta si sobresale al menos esto


# --- Contornos ↔ segmentos ----------------------------------------------------------

def a_segmentos(ctr):
    """Contorno (RecordingPen) → lista de segmentos [p0, p1] o [p0, c1, c2, p3], cerrada."""
    segs, cur, start = [], None, None
    for op, args in ctr:
        if op == "moveTo":
            cur = start = tuple(args[0])
        elif op == "lineTo":
            segs.append([cur, tuple(args[0])])
            cur = tuple(args[0])
        elif op == "curveTo":
            segs.append([cur] + [tuple(p) for p in args])
            cur = tuple(args[-1])
        elif op == "qCurveTo":
            q, p3 = args[0], tuple(args[-1])
            c1 = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
            c2 = (p3[0] + 2 / 3 * (q[0] - p3[0]), p3[1] + 2 / 3 * (q[1] - p3[1]))
            segs.append([cur, c1, c2, p3])
            cur = p3
        elif op in ("closePath", "endPath"):
            if cur is not None and start is not None and math.dist(cur, start) > 1e-6:
                segs.append([cur, start])
    return [s for s in segs if not (len(s) == 2 and math.dist(s[0], s[1]) < 1e-6)]


def a_contorno(segs):
    if not segs:
        return []
    out = [("moveTo", (segs[0][0],))]
    for s in segs:
        out.append(("lineTo", (s[1],)) if len(s) == 2 else ("curveTo", tuple(s[1:])))
    out.append(("closePath", ()))
    return out


# --- Geometría -------------------------------------------------------------------------

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _ang(v):
    return math.degrees(math.atan2(v[1], v[0]))


def _diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def tangente_salida(s):
    """Dirección al inicio del segmento (primer punto distinto de p0)."""
    for p in s[1:]:
        if math.dist(p, s[0]) > 1e-6:
            return _sub(p, s[0])
    return None


def tangente_llegada(s):
    for p in reversed(s[:-1]):
        if math.dist(p, s[-1]) > 1e-6:
            return _sub(s[-1], p)
    return None


def curvatura(s, t):
    """Curvatura con signo de un segmento cúbico en t (0 para rectas)."""
    if len(s) == 2:
        return 0.0
    p0, p1, p2, p3 = s
    mt = 1 - t
    d1 = tuple(3 * mt * mt * (p1[i] - p0[i]) + 6 * mt * t * (p2[i] - p1[i]) + 3 * t * t * (p3[i] - p2[i]) for i in (0, 1))
    d2 = tuple(6 * mt * (p2[i] - 2 * p1[i] + p0[i]) + 6 * t * (p3[i] - 2 * p2[i] + p1[i]) for i in (0, 1))
    n = math.hypot(*d1)
    if n < 1e-9:
        return 0.0
    return (d1[0] * d2[1] - d1[1] * d2[0]) / n ** 3


def punto(s, t):
    if len(s) == 2:
        return (s[0][0] + t * (s[1][0] - s[0][0]), s[0][1] + t * (s[1][1] - s[0][1]))
    mt = 1 - t
    return tuple(mt ** 3 * s[0][i] + 3 * mt * mt * t * s[1][i] + 3 * mt * t * t * s[2][i] + t ** 3 * s[3][i] for i in (0, 1))


def normal(s, t):
    if len(s) == 2:
        d = _sub(s[1], s[0])
    else:
        mt = 1 - t
        d = tuple(3 * mt * mt * (s[1][i] - s[0][i]) + 6 * mt * t * (s[2][i] - s[1][i]) + 3 * t * t * (s[3][i] - s[2][i]) for i in (0, 1))
    n = math.hypot(*d) or 1
    return (-d[1] / n, d[0] / n)


def extremos_interiores(s):
    """t de los extremos en x o y dentro de un segmento cúbico (sin contar los extremos)."""
    if len(s) == 2:
        return []
    ts = []
    for i in (0, 1):
        a = -s[0][i] + 3 * s[1][i] - 3 * s[2][i] + s[3][i]
        b = 2 * (s[0][i] - 2 * s[1][i] + s[2][i])
        c = s[1][i] - s[0][i]
        for t in solveQuadratic(a, b, c):
            if 0.02 < t < 0.98:
                v = punto(s, t)[i]
                if min(abs(v - s[0][i]), abs(v - s[3][i])) >= EXTREMO_MIN:
                    ts.append(t)
    return sorted(set(round(t, 6) for t in ts))


# --- Operaciones ---------------------------------------------------------------------

def agregar_extremos(cs):
    """Parte cada curva en sus extremos horizontales y verticales (como
    Element › Add Extrema). La forma no cambia."""
    out = []
    for ctr in cs:
        segs = []
        for s in a_segmentos(ctr):
            ts = extremos_interiores(s)
            if ts:
                segs += [list(p) for p in splitCubicAtT(*s, *ts)]
            else:
                segs.append(s)
        out.append(a_contorno(segs))
    return out


def _interseccion(a1, a2, b1, b2):
    d1, d2 = _sub(a2, a1), _sub(b2, b1)
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-9:
        return None
    t = ((b1[0] - a1[0]) * d2[1] - (b1[1] - a1[1]) * d2[0]) / den
    return (a1[0] + t * d1[0], a1[1] + t * d1[1])


def _es_liso(a, b):
    ta, tb = tangente_llegada(a), tangente_salida(b)
    return ta is not None and tb is not None and _diff(_ang(ta), _ang(tb)) < ANG_LISO


def armonizar(cs, max_mov=0.2):
    """Armoniza (G2) los nodos lisos entre dos curvas. Solo mueve el nodo sobre
    la recta de sus asas; si el movimiento pasaría de `max_mov` veces la
    distancia entre asas, no lo toca (ahí el problema es de dibujo, no de ajuste)."""
    out, movidos = [], 0
    for ctr in cs:
        segs = [list(s) for s in a_segmentos(ctr)]
        n = len(segs)
        for i in range(n):
            a, b = segs[i], segs[(i + 1) % n]
            if len(a) != 4 or len(b) != 4 or not _es_liso(a, b):
                continue
            a1, a2, b1, b2 = a[1], a[2], b[1], b[2]
            d = _interseccion(a1, a2, b1, b2)
            if d is None:
                continue
            try:
                p0 = math.dist(a1, a2) / math.dist(a2, d)
                p1 = math.dist(d, b1) / math.dist(b1, b2)
            except ZeroDivisionError:
                continue
            if p0 <= 0 or p1 <= 0:
                continue
            r = math.sqrt(p0 * p1)
            t = r / (r + 1)
            nuevo = (a2[0] + t * (b1[0] - a2[0]), a2[1] + t * (b1[1] - a2[1]))
            if math.dist(nuevo, a[3]) > max_mov * math.dist(a2, b1):
                continue
            if math.dist(nuevo, a[3]) > 0.05:
                a[3] = b[0] = nuevo
                movidos += 1
        out.append(a_contorno(segs))
    return out, movidos


def enderezar_asas(cs, max_ang=6.0):
    """Asas de nodos lisos que están casi horizontales o verticales (a menos de
    `max_ang` grados) se giran a la horizontal o vertical exacta, conservando su
    largo. Es la regla «asas H/V en los extremos»; cambia poco la forma."""
    out, n_ = [], 0
    for ctr in cs:
        segs = [list(s) for s in a_segmentos(ctr)]
        n = len(segs)
        for i in range(n):
            a, b = segs[i], segs[(i + 1) % n]
            if len(a) != 4 or len(b) != 4 or not _es_liso(a, b):
                continue
            ang = _ang(_sub(b[1], b[0]))
            eje = min((0, 90, 180, -90, -180), key=lambda k: _diff(ang, k))
            off = _diff(ang, eje)
            if not (0.05 < off <= max_ang):
                continue
            r = math.radians(eje)
            u = (math.cos(r), math.sin(r))
            p = a[3]
            la, lb = math.dist(a[2], p), math.dist(b[1], p)
            a[2] = (p[0] - u[0] * la, p[1] - u[1] * la)
            b[1] = (p[0] + u[0] * lb, p[1] + u[1] * lb)
            n_ += 1
        out.append(a_contorno(segs))
    return out, n_


def alisar_quiebres(cs, max_ang=8.0):
    """Quiebres accidentales (tangentes que difieren entre ANG_LISO y `max_ang`
    grados) se vuelven nodos lisos: con dos curvas, las asas toman la bisectriz;
    con una recta, la curva se alinea con la recta. Las esquinas reales (más de
    `max_ang`) y las uniones entre rectas no se tocan. Es **Point › Curve**."""
    out, n_ = [], 0
    for ctr in cs:
        segs = [list(s) for s in a_segmentos(ctr)]
        n = len(segs)
        for i in range(n):
            a, b = segs[i], segs[(i + 1) % n]
            ta, tb = tangente_llegada(a), tangente_salida(b)
            if ta is None or tb is None:
                continue
            dang = _diff(_ang(ta), _ang(tb))
            if not (ANG_LISO <= dang < max_ang):
                continue
            p = a[-1]
            if len(a) == 4 and len(b) == 4:
                ua = (ta[0] / math.hypot(*ta), ta[1] / math.hypot(*ta))
                ub = (tb[0] / math.hypot(*tb), tb[1] / math.hypot(*tb))
                u = (ua[0] + ub[0], ua[1] + ub[1])
            elif len(a) == 2 and len(b) == 4:
                u = ta
            elif len(a) == 4 and len(b) == 2:
                u = tb
            else:
                continue
            nu = math.hypot(*u)
            u = (u[0] / nu, u[1] / nu)
            if len(a) == 4:
                la = math.dist(a[2], p)
                a[2] = (p[0] - u[0] * la, p[1] - u[1] * la)
            if len(b) == 4:
                lb = math.dist(b[1], p)
                b[1] = (p[0] + u[0] * lb, p[1] + u[1] * lb)
            n_ += 1
        out.append(a_contorno(segs))
    return out, n_


def limpiar(cs, asas=True, quiebres=False):
    """Puntos en los extremos, quiebres accidentales alisados (opcional), asas
    H/V (opcional) y armonización G2, en ese orden (la armonización al final
    para que el nodo quede en el punto de curvatura continua)."""
    cs = agregar_extremos(cs)
    n = 0
    if quiebres:
        cs, k = alisar_quiebres(cs)
        n += k
    if asas:
        cs, k = enderezar_asas(cs)
        n += k
    cs, m = armonizar(cs)
    return cs, n + m


# --- Diagnóstico ----------------------------------------------------------------------

def diagnosticar(cs):
    """Problemas de dibujo de un glifo: {tipo: cantidad}."""
    prob = {"extremo sin nodo": 0, "quiebre": 0, "asa casi H/V": 0, "salto de curvatura (G2)": 0}
    nodos = 0
    for ctr in cs:
        segs = a_segmentos(ctr)
        n = len(segs)
        nodos += n
        for i, s in enumerate(segs):
            prob["extremo sin nodo"] += len(extremos_interiores(s))
            b = segs[(i + 1) % n]
            ta, tb = tangente_llegada(s), tangente_salida(b)
            if ta is None or tb is None:
                continue
            dang = _diff(_ang(ta), _ang(tb))
            if ANG_LISO <= dang < ANG_QUIEBRE:
                prob["quiebre"] += 1
            for v in (ta, tb):
                if len(s) == 4 or len(b) == 4:
                    off = min(_diff(_ang(v), k) for k in (0, 90, 180, 270))
                    if ANG_HV <= off < ANG_CASI_HV:
                        prob["asa casi H/V"] += 1
                        break
            if len(s) == 4 and len(b) == 4 and dang < ANG_LISO:
                k1, k2 = curvatura(s, 1), curvatura(b, 0)
                m = max(abs(k1), abs(k2))
                if m > 1e-4 and abs(k1 - k2) / m > G2_TOL:
                    prob["salto de curvatura (G2)"] += 1
    return prob, nodos


def peine(cs, escala=3000, pasos=14, tope=70, minimo=12):
    """Peine de curvatura: lista de líneas (p, p + normal·k·escala) y la envolvente.
    Los dientes se limitan a `tope` unidades (las gotas y remates muy cerrados
    darían dientes enormes) y se omiten los segmentos de menos de `minimo`."""
    dientes, env = [], []
    for ctr in cs:
        for s in a_segmentos(ctr):
            if len(s) != 4 or math.dist(s[0], s[3]) < minimo:
                continue
            tramo = []
            for j in range(pasos + 1):
                t = j / pasos
                p, nrm, k = punto(s, t), normal(s, t), curvatura(s, t)
                largo = max(-tope, min(tope, k * escala))
                q = (p[0] + nrm[0] * largo, p[1] + nrm[1] * largo)
                dientes.append((p, q))
                tramo.append(q)
            env.append(tramo)
    return dientes, env

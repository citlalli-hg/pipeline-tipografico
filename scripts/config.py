"""Configuración del pipeline: valores comunes + los del proyecto tipográfico.

El pipeline vive en la carpeta `pipeline/` (submódulo de Git) de cada fuente.
Lo propio de cada fuente está en `proyecto.py`, en la raíz de su repositorio:
nombre, métricas, set de caracteres, espaciado y archivos de partida.
Aquí solo hay valores por defecto y rutas derivadas; no edites este archivo
para una fuente concreta.

Raíz del proyecto, en este orden:
  1. La variable de entorno TIPO_PROYECTO.
  2. La carpeta que contiene a `pipeline/` (uso normal, como submódulo).
  3. El directorio actual, si tiene `proyecto.py`.
"""
import importlib.util
import os
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent.parent


def _find_root():
    env = os.environ.get("TIPO_PROYECTO")
    if env:
        return Path(env).resolve()
    if (PIPELINE.parent / "proyecto.py").is_file():
        return PIPELINE.parent
    cwd = Path.cwd()
    for p in [cwd, *cwd.parents]:
        if (p / "proyecto.py").is_file():
            return p
    return PIPELINE.parent


ROOT = _find_root()

# --- Valores por defecto (cada proyecto los sobrescribe en proyecto.py) ------
FAMILY = "SinNombre"
SLUG = None                 # nombre de archivos: por defecto FAMILY en minúsculas
STYLE = "Regular"
VERSION = "0.001"
DESIGNER = "Citlalli HG"
COPYRIGHT = None            # por defecto: "Copyright (c) <año>, DESIGNER."
VENDOR = "CHG "

# Métricas verticales (unidades de fuente)
UPM = 1000
ASCENT = 800                # ascent + descent = UPM
DESCENT = 200
X_HEIGHT = 500
CAP_HEIGHT = 700
ASCENDER = 740
DESCENDER = -200
SIDEBEARING = 40            # margen lateral de glifos nuevos o importados
OVERSHOOT = None            # sobresalto de redondas; None = medirlo en la o

# Estabilizar también mayúsculas y cifras en la altura de mayúsculas (10_estabilizar.py)
ESTABILIZAR_MAYUSCULAS = False
OVERSHOOT_MAY = 10          # sobresalto de las redondas de caja alta y cifras
ZONA_MAY = 20               # cuánto por dentro de la línea se buscan extremos (las contraformas se descartan)

# Etapa "completar": fuente de partida (OTF/TTF) y corrección de línea base.
FUENTE_BASE = None          # ruta relativa a la raíz del proyecto
BASELINE_SHIFT = 0

# Limpieza de curvas al completar (pipeline/scripts/curvas.py): puntos en los
# extremos, asas H/V y armonización G2. None = no se toca nada; "bocetos" = solo
# los glifos que proyecto/completar.py marca como boceto; "todo" = toda la fuente
# (los glifos de partida se limpian ANTES de construir, así las piezas que se
# toman de ellos ya salen limpias); o una lista de nombres.
# No se aplica a glifos dibujados a mano salvo que se pida aquí.
LIMPIAR_CURVAS = None
LIMPIAR_QUIEBRES = False    # además, alisar quiebres accidentales (< 8°)

# Potrace (02_importar.py): ver pipeline/docs/vectorizacion.md
POTRACE = {"alphamax": 1.0, "opttolerance": 0.2, "turdsize": 10}

# Espaciado provisional por lados (método de Tracy). Vacío = no se toca.
LADOS_MIN = {"recto": 40, "redondo": 28, "diagonal": 8, "abierto": 14}
LADOS_MAY = {"recto": 55, "redondo": 38, "diagonal": 8, "abierto": 20}
ESPACIADO = {}

# Texto para el PDF de pruebas
TEXTO_PRUEBAS = ("La tipografía nace del trazo, del ritmo y del blanco entre las letras. "
                 "¿Quién lee sin ver la forma? Pingüino, ñandú, árbol, café.")

# --- Geometría de la plantilla de dibujo (milímetros) --------------------------
# Cada celda contiene una "caja eme": su altura equivale a UPM unidades y la
# línea base queda a DESCENT unidades del borde inferior.
MM_PER_UNIT = 0.03                  # 1000 unidades = 30 mm
CELL_W_FACTOR = 1.2                 # ancho de la caja respecto a la altura
LABEL_MM = 5
GAP_MM = 4
PAGE_W_MM, PAGE_H_MM = 215.9, 279.4 # tamaño carta
MARKER_MM = 8
MARGIN_MM = 12
DPI = 600

# --- Set de caracteres -----------------------------------------------------------
UPPER = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
LOWER = [chr(c) for c in range(ord("a"), ord("z") + 1)] + ["dotlessi"]
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
PUNCT = [
    "period", "comma", "colon", "semicolon", "exclam", "exclamdown", "question",
    "questiondown", "hyphen", "endash", "emdash", "parenleft", "parenright",
    "quoteleft", "quoteright", "quotedblleft", "quotedblright", "guillemotleft",
    "guillemotright", "ampersand", "at", "numbersign", "dollar", "percent",
    "slash", "asterisk",
]
MARKS = ["acute", "grave", "dieresis", "tilde", "circumflex"]
DRAWN = None                # glifos que se dibujan a mano; None = todo el núcleo; "semilla" = SEMILLA

# Set semilla (docs/set-semilla.md): lo mínimo que hay que dibujar para que el
# pipeline genere una fuente completa, en el orden en que conviene dibujarlo.
SEMILLA = (
    # 1. Controles: fijan asta, filete, panza, remate y sobresalto
    ["n", "o", "H", "O"]
    # 2. Minúsculas por familia (cada una aporta una pieza que se reutiliza)
    + ["h", "m", "u", "r", "b", "d", "p", "q", "c", "e", "a", "s", "g",
       "i", "l", "j", "f", "t", "v", "w", "x", "y", "k", "z"]
    # 3. Mayúsculas por familia
    + ["I", "L", "E", "F", "T", "D", "C", "G", "Q", "B", "P", "R", "S", "U", "J",
       "A", "V", "W", "X", "Y", "K", "M", "N", "Z"]
    # 4. No letras que no salen bien por construcción
    + ["period", "comma", "question", "exclam", "parenleft", "hyphen",
       "acute", "tilde", "cedilla",
       "one", "two", "three", "four", "six", "seven", "ampersand"]
)

COMPOSITES = [
    0x00E1, 0x00E9, 0x00ED, 0x00F3, 0x00FA, 0x00FC, 0x00F1,  # á é í ó ú ü ñ
    0x00C1, 0x00C9, 0x00CD, 0x00D3, 0x00DA, 0x00DC, 0x00D1,  # Á É Í Ó Ú Ü Ñ
    0x00E0, 0x00E8, 0x00EC, 0x00F2, 0x00F9,                  # à è ì ò ù
    0x00E2, 0x00EA, 0x00EE, 0x00F4, 0x00FB,                  # â ê î ô û
    0x00E4, 0x00EB, 0x00EF, 0x00F6,                          # ä ë ï ö
]

LABELS = {
    "dotlessi": "ı", "dotlessj": "ȷ", "zero": "0", "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
    "nine": "9", "period": ".", "comma": ",", "colon": ":", "semicolon": ";",
    "exclam": "!", "exclamdown": "¡", "question": "?", "questiondown": "¿",
    "hyphen": "-", "endash": "–", "emdash": "—", "parenleft": "(",
    "parenright": ")", "quoteleft": "‘", "quoteright": "’",
    "quotedblleft": "“", "quotedblright": "”", "guillemotleft": "«",
    "guillemotright": "»", "ampersand": "&", "at": "@", "numbersign": "#",
    "dollar": "$", "percent": "%", "slash": "/", "asterisk": "*",
    "acute": "´", "grave": "`", "dieresis": "¨", "tilde": "˜",
    "circumflex": "ˆ",
}

# --- Valores del proyecto -----------------------------------------------------------------
_spec_path = ROOT / "proyecto.py"
if _spec_path.is_file():
    _spec = importlib.util.spec_from_file_location("proyecto", _spec_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    for _k, _v in vars(_mod).items():
        if _k.isupper():
            globals()[_k] = _v

# --- Derivados ----------------------------------------------------------------------------
SLUG = SLUG or FAMILY.lower()
COPYRIGHT = COPYRIGHT or f"Copyright (c) 2026, {DESIGNER}."
if DRAWN is None:
    DRAWN = UPPER + LOWER + DIGITS + PUNCT + MARKS
elif DRAWN == "semilla":
    DRAWN = list(SEMILLA)

SOURCES = ROOT / "sources"
SFD = SOURCES / f"{SLUG}.sfd"                  # maestro de FontForge: fuente de verdad
BASE_OTF = SOURCES / f"{SLUG}-base.otf"        # salida de `completar`
ESTABLE_OTF = SOURCES / f"{SLUG}-estable.otf"  # salida de `estabilizar`
FEATURES = SOURCES / "features.fea"
KERN_FEA = SOURCES / "kern.fea"
COMPLETAR = ROOT / "proyecto" / "completar.py" # construcciones propias del proyecto (opcional)
FONTS = ROOT / "fonts"
PROOFS = ROOT / "proofs"
FONT_OTF = FONTS / f"{FAMILY}-{STYLE}.otf"

EM_MM = UPM * MM_PER_UNIT
CELL_W_MM = CELL_W_FACTOR * EM_MM
GRID_INSET_MM = MARGIN_MM + MARKER_MM + 4
PX_PER_MM = DPI / 25.4


def grid_shape():
    usable_w = PAGE_W_MM - 2 * GRID_INSET_MM
    usable_h = PAGE_H_MM - 2 * GRID_INSET_MM
    cols = int((usable_w + GAP_MM) // (CELL_W_MM + GAP_MM))
    rows = int((usable_h + GAP_MM) // (LABEL_MM + EM_MM + GAP_MM))
    return cols, rows


def cell_box_mm(slot):
    """Caja eme de la celda número `slot` dentro de su página: (x, y, w, h) en mm,
    con y medida desde el borde superior de la página."""
    cols, rows = grid_shape()
    col, row = slot % cols, (slot // cols) % rows
    x = GRID_INSET_MM + col * (CELL_W_MM + GAP_MM)
    y = GRID_INSET_MM + row * (LABEL_MM + EM_MM + GAP_MM) + LABEL_MM
    return x, y, CELL_W_MM, EM_MM


def per_page():
    cols, rows = grid_shape()
    return cols * rows


def label(name):
    return LABELS.get(name, name)


def file_stem(name):
    """Nombre de archivo seguro en sistemas que no distinguen mayúsculas
    (macOS, Windows): 'A' -> 'A_', 'a' -> 'a' (convención UFO)."""
    return "".join(c + "_" if c.isupper() else c for c in name)


def rel(path):
    """Ruta relativa a la raíz del proyecto, para mensajes."""
    try:
        return Path(path).resolve().relative_to(ROOT)
    except ValueError:
        return path

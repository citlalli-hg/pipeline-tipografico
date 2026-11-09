"""{{FAMILIA}} — configuración del proyecto.

Lo que es propio de esta fuente. Todo lo demás (scripts, documentación,
integración continua) viene del pipeline común en `pipeline/`.
Lista completa de opciones y valores por defecto: pipeline/scripts/config.py
"""

# --- Identidad -------------------------------------------------------------------
FAMILY = "{{FAMILIA}}"
STYLE = "Regular"
VERSION = "0.001"
DESIGNER = "Citlalli HG"

# --- Métricas verticales (unidades de fuente, UPM 1000) -------------------------------
X_HEIGHT = 500
CAP_HEIGHT = 700
ASCENDER = 740
DESCENDER = -200

# --- Punto de partida (opcional) -------------------------------------------------------
# Si la fuente parte de vectores existentes, `mise run completar` los toma de aquí.
# Si se dibuja desde cero, deja FUENTE_BASE = None y usa plantilla → digitalizar → importar.
FUENTE_BASE = None          # p. ej. "sources/originales/MiFuente.otf"
BASELINE_SHIFT = 0

# --- Set de caracteres -------------------------------------------------------------------
# DRAWN: glifos que se dibujan a mano (plantilla). None = núcleo completo (A–Z, a–z, cifras, signos, acentos).
DRAWN = None

# --- Curvas (opcional) ----------------------------------------------------------------
# Puntos en extremos, asas H/V y armonización G2 al completar: None, "bocetos" o lista de glifos.
LIMPIAR_CURVAS = None       # None, "bocetos", "todo" o lista de glifos
LIMPIAR_QUIEBRES = False    # además, alisar quiebres accidentales (< 8°)
# Mayúsculas y cifras planas en la altura de mayúsculas y redondas con sobresalto
ESTABILIZAR_MAYUSCULAS = False
OVERSHOOT_MAY = 10
# Potrace para glifos escaneados (ver pipeline/docs/vectorizacion.md)
# POTRACE = {"alphamax": 1.0, "opttolerance": 0.2, "turdsize": 10}

# --- Espaciado provisional por lados (opcional, método de Tracy) --------------------------
# ESPACIADO = {"n": ("recto", "recto"), "o": ("redondo", "redondo"), ...}
ESPACIADO = {}

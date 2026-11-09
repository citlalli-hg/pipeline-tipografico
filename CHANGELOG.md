# Cambios del pipeline

Lo más reciente arriba. Cada fuente recibe estos cambios por un PR de Dependabot.

## 2026-11-08 — Construir glifos con partes de otros

- `contornos.py`: `recortar` (corte por una recta, con curvas), `recortar_x`, `recortar_y`, `caja`, `estrechar` y `achatar` (quitan una franja sin cambiar grosores), `rotate`, `scale`, `mirror_x`. Sirven en `proyecto/completar.py` para armar cifras y signos con astas, panzas y terminales de las letras de la propia fuente. Sterna los usa en su primera revisión.

## 2026-11-08 — Pipeline común

- El pipeline sale de Elocaso y se vuelve compartido: submódulo `pipeline/` en cada fuente.
- `proyecto.py` en cada fuente reemplaza a `scripts/config.py`; `config.py` solo tiene valores por defecto y rutas derivadas (`sources/<slug>.sfd`, `<slug>-base.otf`, `<slug>-estable.otf`).
- `06_completar_set.py` es genérico: copia `FUENTE_BASE`, corrige la línea base, llama a `proyecto/completar.py` si existe y aplica el espaciado por lados (`ESPACIADO`).
- Utilidades de contornos en `scripts/contornos.py`.
- `10_estabilizar.py`: sobresalto fijo opcional (`OVERSHOOT`) y kerning solo con los glifos que existen.
- `07_a_sfd.py --estable`; `qa.py`; `nuevo_proyecto.py`.
- Tareas de Mise en `tareas.toml`; CI en acciones compuestas (`.github/actions/*`); Dependabot para actualizar.
- Verificado: Elocaso produce exactamente la misma base, altura de x y kerning que antes.

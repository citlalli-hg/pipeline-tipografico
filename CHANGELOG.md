# Cambios del pipeline

Lo más reciente arriba. Cada fuente recibe estos cambios por un PR de Dependabot.

## 2026-11-08 — Hojas de revisión en el pipeline

- **Estabilizar** exporta las hojas de revisión desde la fuente compilada y las sube con el maestro.
- **Estabilizar** se detiene si el maestro tiene commits hechos a mano (para no perder correcciones); entrada `forzar` para reemplazarlo a propósito. Requiere `fetch-depth: 0` en el workflow del proyecto (plantilla actualizada).
- Hojas: nueva `13-acentos`, `14-otros` automática (todo glifo con contorno que no esté en otra hoja), ‹ › ‚ „ … en signos, * / en especiales; cada hoja muestra solo los glifos que existen.
- `docs/pipeline.md`: etapa 7b, ciclo de revisión con las hojas.

## 2026-11-08 — Construir glifos con partes de otros

- `contornos.py`: `recortar` (corte por una recta, con curvas), `recortar_x`, `recortar_y`, `caja`, `estrechar` y `achatar` (quitan una franja sin cambiar grosores), `estirar` y `ensanchar` (agregan una franja rellenando los trazos rectos que cruzan el corte), `tramos_y` y `tramos_x`, `rotate`, `scale`, `mirror_x`. Sirven en `proyecto/completar.py` para armar cifras y signos con astas, panzas y terminales de las letras de la propia fuente. Sterna los usa en su primera revisión.
## 2026-11-08 — Hojas: iteraciones e importación en CI

- `11_hojas.py importar` conserva los márgenes laterales (o el ancho con `--conservar-ancho`), recentra los acentos y acepta hojas con sufijo (`01-redondas-iteracion-2.svg`). Viene del PR #8 de Elocaso.
- `03_limpiar.py`: si FontForge no puede armar una acentuada (**Element › Build › Build Accented Glyph**), la arma como base + acento por referencias, con el acento centrado sobre la tinta; usa ı/ȷ para i/j.
- Acción `importar` y workflow de plantilla `importar.yml` (ramas `importar/…`).

## 2026-11-08 — Pipeline común

- El pipeline sale de Elocaso y se vuelve compartido: submódulo `pipeline/` en cada fuente.
- `proyecto.py` en cada fuente reemplaza a `scripts/config.py`; `config.py` solo tiene valores por defecto y rutas derivadas (`sources/<slug>.sfd`, `<slug>-base.otf`, `<slug>-estable.otf`).
- `06_completar_set.py` es genérico: copia `FUENTE_BASE`, corrige la línea base, llama a `proyecto/completar.py` si existe y aplica el espaciado por lados (`ESPACIADO`).
- Utilidades de contornos en `scripts/contornos.py`.
- `10_estabilizar.py`: sobresalto fijo opcional (`OVERSHOOT`) y kerning solo con los glifos que existen.
- `07_a_sfd.py --estable`; `qa.py`; `nuevo_proyecto.py`.
- Tareas de Mise en `tareas.toml`; CI en acciones compuestas (`.github/actions/*`); Dependabot para actualizar.
- Verificado: Elocaso produce exactamente la misma base, altura de x y kerning que antes.

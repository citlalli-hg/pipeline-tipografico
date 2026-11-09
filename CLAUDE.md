# Contexto para Claude — pipeline común

Este repositorio es la raíz compartida de todos los proyectos tipográficos de Citlallihg. Cada fuente (`citlalli-hg/elocaso`, `citlalli-hg/sterna`, …) lo incluye como submódulo en `pipeline/` y pone lo propio en `proyecto.py` y `proyecto/completar.py`.

- Herramientas de la diseñadora: FontForge y Affinity. Cualquier otra herramienta debe ser open source.
- Ningún script puede tener nombres, métricas ni rutas de una fuente concreta: léelos de `scripts/config.py` (`C.FAMILY`, `C.SFD`, `C.BASE_OTF`, `C.ESTABLE_OTF`, `C.X_HEIGHT`…). Una opción nueva lleva su valor por defecto en `config.py` y se documenta en `plantilla-proyecto/proyecto.py`.
- Un cambio aquí llega a todas las fuentes: verifica que no cambie la salida de las existentes (por ejemplo, que `mise run completar` y `mise run estabilizar` de Elocaso den los mismos glifos) y anótalo en `CHANGELOG.md`.
- Fuente de verdad de cada proyecto: su `sources/<slug>.sfd`. Nunca regenerar ni reemplazar glifos existentes sin que ella lo pida.
- No aplicar correcciones automáticas de morfología a glifos dibujados; estabilizar altura de x, espaciado y kerning sí.
- Nombres de glifo AGL; en archivos, mayúsculas con guion bajo (`A_.png`).
- Al dar instrucciones de apps, usar los nombres de menús y botones en inglés; el texto puede ir en español.
- Trabaja en dos equipos, uno con Windows. Cambios por rama y pull request.

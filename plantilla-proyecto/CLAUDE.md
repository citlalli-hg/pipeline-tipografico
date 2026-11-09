# Contexto para Claude

Repositorio de la fuente tipográfica {{FAMILIA}} (marca Citlallihg). Usa el pipeline común `citlalli-hg/pipeline-tipografico`, incluido como submódulo en `pipeline/`.

- **Qué va dónde.** Lo propio de esta fuente vive aquí: `proyecto.py` (métricas, set, espaciado, fuente de partida), `proyecto/completar.py` (construcciones propias), `sources/`, `brief/`. Scripts, tareas, acciones de CI y documentación del método viven en el pipeline: si el cambio sirve a cualquier fuente, se hace en `citlalli-hg/pipeline-tipografico` (rama + PR) y llega aquí por Dependabot o `mise run actualizar-pipeline`. No edites archivos dentro de `pipeline/` desde este repo.
- Instrucciones del método para Claude: `pipeline/CLAUDE.md`.
- Fuente de verdad: `sources/<slug>.sfd`. Nunca regenerar ni reemplazar glifos existentes sin que ella lo pida: pueden tener retoques manuales.
- Las decisiones de diseño se registran en `brief/bitacora.md`.
- Al dar instrucciones de apps, usar los nombres de menús y botones en inglés; el texto puede ir en español.
- Trabaja en dos equipos, uno con Windows: todo debe funcionar sin `make` ni comandos solo de Unix. Cambios por rama y pull request.

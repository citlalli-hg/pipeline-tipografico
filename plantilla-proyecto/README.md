# {{FAMILIA}}

Fuente tipográfica para la identidad de marca Citlallihg, construida con el [pipeline tipográfico común](https://github.com/citlalli-hg/pipeline-tipografico) (FontForge, Affinity y herramientas open source).

## Empezar

```
git clone --recurse-submodules https://github.com/citlalli-hg/{{SLUG}}
cd {{SLUG}}
mise trust && mise install && mise run setup && mise run doctor
```

En Windows, `pipeline/scripts/setup-windows.ps1 -Repo citlalli-hg/{{SLUG}}` instala todo y clona el repo.

## Qué hay aquí

| Ruta | Contenido |
| --- | --- |
| `proyecto.py` | Configuración de esta fuente: métricas, set, espaciado, fuente de partida |
| `proyecto/completar.py` | Construcciones propias (opcional) |
| `sources/` | Maestro `.sfd`, `features.fea`, `kern.fea` y archivos de partida |
| `brief/` | Brief, referentes y bitácora de decisiones |
| `pipeline/` | Pipeline común (submódulo): scripts, tareas, CI y documentación |

## Pipeline

`mise tasks` lista las tareas. El método completo está en [`pipeline/docs/pipeline.md`](pipeline/docs/pipeline.md) y cómo se comparten el pipeline y sus actualizaciones en [`pipeline/docs/proyectos.md`](pipeline/docs/proyectos.md).

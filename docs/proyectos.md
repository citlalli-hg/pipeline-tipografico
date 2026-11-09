# Varios proyectos, un pipeline

Cada fuente (Elocaso, Sterna y las que vengan) tiene su propio repositorio privado. El método, los scripts, las tareas de Mise, las acciones de GitHub Actions y esta documentación viven una sola vez en **`citlalli-hg/pipeline-tipografico`**, que cada fuente incluye como submódulo de Git en la carpeta `pipeline/`.

```
pipeline-tipografico/              ← raíz común (público: solo método, sin archivos de fuentes)
├── scripts/                       ← etapas 00–11, config.py, contornos.py, ff.py, doctor.py
├── tareas.toml                    ← tareas de `mise run …`
├── .github/actions/               ← preparar, build, estabilizar, hojas (CI de todas las fuentes)
├── docs/                          ← pipeline.md, hojas.md, este documento
└── plantilla-proyecto/            ← punto de partida de una fuente nueva

elocaso/  ·  sterna/  ·  <nueva>/   ← un repositorio por fuente
├── proyecto.py                    ← lo propio: nombre, métricas, set, espaciado, fuente de partida
├── proyecto/completar.py          ← construcciones propias (opcional)
├── sources/  brief/  hojas/       ← maestro .sfd, features, bitácora, hojas de Affinity
├── mise.toml                      ← incluye pipeline/tareas.toml
├── .github/workflows/             ← llamadas cortas a pipeline/.github/actions
└── pipeline/                      ← submódulo: versión fija del pipeline común
```

## Qué va dónde

| Si cambias… | Va en |
| --- | --- |
| Un script, una tarea, una acción de CI, la metodología | `pipeline-tipografico` |
| Métricas, set de caracteres, espaciado, nombre | `proyecto.py` de la fuente |
| Glifos construidos solo para esa fuente | `proyecto/completar.py` de la fuente |
| Dibujo, maestro, kerning, bitácora | la fuente |

Regla práctica: si el cambio le serviría a otra fuente, es del pipeline.

## Cómo llega una mejora del pipeline a todas las fuentes

1. Se cambia el pipeline en una rama de `pipeline-tipografico` y se fusiona su pull request. Anota el cambio en `CHANGELOG.md`.
2. Cada fuente fija una versión concreta del pipeline (el commit del submódulo). Así una mejora nunca cambia una fuente sin revisión.
3. **Dependabot** revisa cada mañana si hay versión nueva y abre en cada fuente un pull request «Pipeline: bump pipeline…». Ese PR corre el build de la fuente con el pipeline nuevo: si pasa, se fusiona.
   - Para no esperar: en la fuente, **Insights › Dependency graph › Dependabot › Check for updates**, o en tu equipo:
     ```
     git switch -c pipeline/actualizar
     mise run actualizar-pipeline
     git commit -am "Pipeline actualizado" && git push -u origin HEAD && gh pr create --fill
     ```
4. Después de fusionar, en cada equipo basta con `git pull` (con `submodule.recurse` activado, `pipeline/` se pone solo en la versión nueva; `setup-windows.ps1` lo activa).

## Probar un cambio del pipeline antes de publicarlo

Desde una fuente, entra al submódulo y cambia a la rama del pipeline:

```
cd pipeline
git fetch && git switch mi-rama
cd ..
mise run completar      # o la etapa que cambió
```

Cuando el PR del pipeline se fusione, vuelve a `main` dentro de `pipeline/` y actualiza el puntero como en el paso 3.

## Crear una fuente nueva

```
python pipeline/scripts/nuevo_proyecto.py "Nombre" --github
```

Crea `../nombre/` desde `plantilla-proyecto/`, con el pipeline como submódulo, y el repositorio privado en GitHub. Después llena `proyecto.py` y `brief/brief.md`.

- Fuente que parte de vectores existentes (como Elocaso desde Elalba, o Sterna desde sus archivos de 2018): pon el archivo en `sources/`, define `FUENTE_BASE` y `BASELINE_SHIFT`, y corre `mise run completar`.
- Fuente desde cero: deja `FUENTE_BASE = None` y sigue plantilla → digitalizar → importar.

## Clonar una fuente en otro equipo

```
git clone --recurse-submodules https://github.com/citlalli-hg/<fuente>
```

Si ya estaba clonada sin el submódulo: `git submodule update --init`.

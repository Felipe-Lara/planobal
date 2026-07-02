# Plano3D

Convierte planos CAD (DXF/DWG de AutoCAD) en un edificio 3D **caminable en primera
persona**, donde se pueden **repintar superficies** (madera / cemento / pintura) y
componer varios planos en un mismo edificio (pisos apilados + extensión hacia el patio).

> Contexto operativo para Claude Code en [CLAUDE.md](CLAUDE.md). Plan de trabajo por
> sprints en [ROADMAP.md](ROADMAP.md).

---

## Arquitectura: dos mitades desacopladas

```
   CAD (DXF/DWG)
        │
        ▼
┌─────────────────────┐        archivos = contrato        ┌──────────────────────┐
│  PIPELINE (Python)  │  ── geometry.json / building.json ─▶│   ENGINE (Godot 4.x) │
│  pipeline/          │                                     │   engine/            │
│  DXF → JSON → .gltf │◀── paint_state.json ────────────────│  walkthrough + pintar│
└─────────────────────┘                                     └──────────────────────┘
```

Las dos mitades **no se conocen**: se comunican solo por archivos. Esto permite
desarrollarlas en paralelo y regenerar la geometría sin perder el estado de pintado.

---

## El contrato (SAGRADO)

Tres archivos JSON. El pipeline escribe los dos primeros; el engine escribe el tercero.
**Nadie escribe el archivo del otro.** Esquemas pydantic en [`pipeline/schema/`](pipeline/schema/),
ejemplos a mano en [`pipeline/schema/examples/`](pipeline/schema/examples/).

| Archivo | Lo escribe | Contenido |
|---|---|---|
| `geometry.json` | pipeline | `walls[]`, `openings[]`, `rooms[]`, `source` — por plano |
| `building.json` | pipeline | `planos[]` con `offset_xy`, `elevation`, `rotation_deg`, `slab_thickness` |
| `paint_state.json` | engine | `surface_id → material` |

**Ids estables:** los ids de `geometry.json` son un hash de la geometría (no un índice),
para que `paint_state.json` sobreviva a regeneraciones del `.gltf`.

Cambiar el contrato requiere discutirlo primero (issue). Los tests de
[`pipeline/tests/test_schema.py`](pipeline/tests/test_schema.py) lo congelan.

---

## Convenciones

- **Unidades: siempre metros.** Se convierte desde `$INSUNITS` del DXF en el ingest.
- **Coordenadas:** plano en X/Y, altura en `elevation`. Godot usa Y arriba; el mapeo
  vive solo en `pipeline/geometry/coords.py`.
- **Aberturas:** los muros se generan **segmentados** (dintel/antepecho/jambas como
  mallas propias), nunca con booleanos en runtime.
- **Materiales:** el `.gltf` sale "desnudo"; el nombre de cada mesh **es** su `surface_id`.
  Godot asigna materiales en runtime leyendo `paint_state.json`.
- Python: `black` + `ruff`, type hints, tests en `pipeline/tests/`.
- Godot 4.x, GDScript. Texturas solo **CC0** (Poly Haven, ambientCG).

---

## Puesta en marcha

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows;  source .venv/bin/activate en Linux/mac
pip install -e ".[dev]"
```

## Comandos

```bash
python -m pipeline validate <archivo.json>   # valida contra el contrato
python -m pipeline ingest   <plano.dxf|dwg>  # DXF → geometry.json   (Fase 2)
python -m pipeline build    <building.json>  # building.json → .gltf (Fase 1/3)
python tools/inspect_dxf.py <plano.dxf>      # resumen de un DXF sin quemar tokens
pytest                                        # tests del pipeline
```

Abrir el visor: abrir la carpeta [`engine/`](engine/) en Godot 4.x.

---

## Estructura del repo

```
pipeline/
  ingest/    DXF/DWG → entidades (ezdxf, odafc)      · agente: dxf-parser
  detect/    heurísticas de muros/aberturas/recintos · agente: dxf-parser
  geometry/  geometry.json → mallas (+ coords.py)    · agente: geometry-builder
  compose/   building.json → composición → .gltf     · agente: geometry-builder
  schema/    contrato pydantic + examples/
  tests/     pytest sobre samples/ y examples/
engine/      proyecto Godot 4.x                       · agente: godot-integrator
tools/       inspect_dxf.py y utilidades de dev
samples/     DXF reales y fixtures de geometría
```

## Subagentes

Definidos en [`.claude/agents/`](.claude/agents/). La sesión principal orquesta:

- **dxf-parser** — DXF/DWG → `geometry.json` (trabaja en `pipeline/ingest`, `pipeline/detect`).
- **geometry-builder** — `geometry.json`/`building.json` → `.gltf` (`pipeline/geometry`, `pipeline/compose`).
- **godot-integrator** — todo `engine/` (FPS, raycast, repintado, multi-nivel, UI).

---

## Estado

**Fase 0 en curso** — contrato pydantic congelado, ejemplos a mano validando, CLI
`validate` operativo. Próximo: Fase 1 (slice vertical Godot). Ver [ROADMAP.md](ROADMAP.md).

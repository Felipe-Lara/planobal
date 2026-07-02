# Changelog

Todos los cambios notables de Plano3D se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado: cada commit significativo suma una entrada y sube el patch
(`v0.1`, `v0.2`, ...). Los commits que solo regeneran assets derivados
(ej. `.gltf` de muestra) se documentan junto al commit que los originó,
no como entrada propia. **`v1.0` = MVP** (Fases 0–4 del README/CLAUDE.md:
contrato, slice vertical, ingest DXF real, composición y repintado —
ver ROADMAP.md para el detalle sprint por sprint).

## [Unreleased]

## [v0.10] — 2026-07-02
### Added
- `CHANGELOG.md` (este archivo).

## [v0.9] — 2026-07-02
### Docs
- `claude.md`: sección "Estado actual" al tope, resumen para arrancar sesiones limpio.
- `ROADMAP.md`: Sprints 1, 2 y 4 marcados como completos.

## [v0.8] — 2026-07-02
### Added
- Menú de pausa en Godot (`menu.tscn`/`menu.gd`): Esc pausa el juego y libera
  el mouse, botón "Reiniciar posición" y botones para saltar entre pisos
  conocidos (elevaciones hardcodeadas desde `building.example.json`).
  Sección "Materiales" placeholder lista para el Sprint 5.

## [v0.7] — 2026-07-02
### Added
- `pipeline/compose/slab.py`: genera una losa horizontal por plano (excepto
  el primero) usando `slab_thickness` de `building.json`, sin z-fighting
  con el piso.
- Tests de existencia/surface_id/no-solapamiento geométrico de la losa.

## [v0.6] — 2026-07-02
### Added
- `engine/main.gd`: piso de seguridad temporal (`_spawn_test_ground`) para
  pruebas manuales, ya que la sala de ejemplo queda aislada sin exterior
  una vez que la puerta del Sprint 2 es atravesable.

## [v0.5] — 2026-07-02
### Added
- Segmentación de muros alrededor de `openings[]` en
  `pipeline/geometry/walls.py`: jambas + dintel + antepecho como mallas
  propias (nunca booleanos en runtime). Puertas atravesables
  (`sill_height = 0`), ventanas con antepecho.
- Tests de segmentación (`pipeline/tests/test_walls_openings.py`).
- `engine/sample_room.gltf` regenerado con la puerta/ventana reales del fixture.

## [v0.4] — 2026-07-02
### Added
- Pipeline: `pipeline/geometry/coords.py` (único mapeo X/Y-plano + altura →
  Y-up de Godot), mallas de muros sólidos y piso desde `walls[]`/`rooms[]`,
  `pipeline/compose/loader.py` (aplica `offset_xy`/`elevation`/`rotation_deg`
  de `building.json`), `python -m pipeline build` funcional.
- Engine: proyecto Godot 4.x, `player.tscn` (FPS, WASD + mouse look,
  colisión trimesh generada en runtime), `main.tscn` cargando el `.gltf`
  de la sala de ejemplo.
- `LICENSE` (MIT) — repo publicado como open source en
  `github.com/Felipe-Lara/planobal`.

## [v0.3] — 2026-07-02
### Changed
- `.gitattributes`: normaliza EOL a LF y marca binarios.

## [v0.2] — 2026-07-02
### Added
- Fase 0: esquemas pydantic (`Geometry`, `Building`, `PaintState`) y
  ejemplos en `pipeline/schema/`. `python -m pipeline validate` operativo.
  Contrato congelado como tag `contract-v1`.

## [v0.1] — 2026-07-02
### Added
- Estructura inicial del repo: `pipeline/`, `engine/`, `tools/`, subagentes
  (`.claude/agents/`).

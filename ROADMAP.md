# ROADMAP — Plano3D

Plan de ejecución por sprints. **MVP = Fases 0–4 con un solo plano de LV25.**
Estrategia: **corte vertical primero** — probar el handoff completo (JSON → .gltf →
caminar) con geometría a mano antes de escribir el parser de DXF.

Leyenda: ✅ hecho · 🔄 en curso · ⬜ pendiente · 🔲 futuro (post-MVP)

---

## Sprint 0 — Congelar el contrato  ✅
**Objetivo:** que las dos mitades tengan un contrato inmutable antes de escribir lógica.
No requiere DXF real.

- ✅ Estructura del repo (`pipeline/`, `engine/`, `tools/`, agentes, git).
- ✅ Esquemas pydantic: `Geometry`, `Building`, `PaintState` (`pipeline/schema/`).
- ✅ `geometry.json` a mano de una pieza simple + ejemplos de `building`/`paint_state`.
- ✅ CLI `python -m pipeline validate` operativo.
- ✅ Tests que congelan el contrato (`pipeline/tests/test_schema.py`).
- ✅ `ruff`/`black` sin quejas sobre `pipeline/` y `tools/`.
- ✅ Contrato etiquetado como `contract-v1` (git tag).

**Definition of Done:** `pytest` verde, `validate` reconoce los tres tipos, contrato taggeado.

---

## Sprint 1 — Slice vertical: geometry.json → .gltf → caminar  ✅
**Objetivo:** ver una habitación en Godot y caminar dentro, partiendo del JSON a mano.
Valida coordenadas, escala y handoff. **Agente: geometry-builder + godot-integrator.**
No requiere DXF real.

Pipeline (`pipeline/geometry/`):
- ✅ `coords.py` — mapeo X/Y-plano + altura → Y-up de Godot (único lugar que convierte ejes).
- ✅ Generar mallas de muros **sólidos** (sin aberturas todavía) desde `walls[]`.
- ✅ Generar piso desde `rooms[].polygon`.
- ✅ Exportar `.gltf` con **una mesh por superficie**, nombre = `surface_id`.
- ✅ `python -m pipeline build` funcional para un solo plano.
- ✅ Tests: asserts sobre nº de meshes, nombres y bounding box en metros.

Engine (`engine/`):
- ✅ Proyecto Godot 4.x + importación del `.gltf` (metros, Y arriba, sin re-escalar).
- ✅ `player.tscn` — `CharacterBody3D` FPS (WASD + mouse look) con colisiones desde las mallas.
- ✅ `main.tscn` que carga el `.gltf` de la habitación.

**Definition of Done:** se camina dentro de la habitación de ejemplo con escala correcta
(un muro mide ~2.5 m de alto), sin caerse por el piso.

---

## Sprint 2 — Aberturas: muros segmentados  ✅
**Objetivo:** puertas y ventanas reales, atravesables/mirables. **Agente: geometry-builder.**

- ✅ Segmentar muros alrededor de `openings[]`: jambas + dintel + antepecho como mallas propias.
- ✅ Puertas (`sill_height = 0`) atravesables; ventanas con antepecho.
- ✅ `surface_id` estable para cada segmento nuevo.
- ✅ Tests de segmentación (geometry.json mínimos de fixture).
- ✅ En Godot: verificar que se puede cruzar la puerta y mirar por la ventana.

**Definition of Done:** la habitación de ejemplo tiene una puerta cruzable y una ventana.

---

## Sprint 3 — Ingest real: DXF de LV25 → geometry.json  ⬜  ⏳ *bloqueado: falta DXF*
**Objetivo:** dejar de escribir geometría a mano. **Agente: dxf-parser.**
Se desarrolla contra el contrato ya congelado (paralelizable con Sprints 1–2).

- ⬜ `python tools/inspect_dxf.py <LV25.dxf>` y **documentar la convención de capas de Prolarq**.
- ⬜ `pipeline/ingest/` — leer DXF (ezdxf), DWG→DXF (odafc), normalizar `$INSUNITS` → metros.
- ⬜ `pipeline/detect/` — muros (polilíneas con ancho o pares de paralelas).
- ⬜ Detección de aberturas (bloques INSERT de puertas/ventanas).
- ⬜ Detección de recintos (polígonos cerrados o por capa).
- ⬜ Ids estables por hash de geometría.
- ⬜ Cada heurística con un test sobre un sample mínimo en `samples/`.

**Definition of Done:** `python -m pipeline ingest LV25.dxf` produce un `geometry.json`
que `validate` acepta y que, pasado por `build`, se camina en Godot.

---

## Sprint 4 — Composición multi-plano/multi-piso  ✅
**Objetivo:** varios planos en un edificio. **Agente: geometry-builder.**

- ✅ `pipeline/compose/` — aplicar `offset_xy`, `elevation`, `rotation_deg` a cada plano.
- ✅ Losas entre pisos con `slab_thickness` (evitar z-fighting techo/piso).
- ✅ Unir todos los planos en un solo `.gltf`.
- ✅ En Godot: soporte multi-nivel (subir de piso vía menú de pausa; sin escaleras físicas
  todavía — no está en el contrato — se resolvió con teletransporte por elevación).

**Definition of Done:** dos plantas apiladas caminables desde un `building.json`.

---

## Sprint 5 — Repintado + persistencia  ⬜
**Objetivo:** el corazón interactivo. **Agente: godot-integrator.**

- ⬜ Raycast desde la cámara para seleccionar superficie (por nombre de mesh = `surface_id`).
- ⬜ UI de selección de material (madera / cemento / pintura) con texturas CC0.
- ⬜ Asignación de material en runtime.
- ⬜ Leer/escribir `paint_state.json`; al cargar, ignorar `surface_id` inexistentes con warning.
- ⬜ Verificar que el pintado sobrevive a regenerar el `.gltf`.

**Definition of Done:** pintar un muro, cerrar, regenerar `.gltf`, reabrir y ver el muro pintado.

---

## 🔲 Futuro (post-MVP)

- 🔲 **Fase 5** — material-system avanzado (variantes, tiling por superficie) y furniture-system.
- 🔲 **Fase 6** — floorplan-vision: PDF → geometría, solo si algún día no existe el CAD.

---

## Notas de proceso

- **Tokens/modelos:** sesión principal en Sonnet; Opus solo en plan mode para arquitectura
  o cambios al contrato. `/clear` al cambiar de fase o de mitad (pipeline ↔ engine).
- **No pegar DXFs en el chat:** usar `tools/inspect_dxf.py` y pegar solo el resumen.
- **Orden recomendado ahora (sin DXF):** terminar Sprint 0 → Sprint 1 → Sprint 2.
  El Sprint 3 arranca en cuanto llegue el DXF de LV25.

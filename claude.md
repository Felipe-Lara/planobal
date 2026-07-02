CLAUDE.md — Plano3D

Contexto del proyecto para Claude Code. Se carga al inicio de cada sesión: mantenlo conciso.

Estado actual (actualizado 2026-07-02)


Sprints 0–4 del ROADMAP.md completos, commiteados y pusheados a
github.com/Felipe-Lara/planobal (repo público, MIT — es portafolio de
búsqueda laboral, cuidar que el historial de commits se vea prolijo).
Validado a mano en Godot 4.7: se camina en la sala de ejemplo, se cruza
la puerta, la ventana tiene antepecho, hay dos pisos con losa entre
ambos, y el menú de pausa (Esc) permite reiniciar posición y saltar de piso.

Próximo: Sprint 5 — repintado (raycast + selección de material +
paint_state.json). El menú ya tiene una sección "Materiales" placeholder
lista para eso. Sprint 3 (ingest DXF real) sigue bloqueado: falta el
DXF de LV25.

Detalle sprint por sprint, con checklist: ver ROADMAP.md.

Qué es

Pipeline en Python que convierte planos CAD (DXF/DWG de AutoCAD) en geometría 3D,


visor en Godot 4.x para caminar en primera persona y repintar superficies
(madera / cemento / pintura). Spec completa en README.md.


Arquitectura: dos mitades desacopladas


PIPELINE (Python) — pipeline/: DXF → geometry.json → malla → .gltf
ENGINE (Godot 4.x) — engine/: .gltf → walkthrough + repintado + composición


Se comunican solo por archivos (el contrato). No se conocen entre sí.

Formato de entrada


Entrada canónica: DXF (pedir a Prolarq "guardar como DXF 2018"). Se lee con ezdxf.
DWG: aceptado, se convierte automáticamente a DXF vía ODA File Converter
(ezdxf.addons.odafc) como paso previo al ingest.
PDF: fuera del MVP. Fase futura solo si algún día no existe el CAD.
Antes de escribir heurísticas nuevas, inspeccionar el archivo real con
python tools/inspect_dxf.py <plano.dxf> y preguntar la convención de capas de Prolarq.


El contrato (SAGRADO — no cambiar sin discutir en un issue)

Tres archivos. El pipeline escribe los dos primeros, el engine escribe el tercero.
Nadie escribe el archivo del otro.


geometry.json — por plano:

walls[]: {id, start, end, thickness, height} — ids estables (hash de geometría, no índice)
openings[]: {id, wall_id, type: door|window, offset_along_wall, width, height, sill_height}
rooms[]: {id, name?, polygon}
source: {file, insunits, generated_at} — trazabilidad y unidades



building.json — manifiesto de composición. Por plano:

offset_xy [x, y] → extensión horizontal (hacia el patio)
elevation → apilamiento vertical de pisos
rotation_deg → giro del plano
slab_thickness → espesor de losa entre pisos (evita z-fighting techo/piso)



paint_state.json — escrito por Godot: {surface_id → material}.
Sobrevive a regeneraciones del .gltf porque los ids son estables.


Esquemas (pydantic) y ejemplos en pipeline/schema/.
Validar con python -m pipeline validate <archivo.json>.

Convenciones


Unidades: SIEMPRE metros (convertir desde $INSUNITS del DXF en el ingest).
Coordenadas: plano en X/Y, altura en elevation. Godot: Y arriba.
El mapeo vive en pipeline/geometry/coords.py y no se rompe después.
Muros con aberturas: se generan segmentados (dintel/antepecho como mallas propias),
nunca booleanos en runtime.
Materiales: el .gltf sale "desnudo"; el nombre de cada mesh codifica su surface_id.
Godot asigna materiales en runtime leyendo paint_state.json.
Python: black + ruff, type hints. Tests en pipeline/tests/ usando samples/.
Godot 4.x, GDScript. Assets/texturas solo CC0 (Poly Haven, ambientCG).
Cada etapa entrega un archivo que la siguiente consume (handoff por archivos).


Comandos


Ingest: python -m pipeline ingest <plano.dxf|dwg> → geometry.json
Build: python -m pipeline build <building.json> → .gltf
Validar: python -m pipeline validate <archivo.json>
Inspección CAD: python tools/inspect_dxf.py <plano.dxf>
Tests: pytest
Engine: abrir engine/ en Godot 4.x


Plan hacia el MVP (corte vertical primero)


Fase 0 — Contrato: esquemas pydantic + un geometry.json escrito A MANO de una
pieza simple. Congela el contrato antes de escribir parsers.
Fase 1 — Slice vertical: geometry.json manual → geometry-builder → .gltf →
caminar en Godot. Valida coordenadas, escala y handoff en una semana.
Fase 2 — Ingest real: DXF de LV25 → geometry.json. Se desarrolla contra el
contrato ya congelado (paralelizable con Fase 1).
Fase 3 — Composición: building.json multi-plano/multi-piso.
Fase 4 — Repintado: raycast + paint_state.json.
(Futuras) Fase 5: material-system avanzado, furniture-system. Fase 6: floorplan-vision (PDF).


MVP = Fases 0–4 con un solo plano de LV25.

Subagentes (.claude/agents/)


dxf-parser → DXF/DWG → geometry.json (trabaja en pipeline/ingest, pipeline/detect)
geometry-builder → geometry.json / building.json → .gltf (pipeline/geometry, pipeline/compose)
godot-integrator → todo engine/ (Godot, FPS, raycast, repintado, multi-nivel, UI)


La sesión principal orquesta: delega a cada subagente y une resultados.
No hay agente orquestador.

Uso eficiente de modelos/tokens


Sesión principal: Sonnet (daily driver). Cambiar a Opus solo en plan mode
para decisiones de arquitectura o cambios al contrato; volver a Sonnet para implementar.
Subagentes: modelo declarado en su frontmatter (Sonnet los tres; el trabajo
mecánico/repetitivo se puede bajar a Haiku por tarea).
/clear al cambiar de fase o de mitad (pipeline ↔ engine). No arrastrar contexto muerto.
No pegar DXFs en el chat: usar tools/inspect_dxf.py y pegar solo su resumen.
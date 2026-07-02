"""geometry.json Wall (+ Openings) -> mallas 3D.

Sprint 1: muros macizos, una caja por muro.
Sprint 2: muros con aberturas se generan SEGMENTADOS (jambas laterales +
dintel + antepecho como mallas propias, calculadas analíticamente por
posición a lo largo del eje del muro). Nunca se usan operaciones booleanas
en runtime para recortar el hueco: el hueco simplemente no genera geometría.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import trimesh

from pipeline.geometry.coords import plane_to_godot
from pipeline.schema import Opening, Room, Wall

# Tolerancia (m) por debajo de la cual un segmento se considera degenerado
# (largo o alto ~0) y no se genera, para evitar cajas de grosor cero cuando
# una abertura toca exactamente el borde del muro o el techo/piso.
_EPS = 1e-6


@dataclass(frozen=True)
class _Segment:
    """Un tramo sólido de muro en coordenadas locales al eje del muro.

    `s0`/`s1`: rango a lo largo del muro, medido desde `wall.start` (m).
    `z0`/`z1`: rango vertical, desde el piso (m).
    """

    surface_id: str
    s0: float
    s1: float
    z0: float
    z1: float


def _build_segment_mesh(
    wall: Wall,
    seg: _Segment,
    thickness: float | None = None,
    y_offset: float = 0.0,
    surface_id: str | None = None,
) -> trimesh.Trimesh:
    """Construye la caja sólida de un `_Segment` y la mapea a Godot Y-up.

    `thickness`/`y_offset` permiten construir mitades delgadas del muro
    (ver `_build_wall_face_meshes`): `thickness` es el espesor de la caja
    (por defecto `wall.thickness` completo) y `y_offset` es un desplazamiento
    en el eje perpendicular al muro, en espacio local previo a la rotación
    (mismo eje que usa el ángulo del muro: el local y-axis del box, tras
    rotar `angle` grados alrededor de Z, coincide con la normal en planta
    `(-uy, ux)` del muro).
    """
    (sx, sy), (ex, ey) = wall.start, wall.end
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    angle = math.atan2(dy, dx)
    mid_x, mid_y = (sx + ex) / 2.0, (sy + ey) / 2.0

    box_thickness = thickness if thickness is not None else wall.thickness
    seg_length = seg.s1 - seg.s0
    seg_height = seg.z1 - seg.z0
    local_x = (seg.s0 + seg.s1) / 2.0 - length / 2.0
    local_z = (seg.z0 + seg.z1) / 2.0

    box = trimesh.creation.box(extents=(seg_length, box_thickness, seg_height))
    box.apply_translation((local_x, y_offset, local_z))
    rotate = trimesh.transformations.rotation_matrix(angle, [0.0, 0.0, 1.0])
    translate = trimesh.transformations.translation_matrix((mid_x, mid_y, 0.0))
    box.apply_transform(translate @ rotate)

    godot_vertices = np.array([plane_to_godot(x, y, z) for x, y, z in box.vertices])
    mesh = trimesh.Trimesh(vertices=godot_vertices, faces=box.faces, process=False)
    final_id = surface_id if surface_id is not None else seg.surface_id
    mesh.metadata["surface_id"] = final_id
    mesh.metadata["name"] = final_id
    return mesh


def _room_centroid(room: Room) -> tuple[float, float]:
    """Centroide simple (promedio de vértices) del polígono de un room.

    Simplificación razonable para el MVP: no es el centroide ponderado por
    área (que sería exacto para polígonos no convexos/irregulares), pero
    para los rectángulos del fixture actual da el mismo resultado y evita
    traer una fórmula de shoelace-centroid solo para esto.
    """
    xs = [p[0] for p in room.polygon]
    ys = [p[1] for p in room.polygon]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _closest_room(wall: Wall, rooms: list[Room]) -> Room | None:
    """Room cuyo centroide está más cerca del punto medio del muro.

    No hay relación explícita room<->wall en el contrato hoy: se infiere por
    proximidad. Con un único room (fixture actual) es trivial, pero queda
    general para cuando haya más de uno por plano.
    """
    if not rooms:
        return None
    (sx, sy), (ex, ey) = wall.start, wall.end
    mid_x, mid_y = (sx + ex) / 2.0, (sy + ey) / 2.0
    closest = min(
        rooms,
        key=lambda r: math.hypot(_room_centroid(r)[0] - mid_x, _room_centroid(r)[1] - mid_y),
    )
    return closest


def _interior_sign(wall: Wall, room: Room) -> float:
    """+1.0 si la normal `(-uy, ux)` del muro apunta hacia el centroide del
    room (esa mitad es la cara interior); -1.0 si apunta al lado contrario."""
    (sx, sy), (ex, ey) = wall.start, wall.end
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux

    mid_x, mid_y = (sx + ex) / 2.0, (sy + ey) / 2.0
    cx, cy = _room_centroid(room)
    dot = (cx - mid_x) * nx + (cy - mid_y) * ny
    return 1.0 if dot >= 0.0 else -1.0


def _build_wall_face_meshes(wall: Wall, seg: _Segment, rooms: list[Room]) -> list[trimesh.Trimesh]:
    """Divide un `_Segment` en sus dos mitades delgadas (cara interior /
    cara exterior), o devuelve la caja completa sin dividir si no se pudo
    inferir a qué room pertenece el muro (caso borde: geometry sin rooms)."""
    room = _closest_room(wall, rooms)
    if room is None:
        print(
            f"[walls] advertencia: no se encontró room cercano para muro "
            f"{wall.id!r}; se genera la caja completa sin separar caras."
        )
        return [_build_segment_mesh(wall, seg)]

    sign = _interior_sign(wall, room)
    half_thickness = wall.thickness / 2.0
    quarter = wall.thickness / 4.0

    interior = _build_segment_mesh(
        wall,
        seg,
        thickness=half_thickness,
        y_offset=sign * quarter,
        surface_id=f"{seg.surface_id}.cara_interior",
    )
    exterior = _build_segment_mesh(
        wall,
        seg,
        thickness=half_thickness,
        y_offset=-sign * quarter,
        surface_id=f"{seg.surface_id}.cara_exterior",
    )
    return [interior, exterior]


def _wall_length(wall: Wall) -> float:
    (sx, sy), (ex, ey) = wall.start, wall.end
    return math.hypot(ex - sx, ey - sy)


def _plan_segments(wall: Wall, openings: list[Opening]) -> list[_Segment]:
    """Calcula los segmentos sólidos de un muro dadas sus aberturas.

    Las aberturas se ordenan por `offset_along_wall` (determinístico). Entre
    aberturas consecutivas (y en los extremos del muro) se generan jambas;
    encima de cada abertura un dintel (si sobra altura hasta el techo); y
    debajo, un antepecho solo si `sill_height > 0`.
    """
    length = _wall_length(wall)
    ordered = sorted(openings, key=lambda o: o.offset_along_wall)

    segments: list[_Segment] = []

    # Jambas: tramos sólidos de piso a techo entre huecos consecutivos.
    cursor = 0.0
    for i, opening in enumerate(ordered):
        jamb_end = opening.offset_along_wall
        if jamb_end - cursor > _EPS:
            segments.append(_Segment(f"{wall.id}_jamb_{i}", cursor, jamb_end, 0.0, wall.height))
        cursor = opening.offset_along_wall + opening.width
    if length - cursor > _EPS:
        segments.append(
            _Segment(f"{wall.id}_jamb_{len(ordered)}", cursor, length, 0.0, wall.height)
        )

    # Dintel y antepecho por abertura, acotados al ancho del hueco.
    for opening in ordered:
        s0 = opening.offset_along_wall
        s1 = opening.offset_along_wall + opening.width
        opening_top = opening.sill_height + opening.height

        if wall.height - opening_top > _EPS:
            segments.append(
                _Segment(f"{wall.id}_lintel_{opening.id}", s0, s1, opening_top, wall.height)
            )

        if opening.sill_height > _EPS:
            segments.append(
                _Segment(f"{wall.id}_sill_{opening.id}", s0, s1, 0.0, opening.sill_height)
            )

    return segments


def build_wall_mesh(wall: Wall) -> trimesh.Trimesh:
    """Construye una caja sólida para un muro sin aberturas.

    Se mantiene para compatibilidad (Sprint 1): un solo box, `surface_id =
    wall.id`. Para muros con aberturas usar `build_wall_meshes`.
    """
    length = _wall_length(wall)
    if length <= 0:
        raise ValueError(f"muro {wall.id!r} tiene longitud cero (start == end)")
    seg = _Segment(wall.id, 0.0, length, 0.0, wall.height)
    return _build_segment_mesh(wall, seg)


def build_wall_meshes(
    wall: Wall,
    openings: list[Opening] | None = None,
    rooms: list[Room] | None = None,
) -> list[trimesh.Trimesh]:
    """Construye las mallas sólidas de un muro, segmentado si tiene aberturas
    y separadas en cara interior/exterior (mitades delgadas coplanares con
    el eje del muro, ver `_build_wall_face_meshes`).

    Sin aberturas: un solo `_Segment` de piso a techo, dividido en 2 mallas
    (`{wall.id}.cara_interior` / `{wall.id}.cara_exterior`). Con aberturas:
    jambas + dinteles + antepechos (ver `_plan_segments`), cada uno también
    dividido en sus 2 caras; el hueco de cada abertura (y el rango vertical
    bajo su sill, si aplica) no genera geometría.

    `rooms` se usa para inferir qué lado de cada muro es "interior" (el más
    cercano al centroide del room); si no se pasa (o está vacío) se genera
    la caja completa sin dividir, con una advertencia.
    """
    length = _wall_length(wall)
    if length <= 0:
        raise ValueError(f"muro {wall.id!r} tiene longitud cero (start == end)")

    rooms = rooms or []
    if not openings:
        segments = [_Segment(wall.id, 0.0, length, 0.0, wall.height)]
    else:
        segments = _plan_segments(wall, openings)

    meshes: list[trimesh.Trimesh] = []
    for seg in segments:
        meshes.extend(_build_wall_face_meshes(wall, seg, rooms))
    return meshes

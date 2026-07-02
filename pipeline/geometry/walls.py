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
from pipeline.schema import Opening, Wall

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


def _build_segment_mesh(wall: Wall, seg: _Segment) -> trimesh.Trimesh:
    """Construye la caja sólida de un `_Segment` y la mapea a Godot Y-up."""
    (sx, sy), (ex, ey) = wall.start, wall.end
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    angle = math.atan2(dy, dx)
    mid_x, mid_y = (sx + ex) / 2.0, (sy + ey) / 2.0

    seg_length = seg.s1 - seg.s0
    seg_height = seg.z1 - seg.z0
    local_x = (seg.s0 + seg.s1) / 2.0 - length / 2.0
    local_z = (seg.z0 + seg.z1) / 2.0

    box = trimesh.creation.box(extents=(seg_length, wall.thickness, seg_height))
    box.apply_translation((local_x, 0.0, local_z))
    rotate = trimesh.transformations.rotation_matrix(angle, [0.0, 0.0, 1.0])
    translate = trimesh.transformations.translation_matrix((mid_x, mid_y, 0.0))
    box.apply_transform(translate @ rotate)

    godot_vertices = np.array([plane_to_godot(x, y, z) for x, y, z in box.vertices])
    mesh = trimesh.Trimesh(vertices=godot_vertices, faces=box.faces, process=False)
    mesh.metadata["surface_id"] = seg.surface_id
    mesh.metadata["name"] = seg.surface_id
    return mesh


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


def build_wall_meshes(wall: Wall, openings: list[Opening] | None = None) -> list[trimesh.Trimesh]:
    """Construye las mallas sólidas de un muro, segmentado si tiene aberturas.

    Sin aberturas: una sola malla (`surface_id = wall.id`), igual que Sprint 1.
    Con aberturas: jambas + dinteles + antepechos (ver `_plan_segments`); el
    hueco de cada abertura (y el rango vertical bajo su sill, si aplica) no
    genera geometría.
    """
    length = _wall_length(wall)
    if length <= 0:
        raise ValueError(f"muro {wall.id!r} tiene longitud cero (start == end)")

    if not openings:
        return [build_wall_mesh(wall)]

    segments = _plan_segments(wall, openings)
    return [_build_segment_mesh(wall, seg) for seg in segments]

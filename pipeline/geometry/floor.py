"""geometry.json Room -> malla de piso plana (polígono triangulado)."""

from __future__ import annotations

import numpy as np
import trimesh
from trimesh.path.polygons import Polygon

from pipeline.geometry.coords import plane_to_godot
from pipeline.schema import Room

# Espesor nominal de la losa de piso: evita una malla de grosor cero
# (degenerada) mientras la composición de losas reales llega en Sprint 4.
_FLOOR_THICKNESS = 0.05


def _build_room_slab(room: Room, z_bottom: float, surface_id: str) -> trimesh.Trimesh:
    """Extruye `room.polygon` en una losa delgada entre `z_bottom` y
    `z_bottom + _FLOOR_THICKNESS` (espacio local del plano, antes del mapeo
    Y-up), y la mapea a Godot. Compartido por piso y techo."""
    polygon = Polygon(room.polygon)
    if not polygon.is_valid or polygon.area == 0:
        raise ValueError(f"room {room.id!r} tiene un polígono inválido o degenerado")

    mesh = trimesh.creation.extrude_polygon(polygon, height=_FLOOR_THICKNESS)
    # extrude_polygon deja el sólido entre z=0 y z=_FLOOR_THICKNESS; lo
    # trasladamos para que ocupe [z_bottom, z_bottom + _FLOOR_THICKNESS].
    vertices = mesh.vertices.copy()
    vertices[:, 2] += z_bottom
    godot_vertices = np.array([plane_to_godot(x, y, z) for x, y, z in vertices])

    slab = trimesh.Trimesh(vertices=godot_vertices, faces=mesh.faces, process=True)
    slab.fix_normals()
    slab.metadata["surface_id"] = surface_id
    slab.metadata["name"] = surface_id
    return slab


def build_floor_mesh(room: Room) -> trimesh.Trimesh:
    """Construye una malla plana (con espesor mínimo) desde `room.polygon`.

    El polígono 2D (X/Y del plano) se triangula y se extruye una pequeña
    altura hacia abajo desde z=0 para obtener un sólido válido, con la cara
    superior en z=0 (nivel de piso). `surface_id = f"{room.id}.piso"`
    (contrato con el engine: separa piso de techo como superficies
    repintables distintas, ver paint_state.example.json).
    """
    return _build_room_slab(room, z_bottom=-_FLOOR_THICKNESS, surface_id=f"{room.id}.piso")


def build_ceiling_mesh(room: Room, ceiling_height: float) -> trimesh.Trimesh:
    """Construye la malla de techo de un room, misma extrusión delgada que
    el piso pero con la cara inferior apoyada en `ceiling_height` (altura,
    en metros, hasta donde llega el muro más alto que delimita el room —
    ver `build.py`, que hoy usa una simplificación: el máximo entre TODOS
    los muros de la geometry, no solo los que delimitan este room).
    `surface_id = f"{room.id}.techo"`.
    """
    return _build_room_slab(room, z_bottom=ceiling_height, surface_id=f"{room.id}.techo")

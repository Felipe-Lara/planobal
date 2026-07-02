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


def build_floor_mesh(room: Room) -> trimesh.Trimesh:
    """Construye una malla plana (con espesor mínimo) desde `room.polygon`.

    El polígono 2D (X/Y del plano) se triangula y se extruye una pequeña
    altura hacia abajo desde z=0 para obtener un sólido válido. El nombre de
    la malla es `room.id` (surface_id: contrato con el engine).
    """
    polygon = Polygon(room.polygon)
    if not polygon.is_valid or polygon.area == 0:
        raise ValueError(f"room {room.id!r} tiene un polígono inválido o degenerado")

    mesh = trimesh.creation.extrude_polygon(polygon, height=_FLOOR_THICKNESS)
    # extrude_polygon deja el sólido entre z=0 y z=height (plano X/Y, Z "arriba
    # del CAD" temporal); lo bajamos para que la cara superior quede en z=0
    # (nivel de piso) y luego mapeamos cada vértice al espacio Y-up de Godot.
    vertices = mesh.vertices.copy()
    vertices[:, 2] -= _FLOOR_THICKNESS
    godot_vertices = np.array([plane_to_godot(x, y, z) for x, y, z in vertices])

    floor = trimesh.Trimesh(vertices=godot_vertices, faces=mesh.faces, process=True)
    floor.fix_normals()
    floor.metadata["surface_id"] = room.id
    floor.metadata["name"] = room.id
    return floor

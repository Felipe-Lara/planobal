"""geometry.json Wall -> malla 3D (caja sólida).

Sprint 1: muros macizos, sin segmentación de aberturas (eso llega en Sprint 2:
dintel/antepecho/jambas como mallas propias, nunca booleanos en runtime).
"""

from __future__ import annotations

import math

import numpy as np
import trimesh

from pipeline.geometry.coords import plane_to_godot
from pipeline.schema import Wall


def build_wall_mesh(wall: Wall) -> trimesh.Trimesh:
    """Construye una caja sólida para un muro, centrada en su línea de eje.

    El muro se extiende de `wall.start` a `wall.end` en el plano X/Y, con
    espesor `wall.thickness` perpendicular a esa línea, desde el piso
    (z=0) hasta `wall.height`. El nombre de la malla es `wall.id`
    (surface_id: contrato con el engine).

    Se construye una caja unitaria (`trimesh.creation.box`, con normales
    salientes ya correctas) en "espacio de plano" y se posiciona con
    traslaciones/rotaciones alrededor del eje Z (vertical del CAD, aún sin
    mapear). Recién al final se convierte cada vértice a Y-up de Godot con
    `plane_to_godot`; como ese mapeo es una rotación propia (determinante
    +1), preserva la orientación de las caras (no hay que recalcular
    normales).
    """
    (sx, sy), (ex, ey) = wall.start, wall.end
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    if length <= 0:
        raise ValueError(f"muro {wall.id!r} tiene longitud cero (start == end)")

    angle = math.atan2(dy, dx)
    mid_x, mid_y = (sx + ex) / 2.0, (sy + ey) / 2.0

    box = trimesh.creation.box(extents=(length, wall.thickness, wall.height))
    # El piso queda en z=0..height en vez de -height/2..height/2.
    box.apply_translation((0.0, 0.0, wall.height / 2.0))
    rotate = trimesh.transformations.rotation_matrix(angle, [0.0, 0.0, 1.0])
    translate = trimesh.transformations.translation_matrix((mid_x, mid_y, 0.0))
    box.apply_transform(translate @ rotate)

    godot_vertices = np.array([plane_to_godot(x, y, z) for x, y, z in box.vertices])
    mesh = trimesh.Trimesh(vertices=godot_vertices, faces=box.faces, process=False)
    mesh.metadata["surface_id"] = wall.id
    mesh.metadata["name"] = wall.id
    return mesh

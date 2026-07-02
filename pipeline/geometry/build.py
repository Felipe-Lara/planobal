"""geometry.json -> trimesh.Scene con un nodo de malla por surface_id.

Orquesta walls.py + floor.py. No aplica materiales (el .gltf sale
"desnudo"; Godot los asigna en runtime leyendo paint_state.json).
"""

from __future__ import annotations

import json
from pathlib import Path

import trimesh

from pipeline.geometry.floor import build_ceiling_mesh, build_floor_mesh
from pipeline.geometry.walls import build_wall_meshes
from pipeline.schema import Geometry


def build_geometry_scene(geometry: Geometry) -> trimesh.Scene:
    """Construye un trimesh.Scene con un nodo por muro (o por segmento de
    muro, si tiene aberturas, cada uno dividido en cara interior/exterior)
    y por recinto (piso + techo).

    El nombre de cada nodo/malla es su surface_id (`{wall_segment_id}.cara_
    interior`/`.cara_exterior`, `{room.id}.piso`/`.techo`): es el contrato
    de repintado con el engine (ver paint_state.example.json).
    """
    scene = trimesh.Scene()
    for wall in geometry.walls:
        wall_openings = [o for o in geometry.openings if o.wall_id == wall.id]
        for mesh in build_wall_meshes(wall, wall_openings, geometry.rooms):
            surface_id = mesh.metadata["surface_id"]
            scene.add_geometry(mesh, node_name=surface_id, geom_name=surface_id)

    # Altura de techo: simplificación para este sprint. El contrato no
    # relaciona explícitamente rooms<->walls, así que en vez de resolver qué
    # muros delimitan cada room usamos la altura máxima entre TODOS los
    # muros de la geometry. Con un solo room (fixture actual) es exacto; con
    # varios rooms de distinta altura de muro puede sobrestimar el techo de
    # los más bajos.
    ceiling_height = max((w.height for w in geometry.walls), default=0.0)

    for room in geometry.rooms:
        floor_mesh = build_floor_mesh(room)
        scene.add_geometry(
            floor_mesh,
            node_name=floor_mesh.metadata["surface_id"],
            geom_name=floor_mesh.metadata["surface_id"],
        )
        ceiling_mesh = build_ceiling_mesh(room, ceiling_height)
        scene.add_geometry(
            ceiling_mesh,
            node_name=ceiling_mesh.metadata["surface_id"],
            geom_name=ceiling_mesh.metadata["surface_id"],
        )
    return scene


def load_geometry(path: Path) -> Geometry:
    """Carga y valida un geometry.json contra el esquema del contrato."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return Geometry.model_validate(data)


def build_geometry_scene_from_file(path: Path) -> trimesh.Scene:
    return build_geometry_scene(load_geometry(path))

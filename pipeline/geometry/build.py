"""geometry.json -> trimesh.Scene con un nodo de malla por surface_id.

Orquesta walls.py + floor.py. No aplica materiales (el .gltf sale
"desnudo"; Godot los asigna en runtime leyendo paint_state.json).
"""

from __future__ import annotations

import json
from pathlib import Path

import trimesh

from pipeline.geometry.floor import build_floor_mesh
from pipeline.geometry.walls import build_wall_meshes
from pipeline.schema import Geometry


def build_geometry_scene(geometry: Geometry) -> trimesh.Scene:
    """Construye un trimesh.Scene con un nodo por muro (o por segmento de
    muro, si tiene aberturas) y por recinto.

    El nombre de cada nodo/malla es su surface_id (wall.id / segmento /
    room.id): es el contrato de repintado con el engine.
    """
    scene = trimesh.Scene()
    for wall in geometry.walls:
        wall_openings = [o for o in geometry.openings if o.wall_id == wall.id]
        for mesh in build_wall_meshes(wall, wall_openings):
            surface_id = mesh.metadata["surface_id"]
            scene.add_geometry(mesh, node_name=surface_id, geom_name=surface_id)
    for room in geometry.rooms:
        mesh = build_floor_mesh(room)
        scene.add_geometry(mesh, node_name=room.id, geom_name=room.id)
    return scene


def load_geometry(path: Path) -> Geometry:
    """Carga y valida un geometry.json contra el esquema del contrato."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return Geometry.model_validate(data)


def build_geometry_scene_from_file(path: Path) -> trimesh.Scene:
    return build_geometry_scene(load_geometry(path))

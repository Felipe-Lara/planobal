"""geometry.json -> trimesh.Scene con un nodo de malla por surface_id.

Orquesta walls.py + floor.py. No aplica materiales (el .gltf sale
"desnudo"; Godot los asigna en runtime leyendo paint_state.json).
"""

from __future__ import annotations

import json
from pathlib import Path

import trimesh

from pipeline.geometry.floor import build_floor_mesh
from pipeline.geometry.walls import build_wall_mesh
from pipeline.schema import Geometry


def build_geometry_scene(geometry: Geometry) -> trimesh.Scene:
    """Construye un trimesh.Scene con un nodo por muro y por recinto.

    El nombre de cada nodo/malla es su surface_id (wall.id / room.id):
    es el contrato de repintado con el engine.
    """
    scene = trimesh.Scene()
    for wall in geometry.walls:
        mesh = build_wall_mesh(wall)
        scene.add_geometry(mesh, node_name=wall.id, geom_name=wall.id)
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

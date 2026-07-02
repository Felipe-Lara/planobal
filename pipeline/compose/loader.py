"""building.json -> trimesh.Scene compuesto (todos los planos, transformados).

Sprint 1/3 (parcial): aplica offset_xy, elevation y rotation_deg por plano.
NO genera losas (slab_thickness) todavía -- eso llega en Sprint 4; si el
campo está presente en el manifiesto simplemente se ignora, no rompe nada.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import trimesh

from pipeline.geometry.build import build_geometry_scene, load_geometry
from pipeline.geometry.coords import plane_to_godot
from pipeline.schema import Building, Plano


def _plano_transform(plano: Plano) -> np.ndarray:
    """Matriz 4x4 en espacio Godot (Y-up) para un plano.

    Se aplica DESPUÉS del mapeo de coords.py, en espacio Godot: primero gira
    alrededor del eje vertical (Y de Godot) por `rotation_deg`, luego
    traslada. La traslación combina `offset_xy` (horizontal, en el plano
    X/Y original) y `elevation` (apilamiento vertical) usando el mismo
    `plane_to_godot` para mantener un único lugar de conversión de ejes.
    """
    rotation = trimesh.transformations.rotation_matrix(
        math.radians(plano.rotation_deg), [0.0, 1.0, 0.0]
    )
    tx, ty, tz = plane_to_godot(plano.offset_xy[0], plano.offset_xy[1], plano.elevation)
    translation = trimesh.transformations.translation_matrix([tx, ty, tz])
    return translation @ rotation


def build_building_scene(building: Building, base_dir: Path) -> trimesh.Scene:
    """Compone todos los planos de un Building en un único trimesh.Scene.

    Cada malla conserva su surface_id original en `mesh.metadata["surface_id"]`
    (el contrato de repintado). Como varios planos pueden reusar el mismo
    geometry.json (p.ej. pisos repetidos), el *nombre de nodo* en la escena
    compuesta se prefija con el índice del plano (`p{i}_<surface_id>`) para
    evitar colisiones; el surface_id real vive en los metadatos de la malla.
    """
    merged = trimesh.Scene()
    for index, plano in enumerate(building.planos):
        geometry_path = (base_dir / plano.geometry).resolve()
        geometry = load_geometry(geometry_path)
        sub_scene = build_geometry_scene(geometry)
        transform = _plano_transform(plano)

        for node_name, mesh in sub_scene.geometry.items():
            transformed = mesh.copy()
            transformed.apply_transform(transform)
            surface_id = mesh.metadata.get("surface_id", node_name)
            transformed.metadata["surface_id"] = surface_id
            transformed.metadata["plano_index"] = index
            merged.add_geometry(
                transformed,
                node_name=f"p{index}_{surface_id}",
                geom_name=f"p{index}_{surface_id}",
            )
    return merged


def load_building(path: Path) -> Building:
    """Carga y valida un building.json contra el esquema del contrato."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return Building.model_validate(data)


def build_building_scene_from_file(path: Path) -> trimesh.Scene:
    building = load_building(path)
    return build_building_scene(building, base_dir=path.parent)

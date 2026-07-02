"""Esquemas pydantic del contrato de Plano3D.

El contrato son tres archivos JSON (ver CLAUDE.md):
- geometry.json    -> Geometry   (lo escribe el pipeline)
- building.json    -> Building   (lo escribe el pipeline)
- paint_state.json -> PaintState (lo escribe el engine/Godot)
"""

from __future__ import annotations

from pipeline.schema.building import Building, Plano
from pipeline.schema.geometry import Geometry, Opening, Room, Source, Wall
from pipeline.schema.paint_state import Material, PaintState

__all__ = [
    "Geometry",
    "Wall",
    "Opening",
    "Room",
    "Source",
    "Building",
    "Plano",
    "PaintState",
    "Material",
]

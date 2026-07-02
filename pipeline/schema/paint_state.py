"""Esquema de paint_state.json — estado de repintado, escrito por el ENGINE.

SAGRADO: no cambiar sin discutir en un issue (ver CLAUDE.md).
Mapea surface_id -> material. El surface_id es el nombre de la mesh en el .gltf
(lo genera geometry-builder); sobrevive a regeneraciones porque los ids son estables.
Es el ÚNICO archivo que Godot escribe.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import RootModel


class Material(StrEnum):
    """Materiales repintables del MVP. Extensible en fases futuras."""

    MADERA = "madera"
    CEMENTO = "cemento"
    PINTURA = "pintura"


class PaintState(RootModel[dict[str, Material]]):
    """paint_state.json: diccionario surface_id -> material."""

    root: dict[str, Material]

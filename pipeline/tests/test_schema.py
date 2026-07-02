"""Fase 0 — congela el contrato: los ejemplos a mano deben validar siempre.

Estos tests son la red de seguridad del contrato. Si alguien cambia un esquema
de forma incompatible, aquí se rompe antes de tocar parsers o el engine.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.schema import Building, Geometry, Material, PaintState

EXAMPLES = Path(__file__).resolve().parents[1] / "schema" / "examples"


def _load(name: str):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_geometry_example_valida():
    geo = Geometry.model_validate(_load("geometry.example.json"))
    assert len(geo.walls) == 4
    assert len(geo.openings) == 2
    assert len(geo.rooms) == 1
    # Toda abertura referencia un muro existente.
    wall_ids = {w.id for w in geo.walls}
    assert all(op.wall_id in wall_ids for op in geo.openings)


def test_building_example_valida():
    bld = Building.model_validate(_load("building.example.json"))
    assert len(bld.planos) == 2
    assert bld.planos[1].elevation > bld.planos[0].elevation  # se apila hacia arriba


def test_paint_state_example_valida():
    state = PaintState.model_validate(_load("paint_state.example.json"))
    assert all(isinstance(m, Material) for m in state.root.values())


def test_geometry_rechaza_thickness_no_positivo():
    data = _load("geometry.example.json")
    data["walls"][0]["thickness"] = 0
    with pytest.raises(ValueError):
        Geometry.model_validate(data)


def test_paint_state_rechaza_material_desconocido():
    with pytest.raises(ValueError):
        PaintState.model_validate({"w_sur.cara_interior": "oro"})

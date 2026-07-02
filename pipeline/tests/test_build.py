"""Tests de pipeline/geometry y pipeline/compose contra los fixtures del contrato."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.compose.loader import build_building_scene_from_file
from pipeline.geometry.build import build_geometry_scene_from_file
from pipeline.geometry.coords import plane_to_godot

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "schema" / "examples"
GEOMETRY_EXAMPLE = EXAMPLES_DIR / "geometry.example.json"
BUILDING_EXAMPLE = EXAMPLES_DIR / "building.example.json"


def test_plane_to_godot_mapping():
    assert plane_to_godot(1.0, 2.0, 3.0) == (1.0, 3.0, -2.0)
    assert plane_to_godot(0.0, 0.0, 0.0) == (0.0, 0.0, 0.0)
    assert plane_to_godot(-1.5, 4.0, 2.5) == (-1.5, 2.5, -4.0)


def test_geometry_scene_has_one_mesh_per_surface():
    scene = build_geometry_scene_from_file(GEOMETRY_EXAMPLE)
    # 4 muros + 1 recinto = 5 mallas.
    assert len(scene.geometry) == 5

    expected_ids = {"w_sur", "w_este", "w_norte", "w_oeste", "room_sala"}
    actual_ids = {mesh.metadata["surface_id"] for mesh in scene.geometry.values()}
    assert actual_ids == expected_ids


def test_geometry_scene_bounding_box_is_sane_meters():
    scene = build_geometry_scene_from_file(GEOMETRY_EXAMPLE)
    extents = scene.bounding_box.extents
    # Habitación de ~4m x 3m (más medio espesor de muro, 0.15m, en cada
    # borde), muros de 2.5m de alto (mapeados al eje Y en Godot).
    assert 4.0 <= extents[0] <= 4.2  # X: ~4m + espesor de muro
    assert 2.4 <= extents[1] <= 2.6  # Y (Godot): altura de muros, 2.5m
    assert 3.0 <= extents[2] <= 3.2  # Z (Godot): ~3m + espesor de muro


@pytest.fixture
def building_dir(tmp_path: Path) -> Path:
    """Copia los fixtures a un directorio temporal donde `geometry` de
    building.example.json ("geometry.json") resuelve correctamente."""
    geometry_target = tmp_path / "geometry.json"
    geometry_target.write_text(GEOMETRY_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    building_target = tmp_path / "building.json"
    building_target.write_text(BUILDING_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    return building_target


def test_building_scene_merges_planos_with_prefixed_node_names(building_dir: Path):
    scene = build_building_scene_from_file(building_dir)
    # 2 planos x 5 mallas cada uno = 10 nodos.
    assert len(scene.geometry) == 10

    node_names = set(scene.geometry.keys())
    assert "p0_w_sur" in node_names
    assert "p1_w_sur" in node_names

    surface_ids = {mesh.metadata["surface_id"] for mesh in scene.geometry.values()}
    assert surface_ids == {"w_sur", "w_este", "w_norte", "w_oeste", "room_sala"}


def test_building_scene_bounding_box_reflects_two_floors_elevation(building_dir: Path):
    scene = build_building_scene_from_file(building_dir)
    extents = scene.bounding_box.extents
    bounds = scene.bounding_box.bounds
    # Segundo plano en elevation=2.7m; con muros de 2.5m de alto, la altura
    # total del edificio compuesto debe superar 2.7 + 2.5 = 5.2m.
    height = bounds[1][1] - bounds[0][1]
    assert height >= 5.2
    # El footprint horizontal (X/Z en Godot) sigue siendo ~4m x 3m, más el
    # espesor de muro (mismo offset_xy=0,0 en ambos planos).
    assert 4.0 <= extents[0] <= 4.2
    assert 3.0 <= extents[2] <= 3.2

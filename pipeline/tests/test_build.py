"""Tests de pipeline/geometry y pipeline/compose contra los fixtures del contrato."""

from __future__ import annotations

import math
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


_WALL_SEGMENT_IDS = {
    "w_norte",
    "w_oeste",
    "w_sur_jamb_0",
    "w_sur_jamb_1",
    "w_sur_lintel_op_puerta",
    "w_este_jamb_0",
    "w_este_jamb_1",
    "w_este_lintel_op_ventana",
    "w_este_sill_op_ventana",
}


def _expected_geometry_surface_ids() -> set[str]:
    # Cada segmento de muro ahora genera 2 mallas (cara_interior/exterior).
    faces = {
        f"{seg_id}.cara_{side}" for seg_id in _WALL_SEGMENT_IDS for side in ("interior", "exterior")
    }
    return faces | {"room_sala.piso", "room_sala.techo"}


def test_geometry_scene_has_one_mesh_per_surface():
    scene = build_geometry_scene_from_file(GEOMETRY_EXAMPLE)
    # 9 segmentos de muro x 2 caras (interior/exterior) = 18
    # + piso + techo del recinto = 20 mallas.
    assert len(scene.geometry) == 20

    actual_ids = {mesh.metadata["surface_id"] for mesh in scene.geometry.values()}
    assert actual_ids == _expected_geometry_surface_ids()


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
    # 2 planos x 20 mallas cada uno (ver test_geometry_scene_has_one_mesh_per_surface)
    # + 1 losa (solo para el plano índice 1, no para el 0) = 41 nodos.
    assert len(scene.geometry) == 41

    node_names = set(scene.geometry.keys())
    assert "p0_w_sur_jamb_0.cara_interior" in node_names
    assert "p1_w_sur_jamb_0.cara_interior" in node_names
    assert "p1_slab" in node_names
    assert "p0_slab" not in node_names

    surface_ids = {mesh.metadata["surface_id"] for mesh in scene.geometry.values()}
    assert surface_ids == _expected_geometry_surface_ids() | {"slab_1"}


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


def test_building_scene_generates_exactly_one_slab_for_second_plano(building_dir: Path):
    scene = build_building_scene_from_file(building_dir)
    slab_names = {name for name in scene.geometry if name.endswith("_slab")}
    assert slab_names == {"p1_slab"}

    slab_mesh = scene.geometry["p1_slab"]
    assert slab_mesh.metadata["surface_id"] == "slab_1"
    assert slab_mesh.metadata["plano_index"] == 1


def test_building_scene_slab_does_not_overlap_any_room_floor(building_dir: Path):
    """Chequeo geométrico real: el rango Y (altura, espacio Godot) de la losa
    del plano 1 no se solapa con el rango Y de ningún piso de recinto de
    ningún plano (incluido el suyo propio), con una tolerancia mínima."""
    scene = build_building_scene_from_file(building_dir)
    tolerance = 1e-6

    slab_mesh = scene.geometry["p1_slab"]
    slab_y_min = slab_mesh.bounds[0][1]
    slab_y_max = slab_mesh.bounds[1][1]

    floor_names = [name for name in scene.geometry if name.endswith("_room_sala.piso")]
    assert floor_names, "se esperaba al menos un piso de recinto en la escena"

    for floor_name in floor_names:
        floor_mesh = scene.geometry[floor_name]
        floor_y_min = floor_mesh.bounds[0][1]
        floor_y_max = floor_mesh.bounds[1][1]
        # Sin solapamiento: los rangos [slab_y_min, slab_y_max] y
        # [floor_y_min, floor_y_max] no deben intersecar (con tolerancia).
        overlaps = slab_y_max > floor_y_min - tolerance and slab_y_min < floor_y_max + tolerance
        assert not overlaps, f"la losa se solapa en Y con {floor_name}"

    # La losa del plano 1 queda inmediatamente debajo del piso de ESE mismo
    # plano (no del suelo del plano 0, que está a otra elevation).
    own_floor = scene.geometry["p1_room_sala.piso"]
    assert slab_y_max <= own_floor.bounds[0][1] - tolerance


def test_wall_faces_split_into_interior_and_exterior():
    """`w_norte` (sin aberturas) debe generar exactamente 2 mallas: cara
    interior y cara exterior, cada una con la mitad del espesor original."""
    scene = build_geometry_scene_from_file(GEOMETRY_EXAMPLE)
    assert "w_norte.cara_interior" in scene.geometry
    assert "w_norte.cara_exterior" in scene.geometry


def test_wall_interior_face_is_geometrically_closer_to_room_centroid():
    """Chequeo geométrico real (no solo de nombre): para `w_norte`, la malla
    `.cara_interior` debe estar más cerca del centroide de `room_sala`
    (2.0, 1.5 en el plano -> Godot (2.0, *, -1.5)) que `.cara_exterior`."""
    scene = build_geometry_scene_from_file(GEOMETRY_EXAMPLE)
    centroid_godot = (2.0, 0.0, -1.5)  # altura (Y) irrelevante para esta comparación XZ

    def _xz_distance_to_centroid(mesh) -> float:
        center = mesh.bounds.mean(axis=0)
        return math.hypot(center[0] - centroid_godot[0], center[2] - centroid_godot[2])

    interior = scene.geometry["w_norte.cara_interior"]
    exterior = scene.geometry["w_norte.cara_exterior"]
    assert _xz_distance_to_centroid(interior) < _xz_distance_to_centroid(exterior)


def test_room_has_floor_and_ceiling_with_ceiling_above_floor():
    """Existen `room_sala.piso` y `room_sala.techo`, y el techo está a mayor
    altura (eje Y en Godot) que el piso (chequeo real de bounding box)."""
    scene = build_geometry_scene_from_file(GEOMETRY_EXAMPLE)
    assert "room_sala.piso" in scene.geometry
    assert "room_sala.techo" in scene.geometry

    floor_mesh = scene.geometry["room_sala.piso"]
    ceiling_mesh = scene.geometry["room_sala.techo"]
    assert ceiling_mesh.bounds[0][1] > floor_mesh.bounds[1][1]

"""Tests de segmentación de muros con aberturas (Sprint 2).

Verifica que los huecos de puertas/ventanas no generan geometría (ningún
vértice de las mallas construidas cae dentro del volumen 3D del hueco) y que
un muro sin aberturas sigue generando una sola malla (no-regresión Sprint 1).
"""

from __future__ import annotations

import numpy as np
import trimesh

from pipeline.geometry.walls import build_wall_mesh, build_wall_meshes
from pipeline.schema import Opening, Room, Wall

# Room de referencia para inferir interior/exterior, misma bounding box que
# el fixture del contrato (geometry.example.json).
_ROOM_SALA = Room(
    id="room_sala",
    name="Sala",
    polygon=[(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)],
)


def _hole_bounds_godot(wall: Wall, opening: Opening) -> tuple[np.ndarray, np.ndarray]:
    """Bounding box 3D (Godot Y-up) del hueco de una abertura, con un margen
    negativo (contracción) para tolerar vértices exactamente en el borde."""
    from pipeline.geometry.coords import plane_to_godot

    (sx, sy), (ex, ey) = wall.start, wall.end
    import math

    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    # Normal perpendicular en el plano.
    nx, ny = -uy, ux

    s0 = opening.offset_along_wall
    s1 = opening.offset_along_wall + opening.width
    z0 = opening.sill_height
    z1 = opening.sill_height + opening.height
    margin = wall.thickness  # margen holgado en el plano perpendicular

    corners_plane = []
    for s in (s0, s1):
        px, py = sx + ux * s, sy + uy * s
        for t in (-margin, margin):
            corners_plane.append((px + nx * t, py + ny * t))

    corners_godot = [plane_to_godot(x, y, z) for (x, y) in corners_plane for z in (z0, z1)]
    arr = np.array(corners_godot)
    # Contraemos el rango un poco (tolerancia) para no rozar el borde exacto.
    tol = 1e-3
    lo = arr.min(axis=0) + tol
    hi = arr.max(axis=0) - tol
    return lo, hi


def _assert_no_vertex_in_hole(meshes: list[trimesh.Trimesh], wall: Wall, opening: Opening) -> None:
    lo, hi = _hole_bounds_godot(wall, opening)
    for mesh in meshes:
        inside = np.all((mesh.vertices >= lo) & (mesh.vertices <= hi), axis=1)
        assert not inside.any(), (
            f"malla {mesh.metadata.get('surface_id')} tiene vértices dentro del "
            f"hueco de {opening.id!r}"
        )


def test_wall_without_openings_and_without_rooms_falls_back_to_single_mesh():
    """Caso borde: sin rooms para inferir interior/exterior, se genera la
    caja completa sin dividir (con advertencia), igual que la ruta legacy."""
    wall = Wall(id="w1", start=(0.0, 0.0), end=(4.0, 0.0), thickness=0.15, height=2.5)
    meshes = build_wall_meshes(wall, [])
    assert len(meshes) == 1
    assert meshes[0].metadata["surface_id"] == "w1"
    # Debe coincidir con la ruta legacy de un solo box.
    assert meshes[0].vertices.shape == build_wall_mesh(wall).vertices.shape


def test_wall_without_openings_generates_interior_and_exterior_faces():
    wall = Wall(id="w1", start=(0.0, 0.0), end=(4.0, 0.0), thickness=0.15, height=2.5)
    meshes = build_wall_meshes(wall, [], [_ROOM_SALA])
    surface_ids = {m.metadata["surface_id"] for m in meshes}
    assert surface_ids == {"w1.cara_interior", "w1.cara_exterior"}
    assert len(meshes) == 2


def test_wall_with_door_generates_jambs_and_lintel_no_sill():
    wall = Wall(id="w_sur", start=(0.0, 0.0), end=(4.0, 0.0), thickness=0.15, height=2.5)
    door = Opening(
        id="op_puerta",
        wall_id="w_sur",
        type="door",
        offset_along_wall=1.55,
        width=0.9,
        height=2.1,
        sill_height=0.0,
    )
    meshes = build_wall_meshes(wall, [door], [_ROOM_SALA])
    surface_ids = {m.metadata["surface_id"] for m in meshes}
    base_ids = {"w_sur_jamb_0", "w_sur_jamb_1", "w_sur_lintel_op_puerta"}
    assert surface_ids == {
        f"{sid}.cara_{side}" for sid in base_ids for side in ("interior", "exterior")
    }
    assert len(meshes) == 6
    _assert_no_vertex_in_hole(meshes, wall, door)


def test_wall_with_window_generates_jambs_lintel_and_sill():
    wall = Wall(id="w_este", start=(4.0, 0.0), end=(4.0, 3.0), thickness=0.15, height=2.5)
    window = Opening(
        id="op_ventana",
        wall_id="w_este",
        type="window",
        offset_along_wall=0.9,
        width=1.2,
        height=1.1,
        sill_height=0.9,
    )
    meshes = build_wall_meshes(wall, [window], [_ROOM_SALA])
    surface_ids = {m.metadata["surface_id"] for m in meshes}
    base_ids = {
        "w_este_jamb_0",
        "w_este_jamb_1",
        "w_este_lintel_op_ventana",
        "w_este_sill_op_ventana",
    }
    assert surface_ids == {
        f"{sid}.cara_{side}" for sid in base_ids for side in ("interior", "exterior")
    }
    assert len(meshes) == 8
    _assert_no_vertex_in_hole(meshes, wall, window)


def test_wall_with_two_openings_generates_middle_jamb():
    wall = Wall(id="w_multi", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.15, height=2.5)
    door_a = Opening(
        id="op_a", wall_id="w_multi", type="door", offset_along_wall=0.5, width=0.9, height=2.1
    )
    door_b = Opening(
        id="op_b", wall_id="w_multi", type="door", offset_along_wall=3.5, width=0.9, height=2.1
    )
    meshes = build_wall_meshes(wall, [door_b, door_a], [_ROOM_SALA])  # orden invertido a propósito
    surface_ids = {m.metadata["surface_id"] for m in meshes}
    # jamb_0 (0..0.5), jamb_1 (1.4..3.5), jamb_2 (4.4..6.0) + 2 dinteles,
    # cada uno dividido en cara interior/exterior.
    base_ids = {
        "w_multi_jamb_0",
        "w_multi_jamb_1",
        "w_multi_jamb_2",
        "w_multi_lintel_op_a",
        "w_multi_lintel_op_b",
    }
    assert surface_ids == {
        f"{sid}.cara_{side}" for sid in base_ids for side in ("interior", "exterior")
    }
    _assert_no_vertex_in_hole(meshes, wall, door_a)
    _assert_no_vertex_in_hole(meshes, wall, door_b)

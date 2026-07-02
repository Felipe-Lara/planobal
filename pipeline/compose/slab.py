"""geometry.json + slab_thickness -> malla de losa horizontal entre pisos.

Sprint 4: cada plano (excepto el primero, apoyado sobre cimiento/suelo real)
genera una losa de transición inmediatamente debajo de su nivel de piso, con
el espesor declarado en `Plano.slab_thickness`. La losa se genera en el mismo
espacio "local" del plano (antes de aplicar rotation_deg/offset_xy/elevation)
para que `pipeline/compose/loader.py` la transforme igual que el resto de las
mallas de ese plano.
"""

from __future__ import annotations

import numpy as np
import trimesh
from trimesh.path.polygons import Polygon

from pipeline.geometry.coords import plane_to_godot
from pipeline.geometry.floor import _FLOOR_THICKNESS
from pipeline.schema import Geometry

# Margen entre la cara inferior del piso (que ya ocupa [-_FLOOR_THICKNESS, 0]
# en espacio local, ver floor.py) y la cara superior de la losa. Sin este
# margen ambas caras quedarían coplanares en z = -_FLOOR_THICKNESS, lo que
# alcanza para no solaparse en volumen pero deja las caras "tocándose" justo
# en el mismo plano; un pequeño gap evita cualquier ambigüedad de z-fighting.
_SLAB_GAP = 0.01


def _rooms_bounding_box(geometry: Geometry) -> list[tuple[float, float]]:
    """Bounding box (rectángulo) que envuelve todos los `rooms[].polygon`.

    Criterio elegido: un rectángulo único por bounding box global de todos
    los recintos del plano, en vez de una losa por room. Es más simple, más
    robusto frente a rooms con huecos/formas cóncavas, y suficiente para el
    propósito de la losa (evitar z-fighting entre pisos) -- no es una
    superficie repintable individualmente por recinto como sí lo es el piso.
    Si en el futuro se necesita una losa por room (p.ej. balcones voladizos
    que no deben extenderse bajo todo el footprint), se puede introducir un
    modo alternativo sin romper el contrato.
    """
    xs: list[float] = []
    ys: list[float] = []
    for room in geometry.rooms:
        for x, y in room.polygon:
            xs.append(x)
            ys.append(y)
    if not xs:
        raise ValueError("geometry sin rooms: no se puede derivar la extensión de la losa")
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]


def build_slab_mesh(geometry: Geometry, slab_thickness: float, surface_id: str) -> trimesh.Trimesh:
    """Construye la malla de losa (rectángulo extruido) para un plano.

    Ocupa, en espacio local (antes de aplicar la transformación del plano),
    el rango de altura `[-_FLOOR_THICKNESS - _SLAB_GAP - slab_thickness,
    -_FLOOR_THICKNESS - _SLAB_GAP]`: queda inmediatamente debajo de la cara
    inferior del piso del propio plano, sin solaparse con él. Al aplicar
    `_plano_transform` (traslación por `elevation`) en el loader, la losa
    queda debajo del nivel de piso de ESE plano, que es el criterio pedido:
    "pertenece" al piso que la usa como base.
    """
    footprint = _rooms_bounding_box(geometry)
    polygon = Polygon(footprint)
    if not polygon.is_valid or polygon.area == 0:
        raise ValueError("footprint de la losa inválido o degenerado")

    mesh = trimesh.creation.extrude_polygon(polygon, height=slab_thickness)
    vertices = mesh.vertices.copy()
    # extrude_polygon deja el sólido entre z=0 y z=slab_thickness; lo bajamos
    # para que la cara superior quede en z = -_FLOOR_THICKNESS - _SLAB_GAP.
    top = -_FLOOR_THICKNESS - _SLAB_GAP
    vertices[:, 2] += top - slab_thickness
    godot_vertices = np.array([plane_to_godot(x, y, z) for x, y, z in vertices])

    slab = trimesh.Trimesh(vertices=godot_vertices, faces=mesh.faces, process=True)
    slab.fix_normals()
    slab.metadata["surface_id"] = surface_id
    slab.metadata["name"] = surface_id
    return slab

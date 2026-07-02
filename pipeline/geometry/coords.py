"""Mapeo de coordenadas: plano (X/Y + altura) -> espacio Y-up de Godot.

Este es el ÚNICO archivo del pipeline que convierte ejes (ver CLAUDE.md).
Ningún otro módulo debe reordenar/negar componentes de un punto.

Convención elegida (right-handed, Y-up, igual que Godot):
    plano (x, y), altura z_up (metros)  ->  Godot (x, z_up, -y)

Es decir: el eje X del plano se mapea 1:1 al eje X de Godot, la altura
(vertical, "hacia arriba" en el mundo real) se mapea al eje Y de Godot, y el
eje Y del plano (habitualmente "norte" en el CAD) se mapea al eje -Z de
Godot. Esto preserva el sentido de giro (CCW visto desde arriba en el plano
sigue siendo CCW visto desde +Y en Godot) y evita reflejar la geometría.
"""

from __future__ import annotations

Point3D = tuple[float, float, float]


def plane_to_godot(x: float, y: float, z_up: float = 0.0) -> Point3D:
    """Convierte un punto del plano (x, y) + altura (z_up, metros) a Godot Y-up."""
    return (x, z_up, -y)

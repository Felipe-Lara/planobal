"""Esquema de building.json — manifiesto de composición multi-plano/multi-piso.

SAGRADO: no cambiar sin discutir en un issue (ver CLAUDE.md).
Cada entrada apila/posiciona un geometry.json en el espacio del edificio.
Unidades en METROS; ángulos en grados.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

Point2D = tuple[float, float]


class Plano(BaseModel):
    """Un plano dentro del edificio, con su transformación de composición."""

    model_config = ConfigDict(extra="forbid")

    geometry: str = Field(..., description="Ruta al geometry.json de este plano.")
    name: str | None = Field(None, description="Etiqueta legible (p.ej. 'Planta baja').")
    offset_xy: Point2D = Field(
        (0.0, 0.0), description="Traslación horizontal en el plano X/Y (m), hacia el patio."
    )
    elevation: float = Field(0.0, description="Altura de apilamiento vertical del piso (m).")
    rotation_deg: float = Field(0.0, description="Giro del plano alrededor de su origen (grados).")
    slab_thickness: float = Field(
        0.2, gt=0, description="Espesor de losa entre pisos (m); evita z-fighting techo/piso."
    )


class Building(BaseModel):
    """building.json completo: lista de planos a componer."""

    model_config = ConfigDict(extra="forbid")

    planos: list[Plano] = Field(..., min_length=1)

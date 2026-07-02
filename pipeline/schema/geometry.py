"""Esquema de geometry.json — el contrato de salida del pipeline por plano.

SAGRADO: no cambiar sin discutir en un issue (ver CLAUDE.md).
Todas las unidades en METROS. Coordenadas de plano en X/Y; la altura vive en
`height`/`sill_height` (el eje vertical se resuelve en el engine con Y arriba).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Un punto 2D en el plano, en metros.
Point2D = tuple[float, float]


class Wall(BaseModel):
    """Un muro como segmento de recta con espesor y altura."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Id estable: hash de la geometría, nunca índice.")
    start: Point2D
    end: Point2D
    thickness: float = Field(..., gt=0, description="Espesor en metros.")
    height: float = Field(..., gt=0, description="Altura en metros.")


class Opening(BaseModel):
    """Puerta o ventana anclada a un muro por su posición a lo largo del muro."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Id estable derivado de la geometría.")
    wall_id: str = Field(..., description="Referencia al Wall.id que la contiene.")
    type: Literal["door", "window"]
    offset_along_wall: float = Field(
        ..., ge=0, description="Distancia desde Wall.start hasta el borde de la abertura (m)."
    )
    width: float = Field(..., gt=0, description="Ancho de la abertura (m).")
    height: float = Field(..., gt=0, description="Alto de la abertura (m).")
    sill_height: float = Field(
        0.0, ge=0, description="Altura del antepecho desde el piso (m). 0 para puertas."
    )


class Room(BaseModel):
    """Un recinto definido por su polígono cerrado (lista de vértices X/Y)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str | None = None
    polygon: list[Point2D] = Field(..., min_length=3, description="Vértices en orden, en metros.")


class Source(BaseModel):
    """Trazabilidad: de dónde salió esta geometría y con qué unidades."""

    model_config = ConfigDict(extra="forbid")

    file: str = Field(..., description="Archivo CAD de origen (o 'manual' para fixtures).")
    insunits: int = Field(..., description="Código $INSUNITS del DXF (6 = metros).")
    generated_at: str = Field(..., description="Timestamp ISO-8601 de generación.")


class Geometry(BaseModel):
    """geometry.json completo de un plano."""

    model_config = ConfigDict(extra="forbid")

    walls: list[Wall] = Field(default_factory=list)
    openings: list[Opening] = Field(default_factory=list)
    rooms: list[Room] = Field(default_factory=list)
    source: Source

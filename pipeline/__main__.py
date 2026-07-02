"""CLI del pipeline de Plano3D.

Comandos (ver CLAUDE.md):
    python -m pipeline validate <archivo.json>   -> valida contra el contrato
    python -m pipeline ingest   <plano.dxf|dwg>  -> geometry.json   (Fase 2)
    python -m pipeline build    <building.json>  -> .gltf           (Fase 1/3)

`ingest` y `build` son stubs hasta sus fases; fallan limpio, no a medias.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from pipeline.compose.loader import build_building_scene_from_file
from pipeline.schema import Building, Geometry, PaintState

# Detección del esquema por pista en el nombre de archivo, luego por estructura.
_BY_NAME = {
    "geometry": Geometry,
    "building": Building,
    "paint_state": PaintState,
}


def _pick_schema(path: Path, data: object):
    stem = path.stem.lower()
    for key, model in _BY_NAME.items():
        if key in stem:
            return model, key
    # Fallback estructural.
    if isinstance(data, dict) and "walls" in data:
        return Geometry, "geometry"
    if isinstance(data, dict) and "planos" in data:
        return Building, "building"
    if isinstance(data, dict):
        return PaintState, "paint_state"
    return None, None


def _cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_file():
        print(f"[error] no existe el archivo: {path}", file=sys.stderr)
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[error] JSON inválido en {path.name}: {exc}", file=sys.stderr)
        return 2

    model, kind = _pick_schema(path, data)
    if model is None:
        print(
            f"[error] no reconozco el tipo de {path.name} (¿geometry/building/paint_state?)",
            file=sys.stderr,
        )
        return 2

    try:
        model.model_validate(data)
    except ValidationError as exc:
        print(f"[FALLA] {path.name} no cumple el esquema '{kind}':\n{exc}", file=sys.stderr)
        return 1

    print(f"[OK] {path.name} es un '{kind}' válido.")
    return 0


def _cmd_stub(name: str, phase: str):
    def run(args: argparse.Namespace) -> int:
        print(f"[pendiente] '{name}' aún no implementado (llega en {phase}).", file=sys.stderr)
        return 3

    return run


def _cmd_build(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_file():
        print(f"[error] no existe el archivo: {path}", file=sys.stderr)
        return 2

    try:
        scene = build_building_scene_from_file(path)
    except json.JSONDecodeError as exc:
        print(f"[error] JSON inválido en {path.name}: {exc}", file=sys.stderr)
        return 2
    except ValidationError as exc:
        print(
            f"[FALLA] {path.name} no cumple el esquema 'building'/'geometry':\n{exc}",
            file=sys.stderr,
        )
        return 1
    except (ValueError, FileNotFoundError) as exc:
        print(f"[error] no se pudo construir la geometría: {exc}", file=sys.stderr)
        return 1

    output = Path(args.output) if args.output else path.with_suffix(".gltf")
    try:
        scene.export(output)
    except Exception as exc:  # noqa: BLE001 - error de export de trimesh, reportar limpio
        print(f"[error] no se pudo exportar {output}: {exc}", file=sys.stderr)
        return 1

    print(f"[OK] {output} generado ({len(scene.geometry)} mallas).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline", description="Pipeline CAD→3D de Plano3D.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Valida un JSON del contrato.")
    p_val.add_argument("file", help="Ruta al geometry/building/paint_state .json")
    p_val.set_defaults(func=_cmd_validate)

    p_ing = sub.add_parser("ingest", help="DXF/DWG -> geometry.json (Fase 2).")
    p_ing.add_argument("file")
    p_ing.set_defaults(func=_cmd_stub("ingest", "Fase 2"))

    p_bld = sub.add_parser("build", help="building.json -> .gltf (Fase 1/3).")
    p_bld.add_argument("file")
    p_bld.add_argument(
        "-o",
        "--output",
        default=None,
        help="Ruta de salida del .gltf (default: junto al building.json, mismo stem).",
    )
    p_bld.set_defaults(func=_cmd_build)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

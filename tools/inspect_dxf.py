#!/usr/bin/env python3
"""Inspecciona un DXF y resume su estructura: capas, entidades, bloques, unidades.

Uso:
    python tools/inspect_dxf.py <plano.dxf>
    python tools/inspect_dxf.py <plano.dwg>   # requiere ODA File Converter instalado

Pega la salida de este script en la sesión de Claude Code en vez del archivo:
define cuánta inteligencia necesita el ingest sin quemar tokens.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import ezdxf

INSUNITS = {
    0: "sin unidad",
    1: "pulgadas",
    2: "pies",
    4: "milímetros",
    5: "centímetros",
    6: "metros",
    14: "decímetros",
}


def load(path: Path):
    if path.suffix.lower() == ".dwg":
        from ezdxf.addons import odafc

        print("[i] Convirtiendo DWG → DXF vía ODA File Converter…")
        return odafc.readfile(str(path))
    return ezdxf.readfile(str(path))


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    doc = load(path)
    msp = doc.modelspace()

    units = doc.header.get("$INSUNITS", 0)
    print(f"\n=== {path.name} ===")
    print(f"Versión DXF : {doc.dxfversion}")
    print(f"$INSUNITS   : {units} ({INSUNITS.get(units, 'otra')})")

    print(f"\n--- Capas ({len(doc.layers)}) con nº de entidades ---")
    per_layer = Counter(e.dxf.layer for e in msp)
    for layer in doc.layers:
        n = per_layer.get(layer.dxf.name, 0)
        flag = "  (vacía)" if n == 0 else ""
        print(f"  {layer.dxf.name:<30} {n:>6}{flag}")

    print("\n--- Tipos de entidad en modelspace ---")
    for etype, n in Counter(e.dxftype() for e in msp).most_common():
        print(f"  {etype:<20} {n:>6}")

    inserts = [e for e in msp if e.dxftype() == "INSERT"]
    if inserts:
        print(f"\n--- Bloques insertados ({len(inserts)} INSERT) ---")
        for name, n in Counter(i.dxf.name for i in inserts).most_common(30):
            print(f"  {name:<30} {n:>4}")
    else:
        print(
            "\n[!] No hay bloques INSERT: puertas/ventanas estarían dibujadas"
            " como líneas sueltas → el ingest necesitará más heurísticas."
        )

    polys = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    with_width = sum(1 for p in polys if p.dxf.hasattr("const_width") and p.dxf.const_width > 0)
    print(f"\n--- Polilíneas: {len(polys)} (con ancho constante: {with_width}) ---")
    if polys and with_width == 0:
        print(
            "[!] Ninguna polilínea tiene ancho: los muros probablemente son"
            " pares de líneas paralelas → activar heurística de paralelas."
        )

    # Extensión del dibujo (sanity check de escala)
    ext_min = doc.header.get("$EXTMIN", None)
    ext_max = doc.header.get("$EXTMAX", None)
    if ext_min and ext_max:
        w = ext_max[0] - ext_min[0]
        h = ext_max[1] - ext_min[1]
        print(f"\nExtensión del dibujo: {w:.2f} x {h:.2f} unidades de dibujo")
        print("(una casa debería medir ~10-30 si está en metros," " ~10000-30000 si está en mm)")


if __name__ == "__main__":
    main()

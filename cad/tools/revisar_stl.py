#!/usr/bin/env python3
"""Revisa los STL: medidas, que apoyen en z = 0 y que quepan en la Ender 3 Pro (220 x 220 x 250)."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

CAMA = (220.0, 220.0, 250.0)


def vertices(path: Path):
    data = path.read_bytes()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        for line in data.decode("ascii", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("vertex"):
                yield tuple(float(v) for v in line.split()[1:4])
    else:
        count = struct.unpack_from("<I", data, 80)[0]
        for i in range(count):
            vals = struct.unpack_from("<12f", data, 84 + i * 50)
            for k in range(3):
                yield vals[3 + 3 * k: 6 + 3 * k]


def revisar(path: Path) -> bool:
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    for v in vertices(path):
        for i in range(3):
            mins[i] = min(mins[i], v[i])
            maxs[i] = max(maxs[i], v[i])
    size = [maxs[i] - mins[i] for i in range(3)]
    cabe = (size[0] <= CAMA[0] and size[1] <= CAMA[1]) or (size[1] <= CAMA[0] and size[0] <= CAMA[1])
    cabe = cabe and size[2] <= CAMA[2]
    apoya = abs(mins[2]) < 0.01
    estado = "ok" if cabe and apoya else ("NO CABE" if not cabe else "no apoya en z=0")
    print(f"{path.stem:32s} {size[0]:7.1f} x {size[1]:7.1f} x {size[2]:6.1f} mm   {estado}")
    return cabe and apoya


def main() -> int:
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "stl"
    resultados = [revisar(p) for p in sorted(carpeta.glob("*.stl"))]
    return 0 if all(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())

"""Analisis y limpieza de los trabajos (.gcode) antes de enviarlos a la impresora."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .marlin import strip_comment

WORD = re.compile(r"([A-Z])\s*(-?\d*\.?\d+)")
TIME_PATTERNS = (
    re.compile(r"^;TIME:(\d+)"),  # Cura
    re.compile(r"^; estimated printing time \(normal mode\) = (.+)$"),  # PrusaSlicer / OrcaSlicer
    re.compile(r"^; total estimated time: (.+)$"),  # OrcaSlicer (nuevo)
)
DURATION = re.compile(r"(\d+)\s*([dhms])")


@dataclass
class JobInfo:
    path: Path
    lines: int = 0
    max_z: float = 0.0  # incluye el ascenso final del G-code
    max_y: float = 0.0
    print_max_y: float = 0.0  # Y maximo con extrusion (la pieza)
    est_seconds: int | None = None
    has_home: bool = False
    tail_start: int = 0  # indice (en ordenes) donde empieza el G-code final
    removed_tail: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.path.name


def _parse_duration(text: str) -> int | None:
    text = text.strip()
    if text.isdigit():
        return int(text)
    total = 0
    for value, unit in DURATION.findall(text):
        total += int(value) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[unit]
    return total or None


def _words(code: str) -> list[tuple[str, float]]:
    return [(axis, float(value)) for axis, value in WORD.findall(code.upper())]


def is_tail_command_removable(code: str, swap_y: float = 235.0) -> str | None:
    """Si una orden del G-code final estorba al cambio de placa, devuelve el motivo."""
    words = _words(code)
    if not words:
        return None
    letter, number = words[0]
    command = f"{letter}{int(number)}"
    if command in ("M84", "M18"):
        return "desactiva los motores (la cama perderia su posicion)"
    if command in ("M140", "M190") and any(a == "S" and v == 0 for a, v in words[1:]):
        return "apaga la cama (la app la mantiene caliente entre trabajos)"
    if command in ("M0", "M1", "M25", "M600"):
        return "pausa la impresora"
    if command in ("G0", "G1") and any(a == "Y" for a, _ in words[1:]):
        return "mueve la cama (la app la lleva a la posicion de cambio)"
    return None


def iter_commands(path: Path) -> Iterator[str]:
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            code = strip_comment(raw)
            if code:
                yield code


def analyze(path: Path, max_part_height: float = 150.0, swap_y: float = 235.0) -> JobInfo:
    path = Path(path)
    info = JobInfo(path)
    absolute = True
    x = y = z = 0.0
    e_absolute = True
    last_e = 0.0
    last_extrusion_index = -1
    index = 0
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            stripped = raw.strip()
            if stripped.startswith(";") and info.est_seconds is None:
                for pattern in TIME_PATTERNS:
                    m = pattern.match(stripped)
                    if m:
                        info.est_seconds = _parse_duration(m.group(1))
                        break
            code = strip_comment(raw).upper()
            if not code:
                continue
            words = _words(code)
            if not words:
                index += 1
                continue
            letter, number = words[0]
            command = f"{letter}{int(number)}"
            if command == "G90":
                absolute = True
                e_absolute = True
            elif command == "G91":
                absolute = False
                e_absolute = False
            elif command == "M82":
                e_absolute = True
            elif command == "M83":
                e_absolute = False
            elif command == "G92":
                for axis, value in words[1:]:
                    if axis == "E":
                        last_e = value
            elif command == "G28":
                info.has_home = True
            elif command in ("G0", "G1", "G2", "G3"):
                extrudes = False
                for axis, value in words[1:]:
                    if axis == "X":
                        x = value if absolute else x + value
                    elif axis == "Y":
                        y = value if absolute else y + value
                        info.max_y = max(info.max_y, y)
                    elif axis == "Z":
                        z = value if absolute else z + value
                        info.max_z = max(info.max_z, z)
                    elif axis == "E":
                        if e_absolute:
                            extrudes = value > last_e + 1e-6
                            last_e = value
                        else:
                            extrudes = value > 0
                if extrudes and command != "G0":
                    last_extrusion_index = index
                    info.print_max_y = max(info.print_max_y, y)
            index += 1
    info.lines = index
    info.tail_start = last_extrusion_index + 1

    # Ordenes del G-code final que estorban al cambio de placa
    if info.tail_start > 0:
        for i, code in enumerate(iter_commands(path)):
            if i < info.tail_start:
                continue
            reason = is_tail_command_removable(code, swap_y)
            if reason:
                info.removed_tail.append(f"{code}  ({reason})")

    printed_height = info.max_z
    if printed_height > max_part_height:
        info.errors.append(
            f"Altura maxima {printed_height:.1f} mm > {max_part_height:.0f} mm permitidos por la estacion"
        )
    if info.print_max_y >= swap_y - 0.5:
        info.warnings.append("La pieza llega a Y=235: la zapata o el tope trasero podrian estorbar")
    if not info.has_home:
        info.warnings.append("El G-code inicial no hace G28 (home); usa la plantilla de slicer/")
    if info.removed_tail:
        info.warnings.append(
            f"Se ignoraran {len(info.removed_tail)} ordenes del G-code final que estorban al cambio"
        )
    if info.lines == 0:
        info.errors.append("El archivo no contiene ordenes G-code")
    return info


def job_commands(info: JobInfo, strip_tail: bool = True, swap_y: float = 235.0) -> Iterator[str]:
    """Ordenes a enviar, sin las del G-code final que estorban (si strip_tail)."""
    for i, code in enumerate(iter_commands(info.path)):
        if strip_tail and i >= info.tail_start and is_tail_command_removable(code, swap_y):
            continue
        yield code


def format_duration(seconds: int | None) -> str:
    if not seconds:
        return "?"
    h, rest = divmod(int(seconds), 3600)
    m = rest // 60
    return f"{h} h {m:02d} min" if h else f"{m} min"

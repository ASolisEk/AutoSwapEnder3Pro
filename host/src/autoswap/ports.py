"""Descubrimiento de puertos USB e identificacion de la impresora y la estacion.

La Ender 3 Pro y muchos Arduino compatibles usan el mismo chip CH340 (1A86:7523),
asi que no basta con mirar el USB: se abre cada puerto y se hace un "saludo".
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from .transport import SerialLike, open_serial

KNOWN_USB = {
    (0x1A86, 0x7523): "CH340",
    (0x1A86, 0x55D4): "CH9102",
    (0x10C4, 0xEA60): "CP210x",
    (0x0403, 0x6001): "FTDI",
    (0x2341, 0x0043): "Arduino UNO",
    (0x2341, 0x0001): "Arduino UNO",
    (0x2A03, 0x0043): "Arduino UNO",
    (0x0483, 0x5740): "STM32 (Creality 4.2.x)",
}


@dataclass
class Candidate:
    device: str
    chip: str
    description: str
    serial_number: str = ""
    location: str = ""


def candidates() -> list[Candidate]:
    from serial.tools import list_ports

    found = []
    for p in sorted(list_ports.comports(), key=lambda x: x.device):
        if p.vid is None:  # Bluetooth y puertos virtuales
            continue
        if p.device.startswith("/dev/tty."):  # en macOS se usan los /dev/cu.*
            continue
        chip = KNOWN_USB.get((p.vid, p.pid), f"{p.vid:04X}:{p.pid:04X}")
        found.append(Candidate(p.device, chip, p.description or "", p.serial_number or "", p.location or ""))
    return found


def _wait_for(ser: SerialLike, token: bytes, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if token in ser.readline():
            return True
    return False


def identify(
    device: str,
    baud: int = 115200,
    opener: Callable[[str, int], SerialLike] | None = None,
    wait_s: float = 2.5,
) -> str:
    """'station', 'printer' o 'unknown'. ¡Nunca llamar con una impresion en curso!"""
    opener = opener or (lambda d, b: open_serial(d, b))
    ser = opener(device, baud)
    try:
        time.sleep(wait_s)  # UNO y placa 1.1.x se reinician al abrir el puerto
        ser.reset_input_buffer()
        ser.write(b"0 HELLO\n")
        if _wait_for(ser, b"AUTOSWAP-STATION", 2.0):
            return "station"
        ser.write(b"M115\n")
        if _wait_for(ser, b"FIRMWARE_NAME", 3.0):
            return "printer"
        return "unknown"
    finally:
        ser.close()


def find_devices(
    printer_port: str = "auto",
    station_port: str = "auto",
    baud: int = 115200,
    log: Callable[[str], None] = print,
) -> tuple[str | None, str | None]:
    """Resuelve los puertos 'auto' identificando cada candidato."""
    printer = None if printer_port == "auto" else printer_port
    station = None if station_port == "auto" else station_port
    if printer and station:
        return printer, station
    for cand in candidates():
        if cand.device in (printer, station):
            continue
        log(f"Identificando {cand.device} ({cand.chip})...")
        try:
            kind = identify(cand.device, baud)
        except OSError as exc:
            log(f"  no se pudo abrir: {exc}")
            continue
        log(f"  -> {kind}")
        if kind == "printer" and not printer:
            printer = cand.device
        elif kind == "station" and not station:
            station = cand.device
        if printer and station:
            break
    return printer, station

"""Interfaz minima de un puerto serie (pyserial o los simuladores de sim.py)."""

from __future__ import annotations

from typing import Protocol


class SerialLike(Protocol):
    def write(self, data: bytes) -> int | None: ...

    def readline(self) -> bytes: ...  # b"" si vence el tiempo de espera

    def reset_input_buffer(self) -> None: ...

    def close(self) -> None: ...


def open_serial(device: str, baud: int = 115200, timeout: float = 0.2) -> SerialLike:
    """Abre un puerto real. Importa pyserial solo cuando hace falta."""
    import serial

    return serial.Serial(device, baud, timeout=timeout, write_timeout=2)

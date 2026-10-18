"""Enlace con la impresora (firmware Marlin) por USB serie.

Cada linea se envia con numero de linea y checksum (`N<n> <orden>*<cs>`) y se espera
su `ok` antes de enviar la siguiente. Se gestionan `Resend`, `busy` y errores fatales.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass

from .transport import SerialLike

RESEND_RE = re.compile(r"^(?:resend|rs)[: ]\s*N?(\d+)", re.IGNORECASE)
TEMP_RE = re.compile(r"\b(T|B)(\d*):\s*(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)")
FATAL = ("Error:Printer halted", "Error:Thermal Runaway", "kill() called", "Error:Heating failed",
         "Error:MAXTEMP", "Error:MINTEMP")

# Ordenes que pueden tardar minutos (calentar, homing, nivelacion, pausas)
LONG_COMMANDS = ("M109", "M190", "M116", "G28", "G29", "M400", "G4", "M303")


class PrinterError(RuntimeError):
    pass


class PrinterHalted(PrinterError):
    """La impresora se detuvo por seguridad: no reintentar."""


@dataclass
class Temperatures:
    nozzle: float = 0.0
    nozzle_target: float = 0.0
    bed: float = 0.0
    bed_target: float = 0.0
    updated: float = 0.0


def checksum(payload: str) -> int:
    cs = 0
    for byte in payload.encode("ascii", errors="replace"):
        cs ^= byte
    return cs


def strip_comment(line: str) -> str:
    """Quita comentarios ';' y '(...)' y espacios sobrantes."""
    code = line.split(";", 1)[0]
    if "(" in code:
        code = re.sub(r"\([^)]*\)", "", code)
    return code.strip()


class MarlinLink:
    def __init__(self, port: SerialLike, on_line: Callable[[str], None] | None = None):
        self.port = port
        self.line_no = 0
        self.history: dict[int, bytes] = {}
        self.on_line = on_line or (lambda _text: None)
        self.temps = Temperatures()
        self.firmware: dict[str, str] = {}
        self.lines_sent = 0
        self.resends = 0

    # ------------------------------------------------------------------ conexion
    def handshake(self, wait_s: float = 2.5) -> dict[str, str]:
        """Espera el arranque, reinicia el contador de lineas y lee M115."""
        time.sleep(wait_s)  # la placa 1.1.x (8 bits) se reinicia al abrir el puerto
        self._drain(0.5)
        self.port.reset_input_buffer()
        self.line_no = 0
        self.send_raw("M110 N0")
        replies = self.send("M115", timeout=10)
        info: dict[str, str] = {}
        for text in replies:
            if text.startswith("FIRMWARE_NAME"):
                for key, value in re.findall(r"([A-Z_]+):(.*?)(?=\s[A-Z_]+:|$)", text):
                    info[key] = value.strip()
            elif text.startswith("Cap:"):
                key, _, value = text[4:].partition(":")
                info[f"Cap:{key}"] = value.strip()
        self.firmware = info
        if info.get("Cap:AUTOREPORT_TEMP") == "1":
            self.send("M155 S2")  # la impresora informa la temperatura cada 2 s
        return info

    def close(self) -> None:
        self.port.close()

    def _drain(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            raw = self.port.readline()
            if raw:
                self._handle_async(raw.decode("ascii", errors="replace").strip())

    # ------------------------------------------------------------------ envio
    def send_raw(self, gcode: str, timeout: float = 5.0) -> list[str]:
        """Envia sin numero de linea (solo para M110 al conectar)."""
        self.port.write(f"{gcode}\n".encode("ascii"))
        return self._wait_ok(timeout)

    def send(self, gcode: str, timeout: float | None = None) -> list[str]:
        """Envia una linea y espera su 'ok'. Devuelve lo recibido mientras tanto."""
        cmd = strip_comment(gcode)
        if not cmd:
            return []
        if timeout is None:
            timeout = 900.0 if cmd.split()[0].upper() in LONG_COMMANDS else 120.0
        self.line_no += 1
        if cmd.upper().startswith("M110"):
            payload = f"N{self.line_no} M110 N{self.line_no}"
        else:
            payload = f"N{self.line_no} {cmd}"
        line = f"{payload}*{checksum(payload)}\n".encode("ascii", errors="replace")
        self.history[self.line_no] = line
        self.history.pop(self.line_no - 200, None)  # conservar solo las ultimas 200
        self.port.write(line)
        self.lines_sent += 1
        return self._wait_ok(timeout)

    def _wait_ok(self, timeout: float) -> list[str]:
        replies: list[str] = []
        skip_ok = 0
        deadline = time.monotonic() + timeout
        while True:
            raw = self.port.readline()
            if not raw:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"Sin 'ok' de la impresora tras {timeout:.0f} s")
                continue
            text = raw.decode("ascii", errors="replace").strip()
            if not text:
                continue
            self.on_line(text)
            if any(f in text for f in FATAL):
                raise PrinterHalted(text)
            match = RESEND_RE.match(text)
            if match:
                number = int(match.group(1))
                if number not in self.history:
                    raise PrinterError(f"La impresora pidio reenviar la linea {number}, que ya no existe")
                skip_ok += 1  # Marlin manda tambien un 'ok' del intento fallido
                self.resends += 1
                self.port.write(self.history[number])
                deadline = time.monotonic() + timeout
                continue
            if text.startswith("echo:busy") or text.startswith("busy:"):
                deadline = time.monotonic() + timeout  # G28, M109, M190... siguen en curso
                continue
            if text.startswith("ok"):
                self._parse_temps(text)
                if skip_ok:
                    skip_ok -= 1
                    continue
                return replies
            self._handle_async(text)
            replies.append(text)

    def _handle_async(self, text: str) -> None:
        self._parse_temps(text)

    def _parse_temps(self, text: str) -> None:
        found = False
        for kind, index, current, target in TEMP_RE.findall(text):
            if kind == "T" and index in ("", "0"):
                self.temps.nozzle, self.temps.nozzle_target = float(current), float(target)
                found = True
            elif kind == "B":
                self.temps.bed, self.temps.bed_target = float(current), float(target)
                found = True
        if found:
            self.temps.updated = time.monotonic()

    def poll(self, seconds: float = 0.2) -> None:
        """Lee mensajes espontaneos (temperaturas) sin enviar nada."""
        self._drain(seconds)

    def query_temperatures(self) -> Temperatures:
        self.send("M105", timeout=10)
        return self.temps

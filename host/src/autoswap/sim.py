"""Impresora y estacion simuladas (para pruebas y para `autoswap ... --simulate`).

Ambas se comportan como un puerto serie: write() recibe ordenes y readline()
devuelve las respuestas cuando "llega su momento".
"""

from __future__ import annotations

import re
import time
from collections import deque

from .marlin import checksum

LINE_RE = re.compile(r"^N(\d+)\s+(.*)\*(\d+)$")


class _SimPort:
    def __init__(self, speed: float = 1.0, read_timeout: float = 0.02):
        self.speed = speed  # 10.0 = diez veces mas rapido que la realidad
        self.read_timeout = read_timeout
        self._out: deque[tuple[float, bytes]] = deque()
        self.closed = False
        self.written: list[str] = []

    def _push(self, text: str, delay: float = 0.0) -> None:
        due = time.monotonic() + delay / self.speed
        item = (due, (text + "\n").encode("ascii"))
        # mantener el orden por instante de entrega
        if not self._out or self._out[-1][0] <= due:
            self._out.append(item)
        else:
            items = sorted([*self._out, item], key=lambda x: x[0])
            self._out = deque(items)

    def readline(self) -> bytes:
        end = time.monotonic() + self.read_timeout
        while True:
            self._tick()
            if self._out and self._out[0][0] <= time.monotonic():
                return self._out.popleft()[1]
            if time.monotonic() >= end:
                return b""
            time.sleep(0.001)

    def _tick(self) -> None:
        pass

    def reset_input_buffer(self) -> None:
        now = time.monotonic()
        self._out = deque(x for x in self._out if x[0] > now)

    def close(self) -> None:
        self.closed = True


class SimMarlin(_SimPort):
    """Ender 3 Pro simulada: checksums, Resend, busy, temperaturas y posicion."""

    def __init__(self, speed: float = 50.0, corrupt_lines: set[int] | None = None,
                 halt_after: int | None = None):
        super().__init__(speed)
        self.expected = 1
        self.corrupt_lines = set(corrupt_lines or ())
        self.halt_after = halt_after
        self.received: list[str] = []  # ordenes aceptadas (sin N ni checksum)
        self.pos = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        self.absolute = True
        self.nozzle = self.bed = 25.0
        self.nozzle_target = self.bed_target = 0.0
        self._push("start")
        self._push("echo:Marlin 2.0.9.3 (simulada)")

    def write(self, data: bytes) -> int:
        for raw in data.decode("ascii", errors="replace").splitlines():
            self._handle(raw.strip())
        return len(data)

    def _handle(self, raw: str) -> None:
        self.written.append(raw)
        m = LINE_RE.match(raw)
        if m:
            number, payload, cs = int(m.group(1)), m.group(2), int(m.group(3))
            if number in self.corrupt_lines:
                self.corrupt_lines.discard(number)
                self._push(f"Error:checksum mismatch, Last Line: {number - 1}")
                self._push(f"Resend: {number}")
                self._push("ok")
                return
            if checksum(f"N{number} {payload}") != cs:
                self._push(f"Error:checksum mismatch, Last Line: {self.expected - 1}")
                self._push(f"Resend: {self.expected}")
                self._push("ok")
                return
            if payload.startswith("M110"):
                self.expected = number + 1
                self._push("ok")
                return
            if number != self.expected:
                self._push(f"Error:Line Number is not Last Line Number+1, Last Line: {self.expected - 1}")
                self._push(f"Resend: {self.expected}")
                self._push("ok")
                return
            self.expected += 1
            cmd = payload.strip()
        else:
            cmd = raw
            if cmd.startswith("M110"):
                self.expected = int(cmd.split("N")[-1] or 0) + 1
                self._push("ok")
                return
        self.received.append(cmd)
        if self.halt_after is not None and len(self.received) >= self.halt_after:
            self._push("Error:Printer halted. kill() called!")
            return
        self._execute(cmd)

    def _execute(self, cmd: str) -> None:
        word = cmd.split()[0].upper()
        args = {w[0].upper(): w[1:] for w in cmd.split()[1:] if w}
        if word == "M115":
            self._push("FIRMWARE_NAME:Marlin 2.0.9.3 (simulada) SOURCE_CODE_URL:github.com/MarlinFirmware/Marlin "
                       "PROTOCOL_VERSION:1.0 MACHINE_TYPE:Ender-3 Pro EXTRUDER_COUNT:1")
            self._push("Cap:AUTOREPORT_TEMP:1")
            self._push("Cap:EMERGENCY_PARSER:0")
            self._push("ok")
        elif word == "M105":
            self._push(f"ok T:{self.nozzle:.2f} /{self.nozzle_target:.2f} B:{self.bed:.2f} /{self.bed_target:.2f}")
        elif word in ("M104", "M109"):
            self.nozzle_target = float(args.get("S", 0) or 0)
            if word == "M109":
                self._push("echo:busy: processing", 0.5)
            self.nozzle = self.nozzle_target or 25.0
            self._push("ok", 1.0 if word == "M109" else 0.0)
        elif word in ("M140", "M190"):
            self.bed_target = float(args.get("S", 0) or 0)
            if word == "M190":
                self._push("echo:busy: processing", 0.5)
            self.bed = self.bed_target or 25.0
            self._push("ok", 1.0 if word == "M190" else 0.0)
        elif word == "G28":
            self.pos = {"X": 0.0, "Y": 0.0, "Z": 0.0}
            self._push("echo:busy: processing", 0.5)
            self._push("ok", 1.0)
        elif word in ("G0", "G1"):
            for axis in "XYZ":
                if axis in args and args[axis]:
                    value = float(args[axis])
                    self.pos[axis] = value if self.absolute else self.pos[axis] + value
            self._push("ok")
        elif word == "G90":
            self.absolute = True
            self._push("ok")
        elif word == "G91":
            self.absolute = False
            self._push("ok")
        elif word == "G4":
            seconds = float(args.get("S", 0) or 0) + float(args.get("P", 0) or 0) / 1000
            self._push("ok", seconds)
        else:
            self._push("ok")


class SimStation(_SimPort):
    """Estacion de cambio simulada (protocolo version 2) con fallos inyectables."""

    def __init__(self, speed: float = 50.0, slots: int = 6, plates: int = 6, plate_on_bed: bool = True):
        super().__init__(speed)
        self.slots = slots
        self.magazine = [k < plates for k in range(slots)]
        self.plate_on_bed = plate_on_bed
        self.level = 0
        self.homed = False
        self.fault = "none"
        self.busy_until = 0.0
        self.pings = 0
        self.dropped = 0
        self.flap = "closed"
        self.stop_pressed = False
        self.fail_next: dict[str, str] = {}  # {"EJECT": "E08 DROP_JAM"}
        self.commands: list[str] = []
        self.cfg = {"s_bed": 530.0, "s_mag": 15.0, "s_drop": 275.0, "slots": float(slots)}
        self._push("* READY AUTOSWAP-STATION fw=0.2.0-sim proto=2 cfg=defaults")

    def write(self, data: bytes) -> int:
        for raw in data.decode("ascii", errors="replace").splitlines():
            if raw.strip():
                self._handle(raw.strip())
        return len(data)

    def _status_text(self) -> str:
        return (f"state={'FAULT' if self.fault != 'none' else ('IDLE' if self.homed else 'UNHOMED')} "
                f"homed={int(self.homed)} pos=285 lift={5 + 14 * self.level:.2f} level={self.level} "
                f"slots={self.slots} bed={int(self.plate_on_bed)} drop=0 eng=0 sw=00 hook=down "
                f"flap={self.flap} stop={int(self.stop_pressed)} err={self.fault}")

    def _handle(self, raw: str) -> None:
        parts = raw.split()
        cid, cmd, args = parts[0], parts[1].upper() if len(parts) > 1 else "", parts[2:]
        if cmd == "PING":
            self.pings += 1
            self._push(f"{cid} OK PONG")
            return
        self.commands.append(" ".join(parts[1:]))
        if cmd == "HELLO":
            self._push(f"{cid} OK AUTOSWAP-STATION fw=0.2.0-sim proto=2")
        elif cmd == "STATUS":
            self._push(f"{cid} OK {self._status_text()}")
        elif cmd == "RESET":
            self.fault = "none"
            self.homed = False
            self._push(f"{cid} OK")
        elif cmd == "STOP":
            self.fault = "E18"
            self._push(f"{cid} OK")
        elif cmd == "CFG":
            if args and args[0].upper() == "LIST":
                for key, value in self.cfg.items():
                    self._push(f"{cid} CFG {key}={value:g}")
                self._push(f"{cid} OK n={len(self.cfg)}")
            elif len(args) == 3 and args[0].upper() == "SET":
                self.cfg[args[1]] = float(args[2])
                self._push(f"{cid} OK {args[1]}={float(args[2]):g}")
            else:
                self._push(f"{cid} OK")
        elif cmd in ("HOME", "EJECT", "LOAD", "LIFT", "MOVE", "GOTO"):
            self._action(cid, cmd, args)
        elif cmd in ("HOOK", "FLAP"):
            self._push(f"{cid} OK")
        else:
            self._push(f"{cid} ERR E12 UNKNOWN_CMD")

    def _action(self, cid: str, cmd: str, args: list[str]) -> None:
        if self.fault != "none":
            self._push(f"{cid} ERR E19 IN_FAULT")
            return
        if cmd in ("EJECT", "LOAD", "GOTO") and not self.homed:
            self._push(f"{cid} ERR E01 NOT_HOMED")
            return
        if cmd == "EJECT" and not self.plate_on_bed:
            self._push(f"{cid} ERR E04 NO_PLATE_ON_BED")
            return
        if cmd == "LOAD" and self.plate_on_bed:
            self._push(f"{cid} ERR E05 BED_OCCUPIED")
            return
        self._push(f"{cid} ACCEPTED")
        duration = {"HOME": 30.0, "EJECT": 35.0, "LOAD": 40.0}.get(cmd, 5.0)
        failure = self.fail_next.pop(cmd, None)
        if failure:
            self.fault = failure.split()[0]
            self._push(f"{cid} ERR {failure}", duration / 2)
            self._push(f"* FAULT {failure} action={cmd}", duration / 2)
            return
        if cmd == "HOME":
            self.homed = True
        elif cmd == "EJECT":
            self.plate_on_bed = False
            self.dropped += 1
        elif cmd == "LOAD":
            if self.level >= self.slots or not self.magazine[self.level]:
                self.fault = "E06"
                self._push(f"{cid} ERR E06 MAGAZINE_EMPTY", duration / 2)
                return
            self.magazine[self.level] = False
            self.level += 1
            self.plate_on_bed = True
        elif cmd == "LIFT" and args and args[0].upper() == "LEVEL":
            self.level = int(args[1])
        self._push(f"{cid} DONE {cmd}", duration)

    def reload(self, plates: int) -> None:
        """El usuario recarga el cargador desde el estante inferior."""
        self.magazine = [k < plates for k in range(self.slots)]

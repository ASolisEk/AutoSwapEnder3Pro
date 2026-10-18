"""Enlace con la Estacion de Cambio Frontal (protocolo del Anexo C, version 2)."""

from __future__ import annotations

import time
from collections.abc import Callable

from .transport import SerialLike

ERROR_HELP = {
    "E01": "Falta hacer HOME en la estacion.",
    "E02": "El boton STOP esta pulsado. Sueltalo (gira la seta) y pulsa Reiniciar.",
    "E03": "Un paso tardo demasiado. Revisa que nada bloquee el carro o el ascensor.",
    "E04": "No se detecta placa en la cama. ¿Se cayo la pieza o la placa? Revisa y reanuda.",
    "E05": "Ya hay una placa en la cama: retirala antes de cargar otra.",
    "E06": "No hay placa en el nivel actual del cargador. Recarga placas e indica cuantas pusiste.",
    "E07": "La placa usada no llego a la zona de descarga. Retirala a mano.",
    "E08": "La placa no cayo a la caja al voltear. Vacia la caja o retira la placa a mano.",
    "E09": "La placa nueva no llego al tope trasero. Empujala contra el tope a mano.",
    "E10": "La estacion esta ocupada con otra accion.",
    "E11": "Argumento invalido.",
    "E12": "Orden desconocida (¿firmware desactualizado?).",
    "E13": "El movimiento sale del recorrido permitido.",
    "E14": "La estacion dejo de recibir senal del ordenador y se detuvo por seguridad.",
    "E15": "El carro no encontro su sensor HOME. Revisa el sensor y el cable.",
    "E16": "El dedo del gancho no engancho la zapata. Recalibra s_bed o revisa la zapata.",
    "E17": "El ascensor no encontro su sensor HOME. Revisa el sensor y el cable.",
    "E18": "Detenida por el ordenador (STOP).",
    "E19": "La estacion esta en falla: pulsa Reiniciar y luego HOME.",
    "E20": "No se pudo guardar la configuracion en la EEPROM.",
}


class StationError(RuntimeError):
    def __init__(self, code: str, name: str, raw: str):
        self.code = code
        self.name = name
        self.raw = raw
        super().__init__(f"{code} {name}: {ERROR_HELP.get(code, '')}".strip())


def parse_pairs(text: str) -> dict[str, str]:
    return dict(kv.split("=", 1) for kv in text.split() if "=" in kv)


class StationLink:
    def __init__(
        self,
        port: SerialLike,
        ping_interval_s: float = 2.0,
        on_line: Callable[[str], None] | None = None,
    ):
        self.port = port
        self.ping_interval_s = ping_interval_s
        self.next_id = 1
        self.last_status: dict[str, str] = {}
        self.firmware = ""
        self.on_line = on_line or (lambda _text: None)
        self.on_status: Callable[[dict[str, str]], None] = lambda _s: None
        self.last_fault = ""

    def handshake(self, wait_s: float = 2.5) -> str:
        time.sleep(wait_s)  # el UNO se reinicia al abrir el puerto
        self.port.reset_input_buffer()
        reply = self.command("HELLO", timeout=5)
        if "AUTOSWAP-STATION" not in reply:
            raise StationError("E12", "BAD_HELLO", reply)
        self.firmware = reply
        self.command("PING", timeout=3)  # activa el watchdog del ordenador en la estacion
        return reply

    def close(self) -> None:
        self.port.close()

    def _new_id(self) -> int:
        cid = self.next_id
        self.next_id = self.next_id % 65000 + 1
        return cid

    def command(self, cmd: str, timeout: float = 60.0) -> str:
        """Envia una orden y espera OK/DONE. Lanza StationError si responde ERR."""
        cid = self._new_id()
        self.port.write(f"{cid} {cmd}\n".encode("ascii"))
        deadline = time.monotonic() + timeout
        last_ping = time.monotonic()
        lines: list[str] = []
        while time.monotonic() < deadline:
            if time.monotonic() - last_ping >= self.ping_interval_s:  # latido para el watchdog
                self.port.write(b"0 PING\n")
                last_ping = time.monotonic()
            raw = self.port.readline()
            if not raw:
                continue
            text = raw.decode("ascii", errors="replace").strip()
            if not text:
                continue
            self.on_line(text)
            if text.startswith("* STATUS"):
                self.last_status = parse_pairs(text)
                self.on_status(self.last_status)
                continue
            if text.startswith("* FAULT"):
                self.last_fault = text
                continue
            if text.startswith("*"):
                continue
            parts = text.split(maxsplit=2)
            if len(parts) < 2 or parts[0] != str(cid):
                continue
            kind = parts[1]
            if kind == "ACCEPTED":
                continue
            if kind == "CFG":
                lines.append(parts[2] if len(parts) > 2 else "")
                continue
            if kind in ("OK", "DONE"):
                if lines:
                    return "\n".join([*lines, text])
                return text
            if kind == "ERR":
                rest = parts[2].split() if len(parts) > 2 else ["E??", "UNKNOWN"]
                raise StationError(rest[0], rest[1] if len(rest) > 1 else "", text)
        raise TimeoutError(f"La estacion no termino '{cmd}' en {timeout:.0f} s")

    # ------------------------------------------------------------------ atajos
    def status(self) -> dict[str, str]:
        self.last_status = parse_pairs(self.command("STATUS", timeout=5))
        self.on_status(self.last_status)
        return self.last_status

    def home(self, timeout: float = 180.0) -> str:
        return self.command("HOME", timeout=timeout)

    def eject(self, timeout: float = 120.0) -> str:
        return self.command("EJECT", timeout=timeout)

    def load(self, timeout: float = 150.0) -> str:
        return self.command("LOAD", timeout=timeout)

    def lift_level(self, level: int, timeout: float = 90.0) -> str:
        return self.command(f"LIFT LEVEL {int(level)}", timeout=timeout)

    def stop(self) -> str:
        return self.command("STOP", timeout=3)

    def reset(self) -> str:
        return self.command("RESET", timeout=3)

    def cfg_list(self) -> dict[str, float]:
        reply = self.command("CFG LIST", timeout=10)
        values: dict[str, float] = {}
        for line in reply.splitlines():
            key, sep, value = line.partition("=")
            if sep and " " not in key:
                values[key] = float(value)
        return values

    def cfg_set(self, key: str, value: float) -> str:
        return self.command(f"CFG SET {key} {value:g}", timeout=5)

    def cfg_save(self) -> str:
        return self.command("CFG SAVE", timeout=10)

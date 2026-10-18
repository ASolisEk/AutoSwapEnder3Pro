"""Conexion con la impresora y la estacion (reales o simuladas) y registro en disco."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig, log_dir
from .marlin import MarlinLink
from .ports import find_devices
from .sim import SimMarlin, SimStation
from .station import StationLink
from .transport import open_serial


class FileLog:
    """Registro de texto en la carpeta de registros del sistema (un archivo por dia)."""

    def __init__(self, folder: Path | None = None):
        folder = folder or log_dir()
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"autoswap-{dt.date.today():%Y%m%d}.log"
        self._fh = self.path.open("a", encoding="utf-8")

    def __call__(self, text: str) -> None:
        self._fh.write(f"{dt.datetime.now():%H:%M:%S.%f}"[:-3] + f" {text}\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


@dataclass
class Session:
    printer: MarlinLink
    station: StationLink
    simulated: bool = False
    sim_printer: SimMarlin | None = None
    sim_station: SimStation | None = None

    def close(self) -> None:
        self.printer.close()
        self.station.close()


def connect(
    cfg: AppConfig,
    simulate: bool = False,
    log: Callable[[str], None] = print,
    raw_log: Callable[[str], None] | None = None,
    sim_speed: float = 50.0,
) -> Session:
    raw = raw_log or (lambda _t: None)
    if simulate:
        sp, ss = SimMarlin(speed=sim_speed), SimStation(speed=sim_speed, plates=cfg.queue.plates_in_magazine)
        printer = MarlinLink(sp, on_line=lambda t: raw(f"IMP< {t}"))
        station = StationLink(ss, ping_interval_s=cfg.station.ping_interval_s, on_line=lambda t: raw(f"EST< {t}"))
        printer.handshake(wait_s=0)
        station.handshake(wait_s=0)
        log("Modo simulado: impresora y estacion virtuales")
        return Session(printer, station, True, sp, ss)

    printer_port, station_port = find_devices(cfg.printer.port, cfg.station.port, cfg.printer.baud, log)
    if not printer_port:
        raise ConnectionError("No se encontro la impresora. Revisa el cable USB y el driver CH340.")
    if not station_port:
        raise ConnectionError("No se encontro la estacion. Revisa el cable USB y que tenga el firmware cargado.")
    log(f"Impresora: {printer_port} | Estacion: {station_port}")
    printer = MarlinLink(open_serial(printer_port, cfg.printer.baud), on_line=lambda t: raw(f"IMP< {t}"))
    station = StationLink(
        open_serial(station_port, cfg.station.baud),
        ping_interval_s=cfg.station.ping_interval_s,
        on_line=lambda t: raw(f"EST< {t}"),
    )
    info = printer.handshake(wait_s=cfg.printer.connect_wait_s)
    log(f"Firmware de la impresora: {info.get('FIRMWARE_NAME', '?')} ({info.get('MACHINE_TYPE', '?')})")
    log(f"Estacion: {station.handshake()}")
    return Session(printer, station)

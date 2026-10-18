"""Configuracion de la app (config.toml) y rutas de cada sistema operativo."""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

APP_NAME = "AutoSwapEnder3Pro"


def _base_dirs() -> tuple[Path, Path]:
    """(carpeta de configuracion, carpeta de registros) segun el sistema."""
    override = os.environ.get("AUTOSWAP_HOME")
    if override:
        base = Path(override)
        return base, base / "logs"
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / APP_NAME, home / "Library" / "Logs" / APP_NAME
    if sys.platform == "win32":
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local")) / APP_NAME
        return local, local / "logs"
    xdg_config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    xdg_state = Path(os.environ.get("XDG_STATE_HOME", home / ".local" / "state"))
    return xdg_config / "autoswap", xdg_state / "autoswap"


def config_dir() -> Path:
    return _base_dirs()[0]


def log_dir() -> Path:
    return _base_dirs()[1]


def config_path() -> Path:
    return config_dir() / "config.toml"


def state_path() -> Path:
    """Archivo donde se guarda el avance de la cola para poder reanudarla."""
    return config_dir() / "queue_state.json"


@dataclass
class PrinterConfig:
    port: str = "auto"  # o "/dev/cu.usbserial-1420" (macOS) / "COM5" (Windows)
    baud: int = 115200
    swap_y: float = 235.0  # posicion de la cama para el cambio
    park_x: float = 5.0
    z_clearance: float = 10.0
    z_max: float = 250.0
    max_part_height: float = 150.0  # la app rechaza trabajos mas altos
    plate_warmup_s: int = 60  # espera tras cargar una placa fria
    z_feed: float = 600.0  # mm/min
    y_feed: float = 3000.0  # mm/min
    connect_wait_s: float = 2.5  # la placa 1.1.x se reinicia al abrir el puerto


@dataclass
class StationConfig:
    port: str = "auto"
    baud: int = 115200
    ping_interval_s: float = 2.0
    eject_timeout_s: float = 120.0
    load_timeout_s: float = 150.0
    home_timeout_s: float = 180.0


@dataclass
class QueueConfig:
    plates_in_magazine: int = 6  # lo indica el usuario al recargar
    pause_on_warning: bool = True
    turn_off_bed_at_end: bool = True
    strip_end_gcode: bool = True  # quitar M84 / M140 S0 / "presentar pieza" del final de cada trabajo


@dataclass
class NotifyConfig:
    desktop: bool = True
    ntfy_topic: str = ""  # opcional: avisos al movil con https://ntfy.sh


@dataclass
class AppConfig:
    printer: PrinterConfig = field(default_factory=PrinterConfig)
    station: StationConfig = field(default_factory=StationConfig)
    queue: QueueConfig = field(default_factory=QueueConfig)
    notifications: NotifyConfig = field(default_factory=NotifyConfig)

    SECTIONS = ("printer", "station", "queue", "notifications")

    def set_value(self, dotted: str, raw: str) -> None:
        """Cambia una opcion con la forma 'seccion.clave' (p. ej. 'printer.port')."""
        section, _, key = dotted.partition(".")
        if section not in self.SECTIONS or not key:
            raise KeyError(f"Opcion desconocida: {dotted}")
        target = getattr(self, section)
        names = {f.name: f for f in fields(target)}
        if key not in names:
            raise KeyError(f"Opcion desconocida: {dotted}")
        current = getattr(target, key)
        setattr(target, key, _coerce(raw, type(current)))


def _coerce(raw: str, kind: type):
    if kind is bool:
        if raw.lower() in ("1", "true", "si", "sí", "yes", "on"):
            return True
        if raw.lower() in ("0", "false", "no", "off"):
            return False
        raise ValueError(f"Valor booleano invalido: {raw}")
    return kind(raw)


def load(path: Path | None = None) -> AppConfig:
    path = path or config_path()
    cfg = AppConfig()
    if not path.exists():
        return cfg
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    for section in AppConfig.SECTIONS:
        values = data.get(section, {})
        target = getattr(cfg, section)
        for f in fields(target):
            if f.name in values:
                setattr(target, f.name, _coerce(str(values[f.name]), type(getattr(target, f.name))))
    return cfg


def _toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def dumps(cfg: AppConfig) -> str:
    lines = ["# config.toml - AutoSwapEnder3Pro (generado por la app; se puede editar a mano)", ""]
    for section in AppConfig.SECTIONS:
        lines.append(f"[{section}]")
        for key, value in asdict(getattr(cfg, section)).items():
            lines.append(f"{key} = {_toml_value(value)}")
        lines.append("")
    return "\n".join(lines)


def save(cfg: AppConfig, path: Path | None = None) -> Path:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(cfg), encoding="utf-8")
    return path

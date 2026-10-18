from pathlib import Path

import pytest

from autoswap import config as config_mod
from autoswap.cli import main
from autoswap.ports import identify


def test_config_roundtrip_and_set():
    cfg = config_mod.load()
    assert cfg.notifications.desktop is False  # escrito por conftest
    cfg.set_value("printer.port", "COM5")
    cfg.set_value("queue.pause_on_warning", "no")
    cfg.set_value("printer.plate_warmup_s", "90")
    path = config_mod.save(cfg)
    again = config_mod.load(path)
    assert again.printer.port == "COM5"
    assert again.queue.pause_on_warning is False
    assert again.printer.plate_warmup_s == 90
    with pytest.raises(KeyError):
        cfg.set_value("printer.nope", "1")


def test_cli_analyze(sample_gcode, capsys):
    assert main(["analyze", str(sample_gcode)]) == 0
    out = capsys.readouterr().out
    assert "altura 15.2 mm" in out
    assert "se omite: M84" in out


def test_cli_queue_simulated(sample_gcode, capsys):
    code = main(["queue", str(sample_gcode), "--copies", "3", "--simulate", "--yes", "--sim-speed", "2000"])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Trabajos completados: 3" in out
    assert "Cambios: 2" in out


def test_cli_test_swap_simulated(tmp_path, capsys):
    report = tmp_path / "r.csv"
    code = main(["test-swap", "--cycles", "4", "--plates", "2", "--simulate", "--yes",
                 "--sim-speed", "2000", "--report", str(report)])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "4/4 ciclos correctos" in out
    assert report.read_text(encoding="utf-8").startswith("ciclo,resultado")


def test_cli_station_simulated(capsys):
    assert main(["station", "--simulate", "STATUS"]) == 0
    assert "state=UNHOMED" in capsys.readouterr().out


def test_cli_merge_manual(sample_gcode, tmp_path):
    out = tmp_path / "cola.gcode"
    assert main(["merge", str(sample_gcode), "--copies", "2", "-o", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.count("M0 Cambia la placa PEI") == 1
    assert text.count("TRABAJO") == 2


def test_cli_config_set_and_show(capsys):
    assert main(["config", "set", "printer.port=/dev/cu.usbserial-1420"]) == 0
    assert main(["config", "show"]) == 0
    assert 'port = "/dev/cu.usbserial-1420"' in capsys.readouterr().out


class FakePort:
    def __init__(self, replies: dict[bytes, bytes]):
        self.replies = replies
        self.pending: list[bytes] = []

    def write(self, data: bytes):
        for key, value in self.replies.items():
            if key in data:
                self.pending.append(value)

    def readline(self) -> bytes:
        return self.pending.pop(0) if self.pending else b""

    def reset_input_buffer(self):
        pass

    def close(self):
        pass


@pytest.mark.parametrize(
    "replies,expected",
    [
        ({b"HELLO": b"0 OK AUTOSWAP-STATION fw=0.2.0 proto=2\n"}, "station"),
        ({b"M115": b"FIRMWARE_NAME:Marlin 2.0.9.3 MACHINE_TYPE:Ender-3 Pro\n"}, "printer"),
        ({}, "unknown"),
    ],
)
def test_identify(replies, expected):
    assert identify("X", opener=lambda _d, _b: FakePort(replies), wait_s=0) == expected


def test_paths_use_override(isolated_home: Path):
    assert config_mod.config_path() == isolated_home / "config.toml"
    assert config_mod.log_dir() == isolated_home / "logs"

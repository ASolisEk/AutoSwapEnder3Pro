from __future__ import annotations

from pathlib import Path

import pytest

SAMPLE = """;FLAVOR:Marlin
;TIME:600
M140 S60
M104 S150
G28 ; home
M190 S60
M109 S200
G92 E0
G1 Z2.0 F3000
G1 X3 Y20 Z0.3 F5000
G1 X3 Y150 Z0.3 F1500 E15 ; purga
G92 E0
G1 X50 Y50 Z0.2 F3000
G1 X60 Y50 E1.0
G1 X60 Y60 E2.0
G1 Z5.2
G1 X70 Y70 E3.0
;End of Gcode
G91
G1 E-2 F2700
G1 Z10 F600
G90
G1 X0 Y235 F3000 ; presentar pieza
M106 S0
M104 S0
M140 S0
M84
"""


@pytest.fixture
def sample_gcode(tmp_path: Path) -> Path:
    path = tmp_path / "pieza.gcode"
    path.write_text(SAMPLE, encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Configuracion y registros en una carpeta temporal; sin avisos de escritorio."""
    home = tmp_path / "home"
    monkeypatch.setenv("AUTOSWAP_HOME", str(home))
    home.mkdir()
    (home / "config.toml").write_text("[notifications]\ndesktop = false\n", encoding="utf-8")
    return home

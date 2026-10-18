import pytest

from autoswap.marlin import MarlinLink, PrinterHalted, checksum, strip_comment
from autoswap.sim import SimMarlin


def connected(**kwargs) -> tuple[MarlinLink, SimMarlin]:
    sim = SimMarlin(speed=1000, **kwargs)
    link = MarlinLink(sim)
    link.handshake(wait_s=0)
    return link, sim


def test_checksum_matches_reprap_example():
    assert checksum("N3 T0") == 57


def test_strip_comment():
    assert strip_comment("G1 X10 ; mover") == "G1 X10"
    assert strip_comment("G1 (comentario) Y5") == "G1  Y5"
    assert strip_comment("; solo comentario") == ""


def test_handshake_reads_firmware_and_enables_autoreport():
    link, sim = connected()
    assert link.firmware["FIRMWARE_NAME"].startswith("Marlin")
    assert link.firmware["MACHINE_TYPE"] == "Ender-3 Pro"
    assert "M155 S2" in sim.received


def test_lines_have_numbers_and_checksums():
    link, sim = connected()
    link.send("G1 X10 Y20 ; comentario")
    last = sim.written[-1]
    assert last.startswith(f"N{link.line_no} G1 X10 Y20*")
    assert sim.received[-1] == "G1 X10 Y20"


def test_resend_is_handled():
    link, sim = connected(corrupt_lines={3})
    link.send("G1 X10")
    assert link.resends == 1
    assert sim.received.count("G1 X10") == 1
    link.send("G1 X20")
    assert sim.received[-1] == "G1 X20"


def test_busy_keeps_waiting():
    link, sim = connected()
    link.send("M109 S200")
    assert sim.nozzle == 200


def test_fatal_error_raises():
    link, _ = connected(halt_after=4)
    with pytest.raises(PrinterHalted):
        link.send("G1 X1")
        link.send("G1 X2")


def test_temperature_parsing():
    link, _ = connected()
    link._parse_temps("ok T:200.5 /205.0 B:60.1 /60.0 @:127 B@:0")
    assert link.temps.nozzle == 200.5
    assert link.temps.nozzle_target == 205.0
    assert link.temps.bed == 60.1
    link.send("M104 S180")
    link.query_temperatures()
    assert link.temps.nozzle_target == 180

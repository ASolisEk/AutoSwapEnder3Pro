import pytest

from autoswap.config import AppConfig
from autoswap.gcode import analyze
from autoswap.marlin import MarlinLink
from autoswap.orchestrator import Decision, Orchestrator, Phase, PreflightError
from autoswap.sim import SimMarlin, SimStation
from autoswap.station import StationLink


def make(plates=6, decide=None, **station_kwargs):
    cfg = AppConfig()
    cfg.printer.plate_warmup_s = 5
    cfg.queue.plates_in_magazine = plates
    sp = SimMarlin(speed=1000)
    ss = SimStation(speed=1000, plates=plates, **station_kwargs)
    printer = MarlinLink(sp)
    station = StationLink(ss, ping_interval_s=0.05)
    printer.handshake(wait_s=0)
    station.handshake(wait_s=0)
    events = []
    orch = Orchestrator(printer, station, cfg, on_event=events.append, decide=decide)
    return orch, sp, ss, events


def test_queue_of_three_jobs_swaps_twice(sample_gcode):
    orch, sp, ss, events = make()
    jobs = [analyze(sample_gcode)] * 3
    assert orch.run(jobs) == 3
    assert ss.dropped == 2
    assert ss.level == 2
    assert orch.plates_left == 4
    assert sp.received.count("G1 Y235.0 F3000") == 2  # cama a la posicion de cambio
    assert sp.received.count("G1 Z25.20 F600") == 2  # Z max del trabajo + 10 mm
    assert "M84" not in sp.received  # el G-code final ya no apaga motores
    assert sp.received.count("M140 S0") == 1  # la cama solo se apaga al final de la cola
    assert sp.received.count("G4 S5") == 2  # calentamiento de la placa nueva
    assert orch.phase == Phase.FINISHED
    assert any(e.kind == "swap" for e in events)
    assert any(e.kind == "done" for e in events)


def test_station_is_homed_automatically(sample_gcode):
    orch, _, ss, _ = make()
    assert not ss.homed
    orch.run([analyze(sample_gcode)])
    assert ss.homed
    assert "HOME" in ss.commands


def test_error_during_swap_pauses_and_retry_recovers(sample_gcode):
    asked = []

    def decide(problem):
        asked.append(problem)
        return Decision.RETRY

    orch, _, ss, events = make(decide=decide)
    ss.fail_next["EJECT"] = "E08 DROP_JAM"
    assert orch.run([analyze(sample_gcode)] * 2) == 2
    assert len(asked) == 1
    assert asked[0].code == "E08"
    assert "RESET" in ss.commands  # la estacion se reinicio y volvio a hacer HOME
    assert any(e.kind == "problem" for e in events)


def test_abort_leaves_printer_safe(sample_gcode):
    orch, sp, ss, events = make(decide=lambda _p: Decision.ABORT)
    ss.fail_next["LOAD"] = "E09 SEAT_FAIL"
    assert orch.run([analyze(sample_gcode)] * 3) == 1
    assert orch.phase == Phase.CANCELLED
    assert sp.received[-1].startswith("M117")
    assert "M104 S0" in sp.received[-8:]
    assert events[-1].data.get("cancelled")


def test_manual_swap_decision_continues(sample_gcode):
    orch, _, ss, _ = make(decide=lambda _p: Decision.DONE_MANUALLY)
    ss.fail_next["LOAD"] = "E09 SEAT_FAIL"

    original = ss._action

    def action(cid, cmd, args):
        original(cid, cmd, args)
        if cmd == "LOAD":  # el usuario coloca la placa a mano
            ss.plate_on_bed = True

    ss._action = action
    assert orch.run([analyze(sample_gcode)] * 2) == 2


def test_preflight_rejects_too_few_plates_and_tall_jobs(sample_gcode):
    orch, _, _, _ = make(plates=1)
    with pytest.raises(PreflightError) as info:
        orch.run([analyze(sample_gcode)] * 3)
    assert "placas" in str(info.value)
    orch2, _, _, _ = make()
    with pytest.raises(PreflightError):
        orch2.run([analyze(sample_gcode, max_part_height=5)])


def test_preflight_requires_plate_on_bed(sample_gcode):
    orch, _, _, _ = make(plate_on_bed=False)
    with pytest.raises(PreflightError) as info:
        orch.run([analyze(sample_gcode)])
    assert "PLACA_EN_CAMA" in str(info.value)


def test_test_cycles_with_reload():
    orch, _, ss, _ = make(plates=3)
    orch.station.home()

    def reload():
        ss.reload(3)
        return 3

    rows = orch.test_cycles(7, on_reload=reload)
    assert len(rows) == 7
    assert all(r["resultado"] == "ok" for r in rows)
    assert ss.dropped == 7


def test_cancel_during_print(sample_gcode):
    orch, sp, _, _ = make()
    orch.cancel()
    orch._cancel.clear()

    def stop_soon(event):
        if event.kind == "job":
            orch.cancel()

    orch.on_event = stop_soon
    assert orch.run([analyze(sample_gcode)] * 2) == 0
    assert orch.phase == Phase.CANCELLED
    assert "M104 S0" in sp.received

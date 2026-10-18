import pytest

from autoswap.sim import SimStation
from autoswap.station import StationError, StationLink, parse_pairs


def link(**kwargs) -> tuple[StationLink, SimStation]:
    sim = SimStation(speed=kwargs.pop("speed", 1000), **kwargs)
    st = StationLink(sim, ping_interval_s=0.05)
    st.handshake(wait_s=0)
    return st, sim


def test_handshake_and_status():
    st, sim = link()
    assert "AUTOSWAP-STATION" in st.firmware
    status = st.status()
    assert status["state"] == "UNHOMED"
    assert status["bed"] == "1"
    assert sim.pings >= 1  # el saludo activa el watchdog


def test_parse_pairs():
    assert parse_pairs("5 OK state=IDLE homed=1 pos=0.0") == {"state": "IDLE", "homed": "1", "pos": "0.0"}


def test_actions_and_pings_during_long_actions():
    st, sim = link(speed=100)
    pings_before = sim.pings
    st.home()
    assert sim.pings > pings_before  # latidos mientras se espera el DONE
    st.eject()
    st.load()
    assert sim.level == 1
    assert sim.dropped == 1
    assert st.status()["bed"] == "1"


def test_errors_raise_station_error_with_code():
    st, sim = link()
    with pytest.raises(StationError) as info:
        st.eject()
    assert info.value.code == "E01"
    st.home()
    sim.fail_next["EJECT"] = "E08 DROP_JAM"
    with pytest.raises(StationError) as info:
        st.eject()
    assert info.value.code == "E08"
    assert "caja" in str(info.value)
    with pytest.raises(StationError):
        st.command("FOO")


def test_cfg_list_and_set():
    st, sim = link()
    values = st.cfg_list()
    assert values["s_bed"] == 530.0
    st.cfg_set("s_bed", 512.5)
    assert sim.cfg["s_bed"] == 512.5

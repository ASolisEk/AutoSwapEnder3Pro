"""Prueba de humo de la interfaz grafica (se omite si PySide6 no esta instalado)."""

import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_main_window_builds_and_updates_status(sample_gcode):
    from PySide6.QtWidgets import QApplication

    from autoswap.gui.app import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.on_status({"state": "IDLE", "err": "none", "pos": "285", "lift": "5", "level": "0",
                      "slots": "6", "bed": "1", "drop": "0", "eng": "0", "stop": "0",
                      "hook": "down", "flap": "closed"})
    assert window.lbl_state.text() == "IDLE"
    window.list_jobs.addItem(str(sample_gcode))
    window.spin_copies.setValue(2)
    window.update_summary()
    assert window.lbl_summary.text().startswith("2 trabajos")
    window.close()
    app.processEvents()

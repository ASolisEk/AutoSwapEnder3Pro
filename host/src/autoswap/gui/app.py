"""Ventana principal de AutoSwap (PySide6): conexion, estacion, cola, asistente y registro.

Todo el acceso a los puertos serie ocurre en hilos de trabajo protegidos por un
candado; la interfaz recibe los resultados por senales de Qt.
"""

from __future__ import annotations

import sys
import threading
import traceback
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from .. import config as config_mod
from ..gcode import analyze, format_duration
from ..orchestrator import Decision, Event, Orchestrator, PreflightError, Problem
from ..platform_utils import keep_awake, notify_desktop, notify_ntfy
from ..session import FileLog, Session, connect
from ..station import ERROR_HELP, StationError

SENSORS = [
    ("bed", "Placa en cama"),
    ("drop", "Placa en descarga"),
    ("eng", "Gancho enganchado"),
    ("stop", "STOP pulsado"),
]

WIZARD_HTML = """
<h3>Asistente de calibracion (seccion 8.10 a 8.13 del plan)</h3>
<ol>
<li><b>Sensores</b>: en la pestaña <i>Estacion</i>, pulsa cada final de carrera con la mano y comprueba que su
indicador cambia. Si alguno sale al reves, cambia <code>inv_mask</code> (ver la guia).</li>
<li><b>Servos</b>: pulsa <i>Gancho abajo</i> y coloca el dedo apuntando hacia abajo; <i>Volteador cerrar</i> y
coloca el brazo con la tapa horizontal.</li>
<li><b>HOME</b>: pulsa <i>HOME</i>. El carro va a su sensor y el ascensor sube a su tope.</li>
<li><b>s_bed</b>: con la cama en Y=235 y una placa asentada, mueve el carro hasta que el dedo quede justo bajo la
ranura de la zapata y pulsa <i>Guardar posicion como s_bed</i>.</li>
<li><b>s_mag</b>: con placas en el cargador (nivel 0), repite y guarda <i>s_mag</i>.</li>
<li><b>s_drop</b>: tira de una placa a mano hasta que quede entera en la descarga y guarda <i>s_drop</i>.</li>
<li><b>Prueba</b>: ejecuta 5 ciclos y luego 20. Objetivo: 20 de 20 sin fallos.</li>
</ol>
"""


class Bridge(QObject):
    log = Signal(str)
    event = Signal(object)
    status = Signal(dict)
    connected = Signal(bool, str)
    problem = Signal(object, object)  # (Problem, holder dict con 'event' y 'decision')
    busy = Signal(bool)
    temps = Signal(str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"AutoSwap Ender 3 Pro {__version__}")
        self.resize(980, 720)
        self.cfg = config_mod.load()
        self.session: Session | None = None
        self.orch: Orchestrator | None = None
        self.io_lock = threading.Lock()
        self.queue_running = False
        self.filelog: FileLog | None = None
        self.bridge = Bridge()
        self.bridge.log.connect(self.append_log)
        self.bridge.event.connect(self.on_event)
        self.bridge.status.connect(self.on_status)
        self.bridge.connected.connect(self.on_connected)
        self.bridge.problem.connect(self.on_problem)
        self.bridge.busy.connect(self.on_busy)

        tabs = QTabWidget()
        tabs.addTab(self._build_connection_tab(), "Conexion")
        tabs.addTab(self._build_station_tab(), "Estacion")
        tabs.addTab(self._build_queue_tab(), "Cola")
        tabs.addTab(self._build_wizard_tab(), "Asistente")
        tabs.addTab(self._build_log_tab(), "Registro")
        self.setCentralWidget(tabs)
        self.bridge.temps.connect(self.lbl_temps.setText)

        quit_action = QAction("Salir", self)
        quit_action.triggered.connect(self.close)
        self.menuBar().addMenu("Archivo").addAction(quit_action)

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_status)
        self.poll_timer.start(1500)
        self.set_controls_enabled(False)

    # ------------------------------------------------------------------ pestañas
    def _build_connection_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        form = QFormLayout()
        self.lbl_printer = QLabel("desconectada")
        self.lbl_station = QLabel("desconectada")
        form.addRow("Impresora:", self.lbl_printer)
        form.addRow("Estacion:", self.lbl_station)
        layout.addLayout(form)
        row = QHBoxLayout()
        self.btn_connect = QPushButton("Conectar (detectar puertos)")
        self.btn_simulate = QPushButton("Modo simulado")
        self.btn_disconnect = QPushButton("Desconectar")
        self.btn_connect.clicked.connect(lambda: self.do_connect(False))
        self.btn_simulate.clicked.connect(lambda: self.do_connect(True))
        self.btn_disconnect.clicked.connect(self.do_disconnect)
        for b in (self.btn_connect, self.btn_simulate, self.btn_disconnect):
            row.addWidget(b)
        layout.addLayout(row)
        note = QLabel(
            "Conecta antes de imprimir: la placa de la impresora se reinicia al abrir el puerto USB.\n"
            "Cierra Cura, Pronterface, Arduino IDE u OctoPrint si estan usando los puertos."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)
        return w

    def _build_station_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        box = QGroupBox("Estado")
        grid = QGridLayout(box)
        self.lbl_state = QLabel("-")
        fuente = self.lbl_state.font()
        fuente.setPointSize(14)
        fuente.setBold(True)
        self.lbl_state.setFont(fuente)
        grid.addWidget(QLabel("Estado:"), 0, 0)
        grid.addWidget(self.lbl_state, 0, 1, 1, 3)
        self.lbl_pos = QLabel("-")
        grid.addWidget(QLabel("Carro / ascensor / nivel:"), 1, 0)
        grid.addWidget(self.lbl_pos, 1, 1, 1, 3)
        self.sensor_labels: dict[str, QLabel] = {}
        for i, (key, name) in enumerate(SENSORS):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setMinimumWidth(140)
            self.sensor_labels[key] = lbl
            grid.addWidget(lbl, 2, i)
        layout.addWidget(box)

        actions = QGroupBox("Acciones")
        g = QGridLayout(actions)
        buttons: list[tuple[str, Callable[[], None]]] = [
            ("HOME", lambda: self.station_cmd("HOME", 240)),
            ("Expulsar placa", lambda: self.station_cmd("EJECT", 150)),
            ("Cargar placa", lambda: self.station_cmd("LOAD", 180)),
            ("Gancho arriba", lambda: self.station_cmd("HOOK UP")),
            ("Gancho abajo", lambda: self.station_cmd("HOOK DOWN")),
            ("Volteador abrir", lambda: self.station_cmd("FLAP OPEN")),
            ("Volteador cerrar", lambda: self.station_cmd("FLAP CLOSE")),
            ("Reiniciar (RESET)", lambda: self.station_cmd("RESET")),
        ]
        self.station_buttons: list[QPushButton] = []
        for i, (text, fn) in enumerate(buttons):
            b = QPushButton(text)
            b.clicked.connect(fn)
            g.addWidget(b, i // 4, i % 4)
            self.station_buttons.append(b)
        self.spin_move = QDoubleSpinBox()
        self.spin_move.setRange(-600, 600)
        self.spin_move.setValue(10)
        self.spin_move.setSuffix(" mm")
        b_move = QPushButton("Mover carro")
        b_move.clicked.connect(lambda: self.station_cmd(f"MOVE {self.spin_move.value():.2f}", 60))
        self.spin_level = QSpinBox()
        self.spin_level.setRange(0, 11)
        b_level = QPushButton("Ir a nivel del cargador")
        b_level.clicked.connect(lambda: self.station_cmd(f"LIFT LEVEL {self.spin_level.value()}", 90))
        g.addWidget(self.spin_move, 2, 0)
        g.addWidget(b_move, 2, 1)
        g.addWidget(self.spin_level, 2, 2)
        g.addWidget(b_level, 2, 3)
        self.station_buttons += [b_move, b_level]
        layout.addWidget(actions)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setMinimumHeight(56)
        self.btn_stop.setStyleSheet("background:#c62828;color:white;font-size:20px;font-weight:bold;")
        self.btn_stop.clicked.connect(self.emergency_stop)
        layout.addWidget(self.btn_stop)
        layout.addStretch(1)
        return w

    def _build_queue_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.list_jobs = QListWidget()
        layout.addWidget(self.list_jobs)
        row = QHBoxLayout()
        for text, fn in (("Añadir .gcode", self.add_files), ("Quitar", self.remove_file),
                         ("Subir", lambda: self.move_file(-1)), ("Bajar", lambda: self.move_file(1))):
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        layout.addLayout(row)
        form = QFormLayout()
        self.spin_copies = QSpinBox()
        self.spin_copies.setRange(1, 50)
        self.spin_plates = QSpinBox()
        self.spin_plates.setRange(0, 12)
        self.spin_plates.setValue(self.cfg.queue.plates_in_magazine)
        self.chk_reloaded = QCheckBox("Acabo de llenar el cargador desde el estante inferior")
        self.chk_reloaded.setChecked(True)
        form.addRow("Copias de cada archivo:", self.spin_copies)
        form.addRow("Placas en el cargador:", self.spin_plates)
        form.addRow("", self.chk_reloaded)
        layout.addLayout(form)
        self.lbl_summary = QLabel("")
        layout.addWidget(self.lbl_summary)
        row = QHBoxLayout()
        self.btn_start = QPushButton("Iniciar cola")
        self.btn_pause = QPushButton("Pausar al terminar el trabajo actual")
        self.btn_cancel = QPushButton("Cancelar cola")
        self.btn_start.clicked.connect(self.start_queue)
        self.btn_pause.clicked.connect(lambda: self.orch and self.orch.pause_after_current_job())
        self.btn_cancel.clicked.connect(self.cancel_queue)
        for b in (self.btn_start, self.btn_pause, self.btn_cancel):
            row.addWidget(b)
        layout.addLayout(row)
        self.lbl_phase = QLabel("Fase: -")
        self.lbl_temps = QLabel("Boquilla - °C | Cama - °C")
        self.progress = QProgressBar()
        layout.addWidget(self.lbl_phase)
        layout.addWidget(self.progress)
        layout.addWidget(self.lbl_temps)
        return w

    def _build_wizard_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        text = QTextBrowser()
        text.setHtml(WIZARD_HTML)
        layout.addWidget(text)
        row = QHBoxLayout()
        for key in ("s_bed", "s_mag", "s_drop"):
            b = QPushButton(f"Guardar posicion como {key}")
            b.clicked.connect(lambda _=False, k=key: self.save_position(k))
            row.addWidget(b)
            self.station_buttons.append(b)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.spin_cycles = QSpinBox()
        self.spin_cycles.setRange(1, 500)
        self.spin_cycles.setValue(5)
        b = QPushButton("Ejecutar ciclos de prueba")
        b.clicked.connect(self.run_test_cycles)
        self.station_buttons.append(b)
        row.addWidget(QLabel("Ciclos:"))
        row.addWidget(self.spin_cycles)
        row.addWidget(b)
        layout.addLayout(row)
        return w

    def _build_log_tab(self) -> QWidget:
        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumBlockCount(5000)
        return self.txt_log

    # ------------------------------------------------------------------ utilidades
    def run_bg(self, fn: Callable[[], object], done: Callable[[object], None] | None = None) -> None:
        def worker():
            self.bridge.busy.emit(True)
            try:
                with self.io_lock:
                    result = fn()
                if done:
                    done(result)
            except StationError as exc:
                self.bridge.log.emit(f"Estacion: {exc}")
            except Exception as exc:  # noqa: BLE001 - se muestra al usuario
                self.bridge.log.emit(f"Error: {exc}")
                self.bridge.log.emit(traceback.format_exc(limit=3))
            finally:
                self.bridge.busy.emit(False)

        threading.Thread(target=worker, daemon=True).start()

    def append_log(self, text: str) -> None:
        self.txt_log.appendPlainText(text)

    def set_controls_enabled(self, on: bool) -> None:
        for b in self.station_buttons:
            b.setEnabled(on and not self.queue_running)
        self.btn_start.setEnabled(on and not self.queue_running)

    def on_busy(self, busy: bool) -> None:
        self.statusBar().showMessage("Trabajando..." if busy else "Listo", 3000 if not busy else 0)

    # ------------------------------------------------------------------ conexion
    def do_connect(self, simulate: bool) -> None:
        if self.session:
            return
        self.append_log("Conectando..." + (" (simulado)" if simulate else ""))

        def fn():
            self.filelog = None if simulate else FileLog()
            return connect(self.cfg, simulate=simulate, log=self.bridge.log.emit, raw_log=self.filelog)

        def done(session):
            self.session = session
            session.station.on_status = self.bridge.status.emit
            self.bridge.connected.emit(True, "simulada" if simulate else "conectada")

        self.run_bg(fn, done)

    def do_disconnect(self) -> None:
        if self.queue_running:
            QMessageBox.warning(self, "AutoSwap", "Cancela la cola antes de desconectar.")
            return
        if self.session:
            with self.io_lock:
                self.session.close()
            self.session = None
        self.on_connected(False, "desconectada")

    def on_connected(self, ok: bool, text: str) -> None:
        self.lbl_printer.setText(text)
        self.lbl_station.setText(text)
        self.set_controls_enabled(ok)

    def poll_status(self) -> None:
        """Consulta periodica (en segundo plano) mientras no haya una cola en marcha."""
        if not self.session or self.queue_running or not self.io_lock.acquire(blocking=False):
            return
        session = self.session

        def worker():
            try:
                session.station.status()  # on_status -> senal status
                session.printer.poll(0.05)
                t = session.printer.temps
                self.bridge.temps.emit(f"Boquilla {t.nozzle:.0f}/{t.nozzle_target:.0f} °C | "
                                       f"Cama {t.bed:.0f}/{t.bed_target:.0f} °C")
            except Exception as exc:  # noqa: BLE001
                self.bridge.log.emit(f"Sin respuesta de la estacion: {exc}")
            finally:
                self.io_lock.release()

        threading.Thread(target=worker, daemon=True).start()

    def on_status(self, st: dict) -> None:
        state = st.get("state", "?")
        err = st.get("err", "none")
        self.lbl_state.setText(state if err == "none" else f"{state}  ({err}: {ERROR_HELP.get(err, '')})")
        self.lbl_pos.setText(f"{st.get('pos', '?')} mm / {st.get('lift', '?')} mm / nivel {st.get('level', '?')} "
                             f"de {st.get('slots', '?')} | gancho {st.get('hook', '?')} | "
                             f"volteador {st.get('flap', '?')}")
        for key, lbl in self.sensor_labels.items():
            active = st.get(key) == "1"
            color = ("#c62828" if key == "stop" else "#2e7d32") if active else "#9e9e9e"
            lbl.setStyleSheet(f"background:{color};color:white;padding:6px;border-radius:4px;")

    # ------------------------------------------------------------------ estacion
    def station_cmd(self, command: str, timeout: float = 10) -> None:
        if not self.session:
            return
        self.append_log(f"> {command}")
        self.run_bg(lambda: self.session.station.command(command, timeout=timeout),
                    lambda r: self.bridge.log.emit(f"< {r}"))

    def emergency_stop(self) -> None:
        if not self.session:
            return
        # STOP no espera al candado: se escribe directamente en el puerto.
        try:
            self.session.station.port.write(b"0 STOP\n")
        except OSError as exc:
            self.append_log(f"No se pudo enviar STOP: {exc}")
        if self.orch:
            self.orch.cancel()
        self.append_log("STOP enviado. Pulsa Reiniciar y HOME para continuar.")

    def save_position(self, key: str) -> None:
        def fn():
            st = self.session.station.status()
            pos = float(st["pos"])
            self.session.station.cfg_set(key, pos)
            self.session.station.cfg_save()
            return f"{key} = {pos:.1f} mm guardado en la estacion"

        self.run_bg(fn, lambda r: self.bridge.log.emit(str(r)))

    def run_test_cycles(self) -> None:
        if not self.session:
            return
        cycles = self.spin_cycles.value()
        self.cfg.queue.plates_in_magazine = self.spin_plates.value()
        orch = Orchestrator(self.session.printer, self.session.station, self.cfg,
                            on_event=self.bridge.event.emit)

        def reload() -> int:
            if self.session.simulated:
                self.session.sim_station.reload(self.spin_plates.value())
            else:
                self.bridge.log.emit("Cargador vacio: devuelve las placas y vuelve a lanzar los ciclos.")
                return 0
            return self.spin_plates.value()

        def fn():
            self.session.printer.send("G28")
            rows = orch.test_cycles(cycles, on_reload=reload)
            ok = sum(1 for r in rows if r["resultado"] == "ok")
            return f"Ciclos de prueba: {ok}/{len(rows)} correctos"

        self.run_bg(fn, lambda r: self.bridge.log.emit(str(r)))

    # ------------------------------------------------------------------ cola
    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Elegir trabajos", str(Path.home()), "G-code (*.gcode *.gco *.g)")
        for f in files:
            self.list_jobs.addItem(f)
        self.update_summary()

    def remove_file(self) -> None:
        for item in self.list_jobs.selectedItems():
            self.list_jobs.takeItem(self.list_jobs.row(item))
        self.update_summary()

    def move_file(self, delta: int) -> None:
        row = self.list_jobs.currentRow()
        if row < 0 or not 0 <= row + delta < self.list_jobs.count():
            return
        item = self.list_jobs.takeItem(row)
        self.list_jobs.insertItem(row + delta, item)
        self.list_jobs.setCurrentRow(row + delta)

    def _jobs(self) -> list:
        jobs = []
        for i in range(self.list_jobs.count()):
            info = analyze(Path(self.list_jobs.item(i).text()), self.cfg.printer.max_part_height,
                           self.cfg.printer.swap_y)
            jobs.extend([info] * self.spin_copies.value())
        return jobs

    def update_summary(self) -> None:
        try:
            jobs = self._jobs()
        except OSError as exc:
            self.lbl_summary.setText(f"Error leyendo archivos: {exc}")
            return
        total = sum(j.est_seconds or 0 for j in jobs)
        tall = [j.name for j in jobs if j.errors]
        text = f"{len(jobs)} trabajos, tiempo estimado {format_duration(total)}"
        if tall:
            text += f" | con errores: {', '.join(sorted(set(tall)))}"
        self.lbl_summary.setText(text)

    def start_queue(self) -> None:
        if not self.session:
            QMessageBox.information(self, "AutoSwap", "Conecta primero la impresora y la estacion.")
            return
        jobs = self._jobs()
        if not jobs:
            return
        self.cfg.queue.plates_in_magazine = self.spin_plates.value()
        self.orch = Orchestrator(self.session.printer, self.session.station, self.cfg,
                                 on_event=self.bridge.event.emit, decide=self.decide_from_thread,
                                 state_file=None if self.session.simulated else config_mod.state_path())
        self.queue_running = True
        self.set_controls_enabled(True)
        reloaded = self.chk_reloaded.isChecked()

        def fn():
            with keep_awake():
                try:
                    return self.orch.run(jobs, magazine_reloaded=reloaded)
                except PreflightError as exc:
                    self.bridge.log.emit("No se puede empezar la cola:\n- " + "\n- ".join(exc.problems))
                    return 0

        def done(result):
            self.queue_running = False
            self.bridge.connected.emit(True, "conectada")
            self.bridge.log.emit(f"Trabajos completados: {result}")

        self.run_bg(fn, done)

    def cancel_queue(self) -> None:
        if self.orch and self.queue_running:
            if QMessageBox.question(self, "AutoSwap", "¿Cancelar la cola? El trabajo actual se detendra.") == \
                    QMessageBox.StandardButton.Yes:
                self.orch.cancel()

    def decide_from_thread(self, problem: Problem) -> Decision:
        holder = {"event": threading.Event(), "decision": Decision.ABORT}
        self.bridge.problem.emit(problem, holder)
        holder["event"].wait()
        return holder["decision"]

    def on_problem(self, problem: Problem, holder: dict) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("AutoSwap: cola en pausa")
        box.setText(problem.message)
        box.setInformativeText(problem.help or "Revisa la estacion y elige como continuar.")
        retry = box.addButton("Reintentar", QMessageBox.ButtonRole.AcceptRole)
        manual = box.addButton("Ya lo hice a mano", QMessageBox.ButtonRole.YesRole) if problem.allow_manual else None
        box.addButton("Cancelar cola", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is retry:
            holder["decision"] = Decision.RETRY
        elif manual is not None and clicked is manual:
            holder["decision"] = Decision.DONE_MANUALLY
        else:
            holder["decision"] = Decision.ABORT
        holder["event"].set()

    def on_event(self, event: Event) -> None:
        if event.kind == "progress":
            d = event.data
            self.progress.setMaximum(max(1, d["total"]))
            self.progress.setValue(d["line"])
            self.lbl_temps.setText(f"Boquilla {d['nozzle']:.0f} °C | Cama {d['bed']:.0f} °C")
            return
        if event.kind == "phase":
            self.lbl_phase.setText(f"Fase: {event.message}")
        self.append_log(f"[{event.kind}] {event.message}")
        if event.kind in ("problem", "done"):
            title = "AutoSwap: problema" if event.kind == "problem" else "AutoSwap"
            if self.cfg.notifications.desktop:
                notify_desktop(title, event.message)
            notify_ntfy(self.cfg.notifications.ntfy_topic, title, event.message)

    def closeEvent(self, event) -> None:  # noqa: N802 - nombre de Qt
        if self.queue_running:
            QMessageBox.warning(self, "AutoSwap", "Hay una cola en marcha: cancelala antes de salir.")
            event.ignore()
            return
        if self.session:
            self.session.close()
        if self.filelog:
            self.filelog.close()
        event.accept()


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

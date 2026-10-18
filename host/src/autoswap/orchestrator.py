"""Cola de trabajos y secuencia de cambio de placa (seccion 6.3 del plan).

El orquestador envia cada trabajo a la impresora linea por linea y, entre trabajos,
ordena a la estacion EXPULSAR y CARGAR verificando los sensores. Ante cualquier falla
pausa la cola, deja la impresora en un estado seguro y pregunta al usuario que hacer.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path

from .config import AppConfig
from .gcode import JobInfo, job_commands
from .marlin import MarlinLink, PrinterError, PrinterHalted
from .station import ERROR_HELP, StationError, StationLink


class Phase(StrEnum):
    IDLE = "idle"
    CHECKING = "comprobando"
    PRINTING = "imprimiendo"
    PREPARING = "preparando cambio"
    EJECTING = "expulsando"
    LOADING = "cargando"
    WARMING = "calentando placa"
    PAUSED = "pausado"
    FINISHED = "cola terminada"
    CANCELLED = "cancelada"


class Decision(StrEnum):
    RETRY = "retry"  # el usuario corrigio el problema: repetir el paso
    DONE_MANUALLY = "manual"  # el usuario hizo el cambio a mano: continuar
    ABORT = "abort"


@dataclass
class Event:
    kind: str  # "phase", "progress", "log", "warning", "problem", "job", "swap", "done"
    message: str = ""
    data: dict = field(default_factory=dict)


@dataclass
class Problem:
    step: str
    message: str
    code: str = ""
    help: str = ""
    allow_manual: bool = True


class QueueAborted(RuntimeError):
    pass


class PreflightError(RuntimeError):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


@dataclass
class QueueState:
    files: list[str]
    next_index: int = 0
    plates_left: int = 0
    swaps_ok: int = 0
    started: float = field(default_factory=time.time)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> QueueState | None:
        if not path.exists():
            return None
        return cls(**json.loads(path.read_text(encoding="utf-8")))


def _default_decide(problem: Problem) -> Decision:
    return Decision.ABORT


class Orchestrator:
    def __init__(
        self,
        printer: MarlinLink,
        station: StationLink,
        cfg: AppConfig,
        on_event: Callable[[Event], None] | None = None,
        decide: Callable[[Problem], Decision] | None = None,
        state_file: Path | None = None,
    ):
        self.printer = printer
        self.station = station
        self.cfg = cfg
        self.on_event = on_event or (lambda _e: None)
        self.decide = decide or _default_decide
        self.state_file = state_file
        self.phase = Phase.IDLE
        self._cancel = threading.Event()
        self._pause_after_job = threading.Event()
        self.plates_left = cfg.queue.plates_in_magazine
        self.swap_times: list[float] = []

    # ------------------------------------------------------------------ eventos
    def emit(self, kind: str, message: str = "", **data) -> None:
        self.on_event(Event(kind, message, data))

    def set_phase(self, phase: Phase, message: str = "") -> None:
        self.phase = phase
        self.emit("phase", message or phase.value, phase=phase.value)

    def cancel(self) -> None:
        self._cancel.set()

    def pause_after_current_job(self, enabled: bool = True) -> None:
        if enabled:
            self._pause_after_job.set()
        else:
            self._pause_after_job.clear()

    # ------------------------------------------------------------------ comprobaciones
    def preflight(self, jobs: list[JobInfo], first_plate_on_bed: bool = True) -> list[str]:
        """Devuelve avisos. Lanza PreflightError si algo impide empezar."""
        problems: list[str] = []
        warnings: list[str] = []
        if not jobs:
            problems.append("La cola esta vacia")
        for job in jobs:
            for error in job.errors:
                problems.append(f"{job.name}: {error}")
            for warning in job.warnings:
                warnings.append(f"{job.name}: {warning}")
        needed = max(0, len(jobs) - (1 if first_plate_on_bed else 0))
        if needed > self.plates_left:
            problems.append(
                f"Hacen falta {needed} placas en el cargador y hay {self.plates_left}. "
                "Recarga el cargador o reduce la cola"
            )
        try:
            status = self.station.status()
        except (StationError, TimeoutError) as exc:
            problems.append(f"La estacion no responde: {exc}")
            status = {}
        if status:
            if status.get("err", "none") != "none":
                problems.append(f"La estacion esta en falla ({status.get('err')}): pulsa Reiniciar y HOME")
            if status.get("stop") == "1":
                problems.append("El boton STOP de la estacion esta pulsado")
            if first_plate_on_bed and status.get("bed") != "1":
                problems.append("No se detecta placa en la cama (sensor PLACA_EN_CAMA)")
            if status.get("flap") != "closed":
                problems.append("El volteador de la estacion no esta cerrado")
        if problems:
            raise PreflightError(problems)
        return warnings

    # ------------------------------------------------------------------ cola
    def run(self, jobs: list[JobInfo], start_index: int = 0, magazine_reloaded: bool = True) -> int:
        """Imprime la cola. Devuelve el numero de trabajos completados.

        magazine_reloaded=True: el usuario acaba de llenar el cargador desde el estante
        inferior (nivel 0) con cfg.queue.plates_in_magazine placas. False: se continua
        desde el nivel en que se quedo la estacion.
        """
        self._cancel.clear()
        self.set_phase(Phase.CHECKING)
        status = self.station.status()
        if status.get("homed") != "1":
            self.emit("log", "La estacion no tiene HOME: haciendo HOME...")
            self.station.home(timeout=self.cfg.station.home_timeout_s)
            status = self.station.status()
        slots = int(status.get("slots", "6"))
        if magazine_reloaded:
            self.plates_left = min(self.cfg.queue.plates_in_magazine, slots)
            if status.get("level") != "0":
                self.station.lift_level(0)
        else:
            self.plates_left = min(self.plates_left, slots - int(status.get("level", "0")))
        warnings = self.preflight(jobs[start_index:], first_plate_on_bed=True)
        for warning in warnings:
            self.emit("warning", warning)

        state = QueueState([str(j.path) for j in jobs], start_index, self.plates_left)
        completed = 0
        try:
            for index in range(start_index, len(jobs)):
                job = jobs[index]
                if index > start_index:
                    self._swap_with_recovery(jobs[index - 1])
                    state.swaps_ok += 1
                self._check_cancel()
                self.emit("job", f"Trabajo {index + 1}/{len(jobs)}: {job.name}", index=index, total=len(jobs))
                self._print_job(job)
                completed += 1
                state.next_index = index + 1
                state.plates_left = self.plates_left
                if self.state_file:
                    state.save(self.state_file)
                if self._pause_after_job.is_set() and index + 1 < len(jobs):
                    self._pause_after_job.clear()
                    decision = self._ask(Problem("pausa", "Cola en pausa a peticion del usuario",
                                                 allow_manual=False))
                    if decision == Decision.ABORT:
                        raise QueueAborted("Cancelada por el usuario")
            self._finish_queue()
            self.set_phase(Phase.FINISHED, f"Cola terminada: {completed} trabajos")
            self.emit("done", f"Cola terminada: {completed} trabajos", completed=completed)
            if self.state_file and self.state_file.exists():
                self.state_file.unlink()
        except QueueAborted as exc:
            self._safe_stop()
            self.set_phase(Phase.CANCELLED, str(exc))
            self.emit("done", str(exc), completed=completed, cancelled=True)
        except PrinterHalted as exc:
            self.set_phase(Phase.CANCELLED, f"La impresora se detuvo por seguridad: {exc}")
            self.emit("problem", f"ALERTA: la impresora se detuvo ({exc}). Revisala antes de seguir.")
            self.emit("done", "Cola cancelada por la impresora", completed=completed, cancelled=True)
            raise
        return completed

    def _check_cancel(self) -> None:
        if self._cancel.is_set():
            raise QueueAborted("Cancelada por el usuario")

    def _ask(self, problem: Problem) -> Decision:
        self.set_phase(Phase.PAUSED, problem.message)
        self.emit("problem", problem.message, step=problem.step, code=problem.code, help=problem.help)
        decision = self.decide(problem)
        self.emit("log", f"Decision del usuario: {decision.value}")
        return decision

    # ------------------------------------------------------------------ impresion
    def _print_job(self, job: JobInfo) -> None:
        self.set_phase(Phase.PRINTING, f"Imprimiendo {job.name}")
        strip = self.cfg.queue.strip_end_gcode
        total = max(1, job.lines)
        last_report = 0.0
        for count, command in enumerate(job_commands(job, strip, self.cfg.printer.swap_y), start=1):
            if self._cancel.is_set():
                raise QueueAborted("Cancelada por el usuario")
            self.printer.send(command)
            now = time.monotonic()
            if now - last_report > 1.0 or count == total:
                last_report = now
                t = self.printer.temps
                self.emit("progress", "", job=job.name, line=count, total=total,
                          nozzle=t.nozzle, bed=t.bed)
        self.printer.send("M400")

    def _finish_queue(self) -> None:
        commands = ["M104 S0", "M106 S0"]
        if self.cfg.queue.turn_off_bed_at_end:
            commands.append("M140 S0")
        commands += ["M84 S600", "M117 AutoSwap: cola terminada"]
        for cmd in commands:
            self.printer.send(cmd)
        self.emit("log", f"Calentadores apagados. Placas restantes en el cargador: {self.plates_left}")

    def _safe_stop(self) -> None:
        """Estado seguro tras cancelar: calentadores apagados, boquilla arriba."""
        for cmd in ("M104 S0", "M140 S0", "M106 S0", "G91", "G1 Z5 F600", "G90", "M117 AutoSwap: cancelado"):
            try:
                self.printer.send(cmd, timeout=30)
            except (PrinterError, TimeoutError):
                break

    # ------------------------------------------------------------------ cambio de placa
    def prepare_printer(self, job: JobInfo) -> None:
        p = self.cfg.printer
        z_safe = min(p.z_max, job.max_z + p.z_clearance)
        for line in (
            "M400",
            "M83",  # extrusor relativo solo para retraer
            "G1 E-2 F2400",
            "G90",
            f"G1 Z{z_safe:.2f} F{p.z_feed:.0f}",
            f"G1 X{p.park_x:.1f} F6000",
            f"G1 Y{p.swap_y:.1f} F{p.y_feed:.0f}",
            "M400",
            "M84 S600",  # motores con fuerza 10 min: la cama no se mueve durante el cambio
            "M117 AutoSwap: cambiando placa",
        ):
            self.printer.send(line, timeout=180)

    def swap_plate(self, job: JobInfo) -> None:
        """Un cambio completo. Lanza StationError/RuntimeError si algo falla."""
        st = self.cfg.station
        started = time.monotonic()
        self.set_phase(Phase.PREPARING)
        self.prepare_printer(job)
        status = self.station.status()
        if status.get("bed") != "1":
            raise StationError("E04", "NO_PLATE_ON_BED", "status bed=0 antes de expulsar")
        self.set_phase(Phase.EJECTING)
        self.station.eject(timeout=st.eject_timeout_s)
        self.set_phase(Phase.LOADING)
        self.station.load(timeout=st.load_timeout_s)
        self.plates_left -= 1
        status = self.station.status()
        if status.get("bed") != "1" or status.get("drop") != "0":
            raise RuntimeError(f"Estado inesperado tras el cambio: {status}")
        elapsed = time.monotonic() - started
        self.swap_times.append(elapsed)
        self.emit("swap", f"Cambio de placa completado en {elapsed:.0f} s", seconds=elapsed,
                  plates_left=self.plates_left)
        self.set_phase(Phase.WARMING)
        self.printer.send("M117 AutoSwap: placa nueva lista")
        warm = self.cfg.printer.plate_warmup_s
        if warm > 0:
            self.printer.send(f"G4 S{warm}", timeout=warm + 60)

    def _swap_with_recovery(self, job: JobInfo) -> None:
        while True:
            self._check_cancel()
            try:
                self.swap_plate(job)
                return
            except StationError as exc:
                problem = Problem("cambio de placa", f"La estacion informo {exc.code} {exc.name}",
                                  code=exc.code, help=ERROR_HELP.get(exc.code, ""))
            except (RuntimeError, TimeoutError) as exc:
                if isinstance(exc, PrinterHalted):
                    raise
                problem = Problem("cambio de placa", str(exc))
            self._make_printer_safe_for_pause()
            decision = self._ask(problem)
            if decision == Decision.ABORT:
                raise QueueAborted(f"Cancelada tras error en el cambio: {problem.message}")
            if decision == Decision.DONE_MANUALLY:
                self.plates_left = max(0, self.plates_left - 1)
                status = self.station.status()
                if status.get("bed") != "1":
                    self.emit("warning", "Sigue sin detectarse placa en la cama: revisa antes de continuar")
                    continue
                return
            # RETRY: reiniciar la estacion si quedo en falla y volver a intentar
            self._recover_station()

    def _make_printer_safe_for_pause(self) -> None:
        try:
            self.printer.send("M104 S0", timeout=10)  # boquilla apagada; la cama se mantiene
            self.printer.send("M117 AutoSwap: pausa por error", timeout=10)
        except (PrinterError, TimeoutError):
            pass

    def _recover_station(self) -> None:
        status = self.station.status()
        if status.get("err", "none") != "none":
            self.station.reset()
            self.station.home(timeout=self.cfg.station.home_timeout_s)

    # ------------------------------------------------------------------ prueba de ciclos
    def test_cycles(self, cycles: int, on_reload: Callable[[], int] | None = None) -> list[dict]:
        """Ciclos de cambio sin imprimir (fase 6 del plan). Devuelve una fila por ciclo."""
        rows: list[dict] = []
        dummy = JobInfo(Path("prueba"), max_z=5.0)
        status = self.station.status()
        if status.get("homed") != "1":
            self.station.home(timeout=self.cfg.station.home_timeout_s)
        for cycle in range(1, cycles + 1):
            self._check_cancel()
            if self.plates_left <= 0:
                if not on_reload:
                    break
                self.plates_left = on_reload()  # el usuario recargo desde el estante inferior
                self.station.lift_level(0)
            started = time.monotonic()
            row = {"ciclo": cycle, "resultado": "ok", "error": "", "segundos": 0.0}
            try:
                self.swap_plate(dummy)
            except (StationError, RuntimeError, TimeoutError) as exc:
                if isinstance(exc, PrinterHalted):
                    raise
                row["resultado"] = "fallo"
                row["error"] = str(exc)
                self.emit("warning", f"Ciclo {cycle}: {exc}")
                self._recover_station()
            row["segundos"] = round(time.monotonic() - started, 1)
            rows.append(row)
            self.emit("log", f"Ciclo {cycle}/{cycles}: {row['resultado']} ({row['segundos']} s)")
        return rows

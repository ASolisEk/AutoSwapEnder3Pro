"""Linea de ordenes: `autoswap <orden> ...` (macOS y Windows)."""

from __future__ import annotations

import argparse
import csv
import sys
import threading
import time
from pathlib import Path

from . import __version__
from . import config as config_mod
from .gcode import analyze, format_duration
from .orchestrator import Decision, Event, Orchestrator, PreflightError, Problem, QueueState
from .platform_utils import keep_awake, notify_desktop, notify_ntfy, upload_firmware
from .session import FileLog, connect
from .station import StationError, StationLink
from .transport import open_serial

REPO_HEX = Path(__file__).resolve().parents[3] / "firmware" / "station" / ".pio" / "build" / "uno" / "firmware.hex"


def _print_event(event: Event) -> None:
    if event.kind == "progress":
        d = event.data
        pct = 100.0 * d["line"] / max(1, d["total"])
        text = f"\r  {d['job']}: {pct:5.1f} %  boquilla {d['nozzle']:.0f} °C  cama {d['bed']:.0f} °C   "
        if sys.stdout.isatty():
            print(text, end="", flush=True)
        return
    prefix = {"warning": "AVISO: ", "problem": "PROBLEMA: ", "swap": "OK ", "phase": "-> "}.get(event.kind, "")
    if sys.stdout.isatty():
        print()
    print(f"{prefix}{event.message}")
    if event.kind == "problem" and event.data.get("help"):
        print(f"   {event.data['help']}")


def _ask_user(problem: Problem) -> Decision:
    print()
    print(f"*** La cola esta en pausa: {problem.message}")
    if problem.help:
        print(f"    {problem.help}")
    options = "[r] reintentar  " + ("[m] ya lo resolvi a mano, continuar  " if problem.allow_manual else "")
    options += "[c] cancelar la cola"
    while True:
        try:
            answer = input(f"    {options}: ").strip().lower()
        except EOFError:
            return Decision.ABORT
        if answer in ("r", "reintentar", "s", "si"):
            return Decision.RETRY
        if answer in ("m", "manual") and problem.allow_manual:
            return Decision.DONE_MANUALLY
        if answer in ("c", "cancelar"):
            return Decision.ABORT


def _confirm(question: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    try:
        return input(f"{question} [s/N]: ").strip().lower() in ("s", "si", "sí", "y", "yes")
    except EOFError:
        return False


def _notifier(cfg: config_mod.AppConfig):
    def handler(event: Event) -> None:
        _print_event(event)
        if event.kind in ("problem", "done"):
            title = "AutoSwap: problema" if event.kind == "problem" else "AutoSwap"
            if cfg.notifications.desktop:
                notify_desktop(title, event.message)
            notify_ntfy(cfg.notifications.ntfy_topic, title, event.message)

    return handler


# ---------------------------------------------------------------------- ordenes
def cmd_ports(_args) -> int:
    from .ports import candidates

    found = candidates()
    if not found:
        print("No se detectaron puertos USB serie. Revisa el cable (de datos) y el driver CH340.")
        return 1
    for c in found:
        print(f"{c.device:28s} {c.chip:22s} {c.description}")
    return 0


def cmd_identify(args) -> int:
    from .ports import candidates, identify

    for c in candidates():
        try:
            kind = identify(c.device, args.baud)
        except OSError as exc:
            kind = f"no se pudo abrir ({exc})"
        name = {"printer": "IMPRESORA", "station": "ESTACION", "unknown": "desconocido"}.get(kind, kind)
        print(f"{c.device:28s} {c.chip:22s} -> {name}")
    return 0


def cmd_analyze(args) -> int:
    cfg = config_mod.load()
    worst = 0
    for name in args.files:
        info = analyze(Path(name), cfg.printer.max_part_height, cfg.printer.swap_y)
        print(f"{info.name}: {info.lines} ordenes, altura {info.max_z:.1f} mm, "
              f"tiempo {format_duration(info.est_seconds)}")
        for e in info.errors:
            print(f"   ERROR: {e}")
            worst = 2
        for w in info.warnings:
            print(f"   aviso: {w}")
            worst = max(worst, 1)
        for r in info.removed_tail:
            print(f"      se omite: {r}")
    return 2 if worst == 2 else 0


def _open_station(args, cfg) -> tuple[StationLink, object]:
    if args.simulate:
        from .sim import SimStation

        sim = SimStation(speed=50)
        link = StationLink(sim, on_line=lambda t: None)
        link.handshake(wait_s=0)
        return link, sim
    port = args.port or cfg.station.port
    if port == "auto":
        from .ports import find_devices

        _, port = find_devices("none", "auto", cfg.station.baud, log=print)
        if not port:
            raise ConnectionError("No se encontro la estacion")
    link = StationLink(open_serial(port, cfg.station.baud))
    link.handshake()
    return link, None


def cmd_station(args) -> int:
    cfg = config_mod.load()
    link, _sim = _open_station(args, cfg)
    command = " ".join(args.command)
    timeout = 240.0 if command.split()[0].upper() in ("HOME", "EJECT", "LOAD", "LIFT", "MOVE", "GOTO") else 15.0
    try:
        print(link.command(command, timeout=timeout))
        return 0
    except StationError as exc:
        print(f"ERROR {exc}")
        return 1
    finally:
        link.close()


def cmd_console(args) -> int:
    ser = open_serial(args.port, args.baud)
    stop = threading.Event()

    def reader():
        while not stop.is_set():
            raw = ser.readline()
            if raw:
                print(f"< {raw.decode('ascii', errors='replace').rstrip()}")

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    print(f"Consola en {args.port} a {args.baud} baudios. Escribe ordenes; 'salir' para terminar.")
    try:
        while True:
            line = input()
            if line.strip().lower() in ("salir", "exit", "quit"):
                break
            ser.write((line.strip() + "\n").encode("ascii", errors="replace"))
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        stop.set()
        time.sleep(0.3)
        ser.close()
    return 0


def _load_jobs(files: list[str], copies: int, cfg) -> list:
    jobs = []
    for name in files:
        info = analyze(Path(name), cfg.printer.max_part_height, cfg.printer.swap_y)
        jobs.extend([info] * max(1, copies))
    return jobs


def cmd_queue(args) -> int:
    cfg = config_mod.load()
    if args.plates is not None:
        cfg.queue.plates_in_magazine = args.plates
    if args.printer:
        cfg.printer.port = args.printer
    if args.station:
        cfg.station.port = args.station
    start_index = 0
    reloaded = not args.no_reload
    state_file = config_mod.state_path()
    files = list(args.files)
    if args.resume:
        state = QueueState.load(state_file)
        if not state:
            print("No hay ninguna cola guardada para reanudar.")
            return 1
        files, start_index = state.files, state.next_index
        cfg.queue.plates_in_magazine = state.plates_left
        reloaded = False
        print(f"Reanudando desde el trabajo {start_index + 1} de {len(files)}")
    if not files:
        print("Indica al menos un archivo .gcode")
        return 1
    jobs = _load_jobs(files, 1 if args.resume else args.copies, cfg)
    total = sum(j.est_seconds or 0 for j in jobs[start_index:])
    print(f"Cola: {len(jobs) - start_index} trabajos, tiempo estimado {format_duration(total)}, "
          f"placas en el cargador: {cfg.queue.plates_in_magazine}")
    for j in jobs[start_index:]:
        for e in j.errors:
            print(f"  ERROR {j.name}: {e}")
    if any(j.errors for j in jobs[start_index:]):
        return 2
    if not _confirm("¿Empezar la cola? La impresora se reiniciara al conectarse.", args.yes):
        return 1

    filelog = None if args.simulate else FileLog()
    session = connect(cfg, simulate=args.simulate, raw_log=filelog, sim_speed=args.sim_speed)
    orch = Orchestrator(session.printer, session.station, cfg, on_event=_notifier(cfg),
                        decide=_ask_user, state_file=None if args.simulate else state_file)
    try:
        with keep_awake():
            done = orch.run(jobs, start_index=start_index, magazine_reloaded=reloaded)
        if orch.swap_times:
            avg = sum(orch.swap_times) / len(orch.swap_times)
            print(f"Cambios: {len(orch.swap_times)}, tiempo medio {avg:.0f} s")
        print(f"Trabajos completados: {done}")
        return 0
    except PreflightError as exc:
        print("No se puede empezar la cola:")
        for p in exc.problems:
            print(f"  - {p}")
        return 2
    except KeyboardInterrupt:
        orch.cancel()
        print("\nCancelado.")
        return 130
    finally:
        session.close()
        if filelog:
            print(f"Registro: {filelog.path}")
            filelog.close()


def cmd_test_swap(args) -> int:
    cfg = config_mod.load()
    cfg.queue.plates_in_magazine = args.plates
    if not _confirm(f"Se haran {args.cycles} cambios de placa sin imprimir. ¿Continuar?", args.yes):
        return 1
    session = connect(cfg, simulate=args.simulate, sim_speed=args.sim_speed)
    orch = Orchestrator(session.printer, session.station, cfg, on_event=_print_event)

    def reload() -> int:
        if args.simulate:
            session.sim_station.reload(args.plates)
            return args.plates
        input(f"Cargador vacio: devuelve las placas de la caja al cargador ({args.plates}) y pulsa Enter...")
        return args.plates

    try:
        session.printer.send("G28")
        status = session.station.status()
        if status.get("homed") != "1":
            session.station.home(timeout=cfg.station.home_timeout_s)
        session.station.lift_level(0)
        with keep_awake():
            rows = orch.test_cycles(args.cycles, on_reload=reload)
    finally:
        session.close()
    ok = sum(1 for r in rows if r["resultado"] == "ok")
    rate = 100.0 * ok / max(1, len(rows))
    print(f"Resultado: {ok}/{len(rows)} ciclos correctos ({rate:.1f} %)")
    if args.report:
        with open(args.report, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["ciclo", "resultado", "segundos", "error"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"Informe: {args.report}")
    return 0 if ok == len(rows) else 1


MANUAL_SWAP_BLOCK = """
; ===== AUTOSWAP: cambio MANUAL de placa (modo sin estacion) =====
M400
G91
G1 Z10 F600
G90
G1 X5 F6000
G1 Y{swap_y:.0f} F3000
M104 S0
M117 Cambia la placa PEI
M0 Cambia la placa PEI y pulsa el boton
; ===== fin del cambio manual =====
"""


def cmd_merge(args) -> int:
    """Une varios G-code en uno (modo microSD). Sin estacion, el cambio es manual (M0)."""
    cfg = config_mod.load()
    jobs: list[Path] = []
    for name in args.files:
        jobs.extend([Path(name)] * max(1, args.copies))
    out = [f"; Generado por AutoSwapEnder3Pro {__version__} (autoswap merge)",
           f"; Trabajos: {len(jobs)}. Entre trabajos la impresora espera (M0) a que cambies la placa."]
    for i, path in enumerate(jobs, start=1):
        out.append(f"\n; ===== TRABAJO {i}/{len(jobs)}: {path.name} =====")
        out.append(path.read_text(encoding="utf-8", errors="replace"))
        if i < len(jobs):
            out.append(MANUAL_SWAP_BLOCK.format(swap_y=cfg.printer.swap_y))
    Path(args.output).write_text("\n".join(out), encoding="utf-8")
    print(f"Archivo combinado: {args.output} ({len(jobs)} trabajos)")
    return 0


def cmd_config(args) -> int:
    cfg = config_mod.load()
    if args.action == "path":
        print(config_mod.config_path())
    elif args.action == "show":
        print(config_mod.dumps(cfg))
    elif args.action == "set":
        for item in args.values:
            key, _, value = item.partition("=")
            cfg.set_value(key.strip(), value.strip())
        print(f"Guardado en {config_mod.save(cfg)}")
    elif args.action == "reset":
        print(f"Valores por defecto guardados en {config_mod.save(config_mod.AppConfig())}")
    return 0


def cmd_firmware_upload(args) -> int:
    hex_path = Path(args.hex) if args.hex else REPO_HEX
    if not hex_path.exists():
        print(f"No existe {hex_path}. Compila primero con 'pio run -e uno' o indica --hex.")
        return 1
    print(f"Cargando {hex_path} en {args.port}...")
    result = upload_firmware(args.port, hex_path)
    print(result.stdout[-2000:] + result.stderr[-2000:])
    print("Firmware cargado." if result.returncode == 0 else "La carga fallo (revisa el puerto y el cable).")
    return result.returncode


def cmd_gui(_args) -> int:
    from .gui.app import main as gui_main

    return gui_main()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autoswap", description="AutoSwapEnder3Pro: cola de impresion con cambio de placa")
    p.add_argument("--version", action="version", version=f"autoswap {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ports", help="Listar puertos USB serie").set_defaults(func=cmd_ports)
    s = sub.add_parser("identify", help="Identificar impresora y estacion (no usar imprimiendo)")
    s.add_argument("--baud", type=int, default=115200)
    s.set_defaults(func=cmd_identify)

    s = sub.add_parser("analyze", help="Analizar archivos .gcode")
    s.add_argument("files", nargs="+")
    s.set_defaults(func=cmd_analyze)

    s = sub.add_parser("station", help="Enviar una orden a la estacion (p. ej. HOME, STATUS, CFG LIST)")
    s.add_argument("command", nargs="+")
    s.add_argument("--port")
    s.add_argument("--simulate", action="store_true")
    s.set_defaults(func=cmd_station)

    s = sub.add_parser("console", help="Consola serie interactiva")
    s.add_argument("--port", required=True)
    s.add_argument("--baud", type=int, default=115200)
    s.set_defaults(func=cmd_console)

    s = sub.add_parser("queue", help="Imprimir una cola con cambio automatico de placa")
    s.add_argument("files", nargs="*")
    s.add_argument("--copies", type=int, default=1, help="Copias de cada archivo")
    s.add_argument("--plates", type=int, help="Placas en el cargador (por defecto, la configuracion)")
    s.add_argument("--printer", help="Puerto de la impresora")
    s.add_argument("--station", help="Puerto de la estacion")
    s.add_argument("--resume", action="store_true", help="Reanudar la ultima cola interrumpida")
    s.add_argument("--no-reload", action="store_true", help="No recargue el cargador: seguir desde su nivel")
    s.add_argument("--simulate", action="store_true", help="Impresora y estacion virtuales")
    s.add_argument("--sim-speed", type=float, default=50.0, help=argparse.SUPPRESS)
    s.add_argument("--yes", "-y", action="store_true", help="No pedir confirmacion")
    s.set_defaults(func=cmd_queue)

    s = sub.add_parser("test-swap", help="Ciclos de cambio sin imprimir (calibracion y fiabilidad)")
    s.add_argument("--cycles", type=int, default=20)
    s.add_argument("--plates", type=int, default=6)
    s.add_argument("--report", help="Guardar un informe CSV")
    s.add_argument("--simulate", action="store_true")
    s.add_argument("--sim-speed", type=float, default=50.0, help=argparse.SUPPRESS)
    s.add_argument("--yes", "-y", action="store_true")
    s.set_defaults(func=cmd_test_swap)

    s = sub.add_parser("merge", help="Unir G-codes en un archivo para la microSD (cambio manual con M0)")
    s.add_argument("files", nargs="+")
    s.add_argument("--copies", type=int, default=1)
    s.add_argument("-o", "--output", default="cola_autoswap.gcode")
    s.set_defaults(func=cmd_merge)

    s = sub.add_parser("config", help="Ver o cambiar la configuracion")
    s.add_argument("action", choices=["show", "path", "set", "reset"])
    s.add_argument("values", nargs="*", help="seccion.clave=valor (con 'set')")
    s.set_defaults(func=cmd_config)

    s = sub.add_parser("firmware-upload", help="Cargar el firmware de la estacion (avrdude)")
    s.add_argument("--port", required=True)
    s.add_argument("--hex")
    s.set_defaults(func=cmd_firmware_upload)

    sub.add_parser("gui", help="Abrir la interfaz grafica").set_defaults(func=cmd_gui)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ConnectionError, OSError, StationError, TimeoutError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

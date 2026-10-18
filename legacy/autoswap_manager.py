#!/usr/bin/env python3
"""
AutoSwapEnder3Pro - Controlador Serial y Combinador de G-Code para macOS
Licencia MIT - Copyright (c) 2026 Angel Solis Ek

Funciones principales:
1. Modo 'merge': Combina multiples archivos .gcode laminados para la Creality
   Ender 3 Pro e inyecta la rutina cinematica de cambio automatico de placa PEI
   (235x235 mm) entre cada impresion.
2. Modo 'bridge': Demonio en macOS (usando pySerial) que escucha en tiempo real
   el puerto USB de la Ender 3 Pro (/dev/cu.usbserial-*) y coordina el
   microcontrolador ESP32-DevKitC (/dev/cu.SLAB_USBtoUART) cuando recibe los
   marcadores M118 //AUTOSWAP:ENGAGE y //AUTOSWAP:RELEASE.
3. Modo 'test': Ejecuta un ciclo de prueba del servomotor MG996R y lee el estado
   de los finales de carrera (presencia de placas y posicion trasera de cama).
"""

import argparse
import pathlib
import sys
import time
import serial
import serial.tools.list_ports

SWAP_GCODE_BLOCK = """
; =====================================================================
; INICIO BLOQUE AUTOSWAP PARA CREALITY ENDER 3 PRO (235x235mm PEI)
; =====================================================================
M400                        ; Esperar a que terminen todos los movimientos en cola
G91                         ; Coordenadas relativas
G1 E-3 F1800                ; Retraer 3 mm de filamento para evitar hilos
G1 Z15 F600                 ; Elevar boquilla 15 mm por seguridad
G90                         ; Coordenadas absolutas
G1 X10 F3000                ; Aparcar cabezal X a la izquierda

; --- FASE 1: Activar mecanismo de cambio en ESP32 via USB Serial ---
M118 //AUTOSWAP:ENGAGE      ; Ordena a macOS accionar el servomotor MG996R
M400
G4 P1500                    ; Pausa de 1.5 s para posicionamiento de leva

; --- FASE 2: Despegar placa actual y enganchar placa nueva en Y=0 ---
G1 Y230 F2500               ; Avanzar cama hacia las cunas frontales de despegue
M400
G1 Y0 F2000                 ; Retroceder cama al fondo para acoplar imanes (20x10x2mm)
M400
G4 P800                     ; Pausa de acoplamiento magnetico

; --- FASE 3: Extraer placa nueva del cargador y expulsar la usada ---
G1 Y235 F1800               ; Avanzar al maximo: la placa nueva empuja la anterior
M400
M118 //AUTOSWAP:RELEASE     ; Ordena al ESP32 devolver el servo a reposo
G4 P1000

; --- FASE 4: Asentar placa nueva sobre la cama magnetica ---
G1 Y15 F2500                ; Retroceso de asentamiento y desacople del gancho
G1 Y110 F3000               ; Centrar cama para iniciar el siguiente trabajo
M400
; =====================================================================
"""


def list_macos_serial_ports() -> None:
    """Lista los puertos seriales USB disponibles en macOS (/dev/cu.*)."""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No se detectaron puertos USB Serial conectados.")
        return
    print("Puertos USB Serial detectados en macOS:")
    for port in ports:
        print(f"  - {port.device}: {port.description} [{port.hwid}]")


def merge_gcode_files(input_files: list[str], clones: int, output_path: str) -> None:
    """Combina multiples archivos G-code e inserta la rutina de cambio de placa."""
    jobs: list[tuple[str, str]] = []
    for file_path in input_files:
        p = pathlib.Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"No se encontro el archivo G-code: {file_path}")
        content = p.read_text(encoding="utf-8", errors="ignore")
        for _ in range(clones):
            jobs.append((p.name, content))

    merged_lines = [
        "; Archivo generado por AutoSwapEnder3Pro GCode Merger (macOS)",
        f"; Total de placas PEI encadenadas: {len(jobs)}",
    ]

    for idx, (name, content) in enumerate(jobs, start=1):
        merged_lines.append(f"\n; === INICIO TRABAJO {idx}/{len(jobs)}: {name} ===")
        merged_lines.append(content)
        if idx < len(jobs):
            merged_lines.append(SWAP_GCODE_BLOCK)

    out = pathlib.Path(output_path)
    out.write_text("\n".join(merged_lines), encoding="utf-8")
    print(f"[OK] Archivo G-code multipieza generado: {out.resolve()} ({len(jobs)} ciclos)")


def send_esp32_command(esp: serial.Serial, command: str) -> str:
    """Envia un comando al ESP32 y devuelve la respuesta."""
    esp.reset_input_buffer()
    esp.write(f"{command.strip()}\n".encode("utf-8"))
    esp.flush()
    deadline = time.time() + 5.0
    while time.time() < deadline:
        line = esp.readline().decode("utf-8", errors="ignore").strip()
        if line:
            return line
    return "TIMEOUT"


def run_serial_bridge(
    printer_port: str,
    esp32_port: str,
    baud_printer: int = 115200,
    baud_esp32: int = 115200,
) -> None:
    """Escucha los comandos M118 de la Ender 3 Pro en macOS y acciona el ESP32."""
    print(f"Conectando a Ender 3 Pro ({printer_port}) y ESP32 ({esp32_port})...")
    with serial.Serial(printer_port, baud_printer, timeout=1) as printer, \
         serial.Serial(esp32_port, baud_esp32, timeout=1) as esp:
        time.sleep(2.0)
        status = send_esp32_command(esp, "STATUS")
        print(f"[ESP32 Estado Inicial] {status}")
        print("Puente AutoSwap activo en macOS. Esperando eventos M118 de la impresora...")

        while True:
            raw = printer.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            print(f"[Ender3Pro] {line}")

            if "//AUTOSWAP:ENGAGE" in line:
                print("-> Activando servomotor de cambio de placa en ESP32...")
                resp = send_esp32_command(esp, "ENGAGE")
                print(f"[ESP32] {resp}")
                if "ERROR:NO_PLATES" in resp:
                    print("[ALERTA] Cargador sin placas PEI disponibles. Pausando impresora (M0)...")
                    printer.write(b"M0 Sin placas en cargador AutoSwap\n")
                    printer.flush()

            elif "//AUTOSWAP:RELEASE" in line:
                print("-> Liberando servomotor a posicion de reposo...")
                resp = send_esp32_command(esp, "RELEASE")
                print(f"[ESP32] {resp}")


def run_test_cycle(esp32_port: str, baud_esp32: int = 115200) -> None:
    """Ejecuta una verificacion de sensores y del servomotor MG996R desde macOS."""
    with serial.Serial(esp32_port, baud_esp32, timeout=2) as esp:
        time.sleep(2.0)
        print("1. Consultando sensores del ESP32...")
        print("   ->", send_esp32_command(esp, "STATUS"))
        print("2. Ejecutando ciclo de prueba del servomotor MG996R...")
        print("   ->", send_esp32_command(esp, "TEST_CYCLE"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Controlador y Combinador G-Code AutoSwapEnder3Pro para macOS"
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    sub.add_parser("ports", help="Listar puertos USB Serial detectados en macOS")

    merge_p = sub.add_parser("merge", help="Combinar archivos .gcode con rutina AutoSwap")
    merge_p.add_argument("files", nargs="+", help="Archivos .gcode de entrada")
    merge_p.add_argument("--clones", type=int, default=1, help="Repeticiones por cada archivo")
    merge_p.add_argument("-o", "--output", default="produccion_autoswap.gcode", help="Ruta de salida")

    bridge_p = sub.add_parser("bridge", help="Iniciar puente USB Serial entre Ender 3 Pro y ESP32")
    bridge_p.add_argument("--printer", required=True, help="Puerto USB de la Ender 3 Pro en macOS")
    bridge_p.add_argument("--esp32", required=True, help="Puerto USB del ESP32 en macOS")

    test_p = sub.add_parser("test", help="Probar servomotor MG996R y microswitches en el ESP32")
    test_p.add_argument("--esp32", required=True, help="Puerto USB del ESP32 en macOS")

    args = parser.parse_args()
    if args.mode == "ports":
        list_macos_serial_ports()
    elif args.mode == "merge":
        merge_gcode_files(args.files, args.clones, args.output)
    elif args.mode == "bridge":
        run_serial_bridge(args.printer, args.esp32)
    elif args.mode == "test":
        run_test_cycle(args.esp32)


if __name__ == "__main__":
    main()
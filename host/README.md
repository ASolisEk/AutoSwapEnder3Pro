# AutoSwap — app de escritorio (macOS y Windows)

Coordina la **Ender 3 Pro** (Marlin, por USB) y la **Estación de Cambio Frontal** (Arduino UNO, por USB): envía cada trabajo línea por línea y, entre trabajos, ordena expulsar la placa usada y cargar una limpia, comprobando cada sensor. Si algo falla, pausa la cola y deja la impresora en un estado seguro.

## Instalación

```bash
# macOS (Homebrew) — en Windows usa "py -3.12" y ".venv\Scripts\Activate.ps1"
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "./host[gui]"      # sin interfaz gráfica: pip install -e ./host
```

Requiere Python 3.11 o superior. Dependencias: `pyserial` (y `PySide6-Essentials` para la interfaz).

## Uso rápido

```bash
autoswap-gui                                  # interfaz gráfica
autoswap ports                                # puertos USB detectados
autoswap identify                             # ¿cuál es la impresora y cuál la estación? (no usar imprimiendo)
autoswap analyze pieza.gcode                  # altura, tiempo y avisos del G-code
autoswap station HOME                         # una orden a la estación (STATUS, CFG LIST, LIFT LEVEL 0...)
autoswap queue pieza.gcode --copies 6 --plates 6
autoswap queue --resume                       # reanudar la última cola interrumpida
autoswap test-swap --cycles 20 --report prueba.csv
autoswap console --port /dev/cu.usbmodem14101 # consola serie interactiva
autoswap merge a.gcode b.gcode -o cola.gcode  # modo microSD sin estación: pausa M0 para cambio manual
autoswap config show | path | set printer.port=COM5 | reset
autoswap firmware-upload --port COM5          # carga firmware.hex en el UNO (avrdude)
```

Todo se puede probar **sin hardware** con `--simulate` (impresora y estación virtuales):

```bash
autoswap queue pieza.gcode --copies 3 --simulate --yes
autoswap test-swap --cycles 10 --simulate --yes
autoswap station --simulate STATUS
```

## Qué hace la cola

1. Comprueba: estación con HOME, sin fallas, volteador cerrado, placa en la cama, placas suficientes, piezas ≤ 150 mm.
2. Imprime el trabajo enviando cada línea con número y checksum (`N… *cs`), gestionando `ok`, `Resend` y `busy`.
3. Entre trabajos: retrae, sube Z (altura máxima del trabajo + 10 mm), aparca X, lleva la cama a `Y=235`, deja los motores con fuerza (`M84 S600`) y ordena a la estación `EJECT` y `LOAD`. Espera `plate_warmup_s` para que la placa nueva se caliente.
4. Del G-code final de cada trabajo omite las órdenes que estorban al cambio (`M84`, `M140 S0`, mover la cama) y lo indica en `autoswap analyze`.
5. Al terminar: apaga calentadores. Avisos en el escritorio y, opcionalmente, al móvil con [ntfy](https://ntfy.sh).

Configuración: `config.toml` en `~/Library/Application Support/AutoSwapEnder3Pro/` (macOS) o `%LOCALAPPDATA%\AutoSwapEnder3Pro\` (Windows). Registros en `~/Library/Logs/AutoSwapEnder3Pro/` o `%LOCALAPPDATA%\AutoSwapEnder3Pro\logs\`.

## Desarrollo

```bash
pip install -e "./host[dev,gui]"
ruff check host
QT_QPA_PLATFORM=offscreen pytest host/tests      # 39 pruebas, sin hardware
```

| Módulo | Contenido |
| :--- | :--- |
| `marlin.py` | Enlace con Marlin: números de línea, checksum, `Resend`, `busy`, errores fatales, temperaturas |
| `station.py` | Protocolo de la estación (Anexo C, versión 2) con latido `PING` |
| `gcode.py` | Análisis (Z/Y máximos, tiempo estimado) y limpieza del G-code final |
| `orchestrator.py` | Cola, comprobaciones previas, cambio de placa, recuperación de errores, ciclos de prueba |
| `ports.py` | Detección de puertos y saludo para distinguir impresora y estación |
| `sim.py` | Impresora y estación simuladas |
| `platform_utils.py` | Evitar suspensión, avisos, avrdude |
| `cli.py`, `gui/app.py` | Línea de órdenes e interfaz PySide6 |

Empaquetado: `packaging/build_macos.sh` y `packaging/build_windows.ps1` (PyInstaller).

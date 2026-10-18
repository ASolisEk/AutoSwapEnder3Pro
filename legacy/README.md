# Archivos de la versión 1 (histórico)

Estos archivos corresponden al primer diseño (ESP32 + servo + hilo de pesca y un puente serie en Python). Se conservan como referencia, pero **no deben usarse para armar el sistema**: la sección 1 del [plan detallado](../PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md) explica por qué esa secuencia mecánica no funciona en una impresora de cama móvil.

| Archivo | Reemplazado por |
| :--- | :--- |
| `README_v1.md`, `INVESTIGACION_AUTOSWAP_A1_A_ENDER3PRO.md` | [README.md](../README.md) y [PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md](../PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md) |
| `TUTORIAL_INSTALACION.md`, `Tutorial_Instalacion_AutoSwap_Ender3Pro.pdf` | [docs/TUTORIAL_ARMADO.md](../docs/TUTORIAL_ARMADO.md) |
| `autoswap_esp32.cpp`, `platformio.ini` | [firmware/station](../firmware/station) (Arduino UNO + CNC Shield) |
| `autoswap_manager.py`, `requirements.txt` | [host](../host) (app para macOS y Windows) |
| `ender3pro_autoswap_macro.gcode` | Secuencia de cambio en `host/src/autoswap/orchestrator.py` y plantillas en [slicer](../slicer) |

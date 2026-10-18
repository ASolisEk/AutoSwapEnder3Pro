#!/usr/bin/env bash
# Genera AutoSwap.app (interfaz grafica) y autoswap (linea de ordenes) para macOS.
# Ejecutar en un Mac (PyInstaller no compila de forma cruzada). Resultado en dist/.
#   ./packaging/build_macos.sh
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv-build
source .venv-build/bin/activate
pip install --upgrade pip
pip install -e "./host[gui,build]"

pyinstaller --noconfirm --clean --windowed --name AutoSwap \
  --osx-bundle-identifier com.asolisek.autoswap \
  packaging/autoswap_gui_entry.py
pyinstaller --noconfirm --clean --onefile --name autoswap packaging/autoswap_cli_entry.py

# Firmware compilado (si existe) junto a la app
if [[ -f firmware/station/.pio/build/uno/firmware.hex ]]; then
  cp firmware/station/.pio/build/uno/firmware.hex dist/
fi

contenido=(AutoSwap.app autoswap)
[[ -f dist/firmware.hex ]] && contenido+=(firmware.hex)
(cd dist && zip -qry "AutoSwap-macOS-$(uname -m).zip" "${contenido[@]}")
shasum -a 256 dist/*.zip
echo "Listo: dist/AutoSwap.app. La primera vez: clic derecho -> Abrir (la app no esta firmada)."

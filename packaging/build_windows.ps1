# Genera AutoSwap.exe (interfaz grafica) y autoswap.exe (linea de ordenes) para Windows.
# Ejecutar en PowerShell desde la carpeta del proyecto:
#   powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

py -3.12 -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".\host[gui,build]"

pyinstaller --noconfirm --clean --windowed --name AutoSwap packaging\autoswap_gui_entry.py
pyinstaller --noconfirm --clean --onefile --name autoswap packaging\autoswap_cli_entry.py

if (Test-Path firmware\station\.pio\build\uno\firmware.hex) {
  Copy-Item firmware\station\.pio\build\uno\firmware.hex dist\
}

Compress-Archive -Force -Path dist\AutoSwap, dist\autoswap.exe -DestinationPath dist\AutoSwap-Windows.zip
Get-FileHash dist\AutoSwap-Windows.zip -Algorithm SHA256
Write-Host "Listo: dist\AutoSwap\AutoSwap.exe. Si SmartScreen avisa: 'Mas informacion' -> 'Ejecutar de todas formas'."

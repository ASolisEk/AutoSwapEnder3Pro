#!/usr/bin/env bash
# Genera todos los STL de cad/stl a partir de los .scad (requiere OpenSCAD 2024 o posterior).
#   macOS:   brew install --cask openscad@snapshot
#   Windows: instala OpenSCAD (version "development snapshot") y ejecuta este script en Git Bash
# Uso: ./generar_stl.sh            (todas las piezas)
#      ./generar_stl.sh zapata     (solo las que contienen "zapata" en el nombre)
set -euo pipefail
cd "$(dirname "$0")"
OPENSCAD="${OPENSCAD:-openscad}"
FILTRO="${1:-}"
mkdir -p stl
# El motor "manifold" (OpenSCAD 2024+) es cientos de veces mas rapido; con versiones antiguas se usa CGAL.
BACKEND=()
"$OPENSCAD" --help 2>&1 | grep -q -- "--backend" && BACKEND=(--backend=manifold)

# archivo.scad | parametros -D | nombre del STL
PIEZAS=(
  "zapata.scad||zapata"
  "tope_trasero.scad||tope_trasero"
  "carro_base.scad||carro_base"
  "carro_torre.scad||carro_torre"
  "dedo_gancho.scad||dedo_gancho"
  "eje_soportes.scad|pieza=\"motor\"|eje_soporte_motor"
  "eje_soportes.scad|pieza=\"polea\"|eje_soporte_polea"
  "riel_tapa.scad||riel_tapa"
  "pedestal.scad|pieza=\"riel\"|pedestal_riel"
  "pedestal.scad|pieza=\"bisagra\"|pedestal_bisagra"
  "pedestal.scad|pieza=\"calza\"|calza_riel"
  "volteador.scad|pieza=\"mitad1\"|volteador_mitad1"
  "volteador.scad|pieza=\"mitad2\"|volteador_mitad2"
  "volteador.scad|pieza=\"union\"|volteador_union"
  "volteador_servo.scad|pieza=\"soporte\"|volteador_servo_soporte"
  "volteador_servo.scad|pieza=\"palanca\"|volteador_servo_palanca"
  "peine.scad|lado=\"der\"|peine_derecho"
  "peine.scad|lado=\"izq\"|peine_izquierdo"
  "ascensor.scad|pieza=\"placa_der\"|ascensor_placa_derecha"
  "ascensor.scad|pieza=\"placa_izq\"|ascensor_placa_izquierda"
  "ascensor.scad|pieza=\"tuerca\"|ascensor_soporte_tuerca"
  "ascensor.scad|pieza=\"motor\"|ascensor_soporte_motor"
  "sensores.scad|pieza=\"final_carrera\"|soporte_final_carrera"
  "sensores.scad|pieza=\"inductivo_cama\"|soporte_inductivo_cama"
  "sensores.scad|pieza=\"inductivo_descarga\"|soporte_inductivo_descarga"
  "caja_electronica.scad|pieza=\"caja\"|caja_electronica"
  "caja_electronica.scad|pieza=\"tapa\"|caja_electronica_tapa"
  "pie.scad||pie_nivelador"
)

for entrada in "${PIEZAS[@]}"; do
  IFS='|' read -r archivo param nombre <<< "$entrada"
  [[ -n "$FILTRO" && "$nombre" != *"$FILTRO"* ]] && continue
  args=(${BACKEND[@]+"${BACKEND[@]}"} --export-format binstl -o "stl/$nombre.stl")
  [[ -n "$param" ]] && args+=(-D "$param")
  printf '%-32s ' "$nombre"
  if salida=$("$OPENSCAD" "${args[@]}" "$archivo" 2>&1) && [[ -s "stl/$nombre.stl" ]] && ! grep -q "ERROR" <<< "$salida"; then
    echo "ok"
  else
    echo "ERROR"
    echo "$salida"
    exit 1
  fi
done

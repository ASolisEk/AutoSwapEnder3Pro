; --- AUTOSWAP INICIO (OrcaSlicer) - Ender 3 Pro con placas PEI y zapata ---
M140 S[bed_temperature_initial_layer_single]    ; calentar cama
M104 S150                                   ; precalentar boquilla sin escurrir
G28                                         ; home de todos los ejes (obligatorio: la placa es nueva)
M190 S[bed_temperature_initial_layer_single]    ; esperar a la cama
M109 S[nozzle_temperature_initial_layer]  ; esperar a la boquilla
G92 E0
G1 Z2.0 F3000
G1 X3 Y25 Z0.3 F5000.0                      ; linea de purga en el borde izquierdo,
G1 X3 Y150 Z0.3 F1500.0 E12                 ; lejos de la zapata (frente) y de los topes (fondo)
G1 X3.4 Y150 Z0.3 F5000.0
G1 X3.4 Y25 Z0.3 F1500.0 E24
G92 E0
G1 Z2.0 F3000

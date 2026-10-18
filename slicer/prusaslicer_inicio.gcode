; --- AUTOSWAP INICIO (PrusaSlicer) - Ender 3 Pro con placas PEI y zapata ---
M140 S[first_layer_bed_temperature]    ; calentar cama
M104 S150                                   ; precalentar boquilla sin escurrir
G28                                         ; home de todos los ejes (obligatorio: la placa es nueva)
M190 S[first_layer_bed_temperature]    ; esperar a la cama
M109 S[first_layer_temperature]  ; esperar a la boquilla
G92 E0
G1 Z2.0 F3000
G1 X3 Y25 Z0.3 F5000.0                      ; linea de purga en el borde izquierdo,
G1 X3 Y150 Z0.3 F1500.0 E12                 ; lejos de la zapata (frente) y de los topes (fondo)
G1 X3.4 Y150 Z0.3 F5000.0
G1 X3.4 Y25 Z0.3 F1500.0 E24
G92 E0
G1 Z2.0 F3000

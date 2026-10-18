; --- AUTOSWAP FIN (Cura) ---
G91                 ; coordenadas relativas
G1 E-2 F2700        ; retraer filamento
G1 Z10 F600         ; subir 10 mm
G90                 ; coordenadas absolutas
M106 S0             ; ventilador de capa apagado
M104 S0             ; boquilla apagada
; NO usar M84, M140 S0 ni G1 Y235: la app AutoSwap hace el cambio de placa,
; mantiene la cama caliente entre trabajos y la apaga al terminar la cola.

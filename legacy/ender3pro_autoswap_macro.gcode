; =====================================================================
; SECUENCIA AUTOSWAP PARA CREALITY ENDER 3 PRO (235x235mm PEI)
; Proyecto: AutoSwapEnder3Pro (https://github.com/ASolisEk/AutoSwapEnder3Pro)
; =====================================================================
M400                        ; Esperar a que terminen todos los movimientos en cola
G91                         ; Modo de coordenadas relativas
G1 E-3 F1800                ; Retraer 3 mm de filamento para evitar hilos
G1 Z15 F600                 ; Elevar boquilla 15 mm sobre la pieza terminada
G90                         ; Volver a coordenadas absolutas
G1 X10 F3000                ; Aparcar cabezal X a la izquierda fuera del area de choque

; --- FASE 1: Activar mecanismo de cambio (via USB Serial M118 o tope Z) ---
M118 //AUTOSWAP:ENGAGE      ; Envia senal por USB a macOS para que el ESP32 active el servo
; (Si usas el modo 100% mecanico sin ESP32, descomenta la siguiente linea: G1 Z245 F600)
M400
G4 P1500                    ; Pausa de 1.5 s para que el servo MG996R posicione la leva

; --- FASE 2: Despegar placa actual y enganchar placa nueva en el fondo ---
G1 Y230 F2500               ; Avanzar cama al frente para levantar borde en las cunas
M400
G1 Y0 F2000                 ; Retroceder cama al fondo (Y=0) para acoplar imanes de nueva placa
M400
G4 P800                     ; Pausa breve de acoplamiento magnetico (20x10x2 mm)

; --- FASE 3: Extraer placa nueva y expulsar la placa anterior ---
G1 Y235 F1800               ; Avanzar al maximo: la placa nueva empuja y expulsa la usada
M400
M118 //AUTOSWAP:RELEASE     ; Ordenar al ESP32 regresar el servo a reposo
G4 P1000

; --- FASE 4: Asentar placa nueva y desacoplar gancho trasero ---
G1 Y15 F2500                ; Retroceso de asentamiento sobre la base magnetica
G1 Y110 F3000               ; Centrar cama para iniciar el siguiente trabajo
M400
; =====================================================================

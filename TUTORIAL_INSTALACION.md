# Tutorial Paso a Paso de Instalación: AutoSwapEnder3Pro

> **Aviso:** este tutorial corresponde a la versión anterior del diseño, cuyas piezas impresas no existen y cuya secuencia mecánica no es viable (ver sección 1 de **[PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md](PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md)**). Para armar el sistema, sigue la sección 8 de ese plan.

Guía práctica de montaje mecánico, cableado electrónico sin soldadura y configuración en **macOS** para adaptar el sistema **[Kit AutoSwap A1 de Nel 3D](https://nel-3d.com/products/autoswap-completo-a1)** (basado en el diseño original de **[EVRENOT en Cults3D](https://cults3d.com/es/modelo-3d/herramientas/autoswap-bambulab-a1-plate-changer-upgrade-kit-v1)** y analizado en el video **[Convierte tu Impresora 3D en una Máquina Automática 24/7](https://www.youtube.com/watch?v=CNrtmL0N2PQ)**) a la impresora **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)**.

## Fase 0: Preparación del Área, Herramientas y Seguridad Básica

No necesitas saber soldar con estaño ni tener experiencia previa en electrónica para completar esta instalación.

### Herramientas Necesarias y Tiempo Estimado
- **Tiempo total estimado:** 75 a 90 minutos divididos en 6 fases verificables.
- **Juego de llaves Allen (incluidas con tu Ender 3 Pro):** Llaves de 2.0 mm, 2.5 mm y 3.0 mm para tornillería M3 y M4.
- **Destornillador de precisión (plano o estrella de 2.5 mm):** Para apretar los bornes de la placa de expansión del microcontrolador **[ESP32-DevKitC V4](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)**.
- **Tijeras o alicate de corte al ras:** Para cortar a medida el hilo de pesca trenzado (50 lb) y el tubo guía PTFE.
- **Plumón permanente:** Indispensable para marcar la cara norte ("N") de los imanes de neodimio antes de insertarlos.

### Tres Reglas de Oro de Seguridad Antes de Comenzar
1. **Desconecta el cable de alimentación principal (110V/220V) de la fuente MeanWell de tu Ender 3 Pro** antes de manipular el perfil de aluminio V-Slot 4040 o retirar los muelles de la cama caliente.
2. **Deja enfriar la cama y la boquilla por debajo de 30 °C** antes de retirar la alfombrilla magnética original o instalar los espaciadores de silicona.
3. **Respeta la regla de Tierra Común (`GND`):** Une siempre el polo negativo (`-`) de la fuente externa de 5V 3A con un borne `GND` del ESP32, pero nunca conectes el polo positivo (`+5V`) de la fuente externa al pin `3V3` del ESP32.

## Fase 1: Impresión Previa de las Piezas 3D del Kit Adaptador

Antes de desmontar la cama de tu impresora, imprime las cinco familias de piezas plásticas que conforman la adaptación mecánica para el chasis V-Slot 4040 de la **[Creality Ender 3 Pro](https://3dprinting.com/products/3d-printer/creality-ender-3-pro/)**. Tal como recomienda **[Nel 3D en su guía de montaje](https://www.youtube.com/watch?v=3vubNZdhSGA)**, las piezas que tocan las placas calientes deben imprimirse en **ABS o PETG** para soportar temperaturas de cama de 60 °C a 80 °C sin deformarse:

| Pieza Impresa | Cantidad | Material Recomendado | Ajustes de Laminado | Función en el Sistema |
| :--- | :--- | :--- | :--- | :--- |
| **Sujetador Trasero de Placa (Plate Clip 235 mm)** | 1 por cada placa PEI (3 a 10 uds.) | ABS o PETG (obligatorio por calor de cama) | Altura de capa 0.20 mm, 4 perímetros, 40% relleno giroide | Aloja 2 imanes de neodimio de 20 × 10 × 2 mm y permite que el carro arrastre la placa |
| **Bastidor Cargador Trasero V-Slot 4040** | 1 conjunto (base + 2 columnas inclinadas a 18°) | PLA+ o PETG | Altura de capa 0.20 mm, 4 perímetros, 30% relleno | Sostiene la pila de hasta 10 placas PEI de 235 × 235 mm detrás del eje Y |
| **Carro Acoplador Magnético y Pestillo (Latch)** | 1 conjunto | PETG o ABS | Altura de capa 0.16 mm, 4 perímetros, 50% relleno | Libera únicamente la placa inferior del cargador cuando el servomotor tira del hilo |
| **Uñas Despegadoras Frontales (Wedge Lifters)** | 2 uds. (izquierda y derecha) | PETG o ABS | Altura de capa 0.16 mm, 5 perímetros, 60% relleno | Levantan el borde frontal de la placa usada al llegar a Y=230 mm para vencer el imán |
| **Soporte de Servomotor MG996R y Microswitches** | 1 conjunto | PLA+ o PETG | Altura de capa 0.20 mm, 3 perímetros, 25% relleno | Fija el servomotor y los dos finales de carrera KW11-3Z al perfil de aluminio |

## Fase 2: Preparación de la Cama Caliente y de las Placas PEI (235 × 235 mm)

### Paso 2.1: Sustituir los Muelles por Espaciadores Rígidos de Silicona
1. Gira las 4 ruedas de nivelación inferiores en sentido antihorario hasta retirarlas por completo.
2. Levanta con cuidado la cama de aluminio (cuidado con el cable trasero del calefactor) y retira los 4 muelles amarillos o metálicos originales.
3. Coloca los 4 **[espaciadores rígidos de silicona (16–18 mm)](https://www.aliexpress.com/item/1005006152753312.html)** en los cuatro tornillos de las esquinas; si tu Ender 3 Pro tiene el prensaestopas del cable de la cama en la esquina trasera izquierda, coloca allí el espaciador más corto del kit (16 mm).
4. Vuelve a enroscar las 4 ruedas de nivelación comprimiendo ligeramente la silicona para que la cama quede firme y no cabecee durante el arrastre magnético.

### Paso 2.2: Preparar la Base Magnética y Armar los Sujetadores en Cada Placa PEI
1. Retira la alfombrilla superior blanda *CMag* de la cama, dejando únicamente la lámina magnética adhesiva pegada sobre el aluminio de 235 × 235 mm. Si la lámina magnética original está dañada, pega la base magnética 3M nueva incluida con tus **[placas de acero flexible PEI de 235 × 235 mm](https://store.creality.com/products/smooth-pei-build-plate-235-235mm)**.
2. Toma tus **imanes de neodimio de 20 × 10 × 2 mm** y apílalos todos juntos para identificar su orientación magnética. Con el plumón permanente, marca una letra **"N"** en la misma cara de todos los imanes.
3. En cada **Sujetador Trasero (Plate Clip en ABS/PETG)**, inserta a presión 2 imanes de 20 × 10 × 2 mm asegurándote de que la marca "N" mire hacia afuera (hacia la parte trasera de la impresora). En el carro acoplador del cargador, coloca los 2 imanes enfrentados con la cara opuesta para que se **atraigan con fuerza** al tocarse.
4. Fija el sujetador trasero centrado en el borde posterior de cada placa PEI de 235 × 235 mm apretando 4 tornillos **M3 × 8 mm**.

## Fase 3: Montaje Mecánico en el Chasis V-Slot 4040 de la Ender 3 Pro

### Paso 3.1: Instalar el Bastidor del Cargador Trasero y las Guías Laterales
1. Desliza 4 tuercas en T (*T-Nuts* M4) dentro de las ranuras laterales del perfil central **V-Slot 4040** en la parte posterior de la impresora, justo detrás de la carcasa del motor paso a paso del eje Y.
2. Presenta el **Bastidor del Cargador Trasero** salvando el motor Y y aprieta los 4 tornillos **M4 × 12 mm** con la llave Allen de 2.5 mm.
3. Encaja las dos guías laterales de centrado a los costados de la cama para que, cuando una placa nueva caiga desde el cargador trasero, quede alineada dentro de los 235 × 235 mm sin desviarse.

### Paso 3.2: Instalar las Uñas Despegadoras Frontales y el Tubo Guía PTFE
1. En el extremo delantero del perfil V-Slot 4040 (junto al tensor de la correa del eje Y), fija el soporte de las **dos uñas despegadoras frontales (Wedge Lifters)** con 2 tornillos M4 × 12 mm y tuercas en T.
2. Atornilla el soporte del **[servomotor metálico MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)** en el lateral trasero izquierdo del chasis (perfil 2040).
3. Conecta un extremo del **tubo PTFE de 1 metro** en el ojal de salida del soporte del servomotor y el otro extremo en el pestillo retenedor del cargador trasero.
4. Pasa el **hilo de pesca trenzado (50 lb)** por el interior del tubo PTFE. Con el brazo del servomotor en su posición de reposo (`15°`), ata un extremo del hilo al brazo del servo y el otro extremo a la leva del cargador dejando una tensión suave.
5. Coloca delante de la impresora una caja o bandeja con base de espuma de al menos 260 × 260 mm para amortiguar la caída de las placas terminadas.

## Fase 4: Cableado Electrónico Paso a Paso (Cero Soldadura)

Alinea las dos filas de pines de tu placa **[ESP32-DevKitC V4](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)** sobre el zócalo central de la **Placa de Expansión con Bornes de Tornillo** asegurándote de que la serigrafía coincida (`GND` con `GND`, `D18` con `D18`) y realiza estas 7 conexiones apretando los tornillos:

| Orden | Cable / Origen del Componente | Color del Cable | Borne de Tornillo Destino | Verificación para Principiantes |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Polo Negativo (`-`) del Adaptador de Fuente 5V 3A | Negro | Borne **`GND`** del ESP32 | Establece la Tierra Común entre la fuente de fuerza y el cerebro ESP32 |
| **2** | Cable de Tierra del **[Servomotor MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)** | Marrón o Negro | Mismo borne **`GND`** (o segundo borne `GND` del ESP32) | Cierra el circuito de alimentación del servomotor |
| **3** | Polo Positivo (`+`) del Adaptador de Fuente 5V 3A | Rojo | Unir directamente en bornera con el cable **Rojo (central)** del Servo MG996R | Alimenta el motor directamente desde la fuente de 5V 3A sin pasar por el USB de tu Mac |
| **4** | Cable de Señal PWM del **[Servomotor MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)** | Naranja o Amarillo | Borne **`GPIO 18`** (marcado como `D18` o `18`) | Envía el ángulo exacto de giro (`15°` reposo / `125°` expulsión) |
| **5** | Microswitch 1 (Cama en Fondo Y=0) — Pines `C` y `NO` | Negro (`C`) y Verde (`NO`) | Pin `C` a **`GND`** y Pin `NO` al borne **`GPIO 19`** (`D19`) | Detecta cuando la cama retrocede al tope trasero para acoplar la placa nueva |
| **6** | Microswitch 2 (Sensor de Placas en Cargador) — Pines `C` y `NO` | Negro (`C`) y Blanco (`NO`) | Pin `C` a **`GND`** y Pin `NO` al borne **`GPIO 21`** (`D21`) | Comprueba que haya al menos una placa PEI virgen antes de iniciar el ciclo |
| **7** | Cables USB de Datos (Impresora y ESP32) | USB Mini/Micro a USB-C | Conectar ambos puertos USB a tu computadora con **macOS** | Permite que el script en Python coordine la impresora y el ESP32 |

## Fase 5: Instalación del Software y Carga de Firmware en macOS

### Paso 5.1: Preparar el Entorno en la Terminal de macOS
```bash
# 1. Instalar Python 3 y PlatformIO Core en macOS via Homebrew
brew install python platformio
# 2. Entrar al proyecto, crear entorno virtual e instalar pySerial
cd ~/AutoSwapEnder3Pro && python3 -m venv .venv
source .venv/bin/activate && pip install pyserial
```

### Paso 5.2: Cargar el Firmware (`autoswap_esp32.cpp`) al ESP32 desde macOS
```bash
mkdir -p esp32_firmware/src
cp autoswap_esp32.cpp esp32_firmware/src/main.cpp
cd esp32_firmware
pio project init --board esp32dev --project-option "lib_deps=madhephaestus/ESP32Servo@^3.0.5"
pio run --target upload
cd ..
```

### Paso 5.3: Identificar los Puertos USB de tu Ender 3 Pro y del ESP32 en macOS
```bash
python3 autoswap_manager.py ports
```

## Fase 6: Calibración, Prueba en Vacío y Primera Cola Automática

### Paso 6.1: Prueba de Sensores y del Servomotor desde macOS
```bash
python3 autoswap_manager.py test --esp32 /dev/cu.SLAB_USBtoUART
```

### Paso 6.2: Nivelación Inicial de Primera Capa sobre la Placa PEI
Coloca la primera placa PEI sobre la cama magnética de la Ender 3 Pro, ejecuta un **Auto Home** (**[comando G28 de Marlin](https://marlinfw.org/docs/gcode/G028.html)**) desde la pantalla LCD de la impresora y ajusta por última vez las 4 ruedas inferiores con una hoja de papel.

### Paso 6.3: Unir tus Archivos G-Code y Lanzar la Producción Continua
```bash
# 1. Crear un archivo G-code multipieza (ejemplo: repetir 4 veces pieza_soporte.gcode)
python3 autoswap_manager.py merge pieza_soporte.gcode --clones 4 -o lote_4_placas.gcode

# 2. Iniciar el puente automatico en macOS mientras imprimes lote_4_placas.gcode
python3 autoswap_manager.py bridge \
  --printer /dev/cu.usbserial-1410 \
  --esp32 /dev/cu.SLAB_USBtoUART
```

### Guía Rápida de Diagnóstico y Ajuste Fino (Troubleshooting)

| Síntoma Observado | Causa Probable | Solución Inmediata |
| :--- | :--- | :--- |
| **La placa usada no termina de despegarse al avanzar a Y=230 mm** | Las uñas frontales (*Wedge Lifters*) están 1 mm demasiado altas o el hilo tiene holgura | Afloja los 2 tornillos M4 frontales, baja las cuñas al ras de la base magnética y tensa 3 mm el hilo trenzado en el brazo del servo |
| **El carro trasero retrocede a Y=0 pero no arrastra la placa nueva** | Imanes de neodimio (20 × 10 × 2 mm) montados con la misma polaridad enfrentada (se repelen) | Verifica con un imán testigo que el carro trasero y el clip ABS de la placa se atraigan con firmeza al llegar a `Y=0` |
| **El servomotor MG996R vibra pero no tiene fuerza para tirar del hilo** | Fuente externa desconectada o falta unir la Tierra Común (`GND`) | Comprueba que el cable negro (`-`) de la fuente de 5V 3A esté atornillado en el mismo borne `GND` del ESP32 |
| **La consola de macOS muestra `ERROR:NO_PLATES_IN_MAGAZINE` con placas puestas** | La palanca del Microswitch 2 no alcanza a ser presionada por la placa inferior | Adelanta 2 mm el soporte del Microswitch 2 en la ranura del cargador hasta escuchar el "clic" al apoyar una placa PEI |

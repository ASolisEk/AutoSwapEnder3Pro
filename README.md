# AutoSwapEnder3Pro: Sistema de Cambio Automático de Placas para Creality Ender 3 Pro

> **Actualización (plan v2):** el análisis detallado y el nuevo plan de trabajo están en **[PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md](PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md)**. Ese documento audita este README, explica por qué la secuencia mecánica descrita aquí no funciona en una impresora de cama móvil y propone una **Estación de Cambio Frontal** con lista de compras, armado paso a paso para principiantes y plan de software para **macOS y Windows**. Las secciones 1.2 y 2–5 de este README quedan como referencia histórica.

Documentación técnica integral, análisis de ingeniería inversa, lista de materiales (BOM), guía de armado electrónico paso a paso para principiantes y arquitectura de software en **macOS** para adaptar el sistema de cambio automático de camas magnéticas **[AutoSwap A1 de Nel 3D](https://nel-3d.com/products/autoswap-completo-a1)** (diseñado originalmente por **EVRENOT** en **[Cults3D](https://cults3d.com/es/modelo-3d/herramientas/autoswap-bambulab-a1-plate-changer-upgrade-kit-v1)** y gestionado mediante **[AutoSwap GCode Manager](https://auto-swap.net/)**) a la impresora **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)**.

## 1. Análisis Detallado del Video y del Producto Original AutoSwap A1

### 1.1 Desglose del Video de Referencia (Nel 3D)

En el video **[Convierte tu Impresora 3D en una Máquina Automática 24/7](https://www.youtube.com/watch?v=CNrtmL0N2PQ)** (complementado por el análisis de montaje en **[¡AUTOMATIZA tu Bambu Lab A1 al 100%! Imprime sin parar](https://www.youtube.com/watch?v=3vubNZdhSGA)**), el canal **Nel 3D** evalúa las alternativas reales para automatizar granjas de impresión 3D y producir de forma continua sin intervención humana:

| Sistema Analizado | Impresora Objetivo | Coste Aproximado | Principio de Funcionamiento | Ventajas Clave | Limitaciones Detectadas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **[SwapMod A1 Mini](https://nel-3d.com/products/kit-swapmod-a1-mini)** | Bambu Lab A1 Mini | ~70 € | Cambio mecánico de hasta 10 placas PEI accionado por los propios ejes de la impresora | Montaje en 1 a 2 horas, alta fiabilidad, cambio instantáneo sin esperar enfriamiento | Exclusivo para la geometría de la A1 Mini (180 × 180 mm) |
| **[Kit AutoSwap A1](https://nel-3d.com/products/autoswap-completo-a1)** | Bambu Lab A1 (256 × 256 mm) | ~90 € (oferta) / 100 € | Cargador trasero inclinado de hasta 10 placas PEI con tracción por hilo trenzado, tubo PTFE e imanes de neodimio | Permite encadenar hasta 11 trabajos seguidos (1 en cama + 10 en cargador) en pocos segundos (mostrado entre `04:48` y `05:10` del **[video principal](https://www.youtube.com/watch?v=CNrtmL0N2PQ)**) | Requiere que el eje Z suba al tope máximo para accionar el mecanismo; sensible al grosor de placas clónicas |
| **Auto-Eject (Empuje con Cabezal)** | Cualquier impresora FDM abierta o con puerta abierta | ~0 € (2 soportes impresos en PLA para inclinar a ~35°) | Espera de 30 a 45 minutos tras finalizar para enfriar la cama y barrido con el propio cabezal (hotend) | Sin coste adicional ni hardware extra | Riesgo de romper el cabezal si la pieza no despega, inútil en piezas muy planas/pequeñas o bandejas llenas, pierde 30–45 min por ciclo |
| **Automat (Kickstarter)** | Impresoras cerradas o abiertas en granja | Gama alta industrial | Riel frontal motorizado que abre la puerta, retira la pieza y cierra la cámara | Compatible con ABS y materiales técnicos en cabina cerrada | Sistema voluminoso, costoso y en fase de lanzamiento |

### 1.2 Ingeniería y Comportamiento Mecánico del AutoSwap Original (Bambu Lab A1)

A partir de las especificaciones del **[Kit AutoSwap A1 en Nel 3D](https://nel-3d.com/products/autoswap-completo-a1)**, el **[análisis técnico de Fabbaloo](https://www.fabbaloo.com/news/design-of-the-week-autoswap-bambu-lab-a1-plate-changer)** y el modelo original de **[EVRENOT en Cults3D](https://cults3d.com/es/modelo-3d/herramientas/autoswap-bambulab-a1-plate-changer-upgrade-kit-v1)**, el sistema original opera como un **autómata puramente mecánico sincronizado por G-code**:

1. **Almacenamiento en Cargador Trasero (Magazine)**: Se instala una estructura impresa en la parte trasera del eje Y capaz de apilar hasta **10 placas flexibles PEI** en ángulo.
2. **Sujetador Trasero por Placa (Plate Clip en ABS)**: Cada placa PEI lleva atornillada en su pestaña trasera una pieza impresa en **ABS** con 4 tornillos M3 e **imanes de neodimio de 20 × 10 × 2 mm** (detallado en el minuto `02:44–04:15` del **[video de montaje de Nel 3D](https://www.youtube.com/watch?v=3vubNZdhSGA)**).
3. **Transmisión por Hilo Trenzado y Tubo PTFE**: Un hilo de pesca trenzado de alta resistencia al desgaste pasa por el interior de un **tubo guía PTFE de 1 metro**, conectando el puente superior/eje Z con el brazo elevador y el pestillo del cargador.
4. **Secuencia Cinemática de 5 Etapas al Finalizar la Impresión**:
   - **Etapa 1 (Activación en Z alto)**: Al terminar la pieza, el G-code eleva el eje Z hasta su cota superior máxima. Este movimiento tensa el hilo trenzado a través del tubo PTFE y arma el pestillo mecánico (como confirman las reseñas técnicas en **[Nel 3D](https://nel-3d.com/products/autoswap-completo-a1)**, si el cabezal no llega arriba del todo, no se activa la expulsión).
   - **Etapa 2 (Despegado y Expulsión de la Placa Usada)**: La cama (eje Y) avanza hacia adelante; unas cuñas inferiores levantan el borde de la placa PEI venciendo la atracción magnética en pelado (*peel force*, mucho menor que la fuerza de tracción vertical) y la placa con la pieza recién impresa cae por gravedad hacia la bandeja de recogida frontal.
   - **Etapa 3 (Enganche de Placa Virgen)**: El carro Y retrocede hasta el final de su recorrido trasero (`Y_min`), donde el acoplador magnético acopla los imanes de `20 × 10 × 2 mm` del sujetador ABS de la primera placa disponible en el cargador.
   - **Etapa 4 (Arrastre y Asentamiento Magnético)**: La cama se desplaza hacia adelante extrayendo la nueva placa del cargador; al pasar sobre la base magnética calefactada, las guías laterales la centran y la placa cae a plomo sobre la cama.
   - **Etapa 5 (Liberación y Reinicio)**: Un movimiento corto de retroceso desacopla el gancho trasero y comienza de inmediato la siguiente impresión encadenada en el archivo generado por **[AutoSwap GCode Manager](https://auto-swap.net/)**.

## 2. Plan de Ingeniería para Adaptar el Sistema a la Creality Ender 3 Pro

### 2.1 Diferencias Críticas entre Bambu Lab A1 y Creality Ender 3 Pro

Para trasladar esta funcionalidad a la **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)** (especificaciones técnicas en **[3DPrinting.com](https://3dprinting.com/products/3d-printer/creality-ender-3-pro/)**), es necesario resolver cinco diferencias físicas y electrónicas fundamentales:

| Parámetro Técnico | Bambu Lab A1 | [Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer) | Solución de Adaptación en `AutoSwapEnder3Pro` |
| :--- | :--- | :--- | :--- |
| **Tamaño Físico de Cama** | 256 × 256 mm | **235 × 235 mm** (área imprimible 220 × 220 mm) | Redimensionar el cargador trasero, guías laterales y clips ABS al estándar de **[placas PEI de 235 × 235 mm](https://store.creality.com/products/smooth-pei-build-plate-235-235mm)** |
| **Superficie de Fábrica** | Placa de acero flexible PEI | Alfombrilla magnética blanda (*CMag*) | Sustituir la alfombrilla blanda por **placas de acero para muelles PEI magnéticas de 235 × 235 mm**, ya que el acero rígido es indispensable para deslizar y empujar una placa con otra |
| **Estructura del Eje Y** | Carcasa cerrada con riel lineal integrado | Perfil de aluminio **V-Slot 4040** central con motor Y trasero expuesto | Anclar el bastidor del cargador trasero directamente al perfil **4040 central** y al travesaño **2040** mediante tuercas en T (*T-nuts* M4/M5), salvando la carcasa del motor Y |
| **Nivelación de Cama** | Automática por sensor de fuerza en boquilla | 4 ruedas manuales inferiores con muelles | Sustituir los muelles amarillos por **espaciadores rígidos de silicona** para que la cama no pierda nivelación al tirar de las placas |
| **Velocidad y Fuerza del Eje Z** | Doble motor / correa rápida | 1 husillo trapezoidal T8 lento (`G1 Z250` toma >40 s) | **Arquitectura Dual**: permitir accionamiento **Mecánico Puro por eje Y** o **Asistido Electrónicamente con ESP32 + Servomotor MG996R** para no forzar el husillo Z |

### 2.2 Arquitectura Propuesta: Sistema Híbrido Asistido (`AutoSwapEnder3Pro`)

Aunque es posible tensar el hilo subiendo el eje Z a `Z=250 mm`, en la **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)** subir y bajar el husillo T8 en cada pieza añade lentitud y riesgo de descalibrar el pórtico X. Por ello, este proyecto implementa una **arquitectura electromecánica asistida y controlada desde macOS** (que mantiene toda la simplicidad mecánica del cargador por gravedad de EVRENOT, pero sustituye el tirón del eje Z por un servomotor dedicado):

1. **Bastidor Trasero V-Slot 4040 (Cargador de 5 a 10 placas PEI 235 × 235 mm)**: Se fija en la parte posterior del perfil 4040 de la Ender 3 Pro con una inclinación de **15° a 20°**.
2. **Mecanismo de Retención y Liberación con Servomotor ([MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf))**: En lugar de depender de que el cabezal Z suba a 250 mm para tirar del hilo de pesca, un servomotor metálico de alto torque (**11 kg·cm**) tira del cable/leva para liberar exactamente una placa PEI del cargador y posicionar el gancho magnético cuando la cama va hacia atrás (`Y = 0`).
3. **Uñas Despegadoras Frontales (Wedge Lifters) y Rampa de Expulsión**: Cuando la cama avanza al máximo (`Y = 235 mm`) con el pestillo de expulsión activo, dos cuñas de perfil bajo levantan las esquinas de la placa PEI usada y la nueva placa empujada desde atrás termina de desplazarla hacia la bandeja recolectora frontal.
4. **Coordinador en macOS + Microcontrolador [ESP32-DevKitC](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)**: Tu Mac se comunica por USB Serial tanto con la placa base de la Ender 3 Pro (ejecutando **[Marlin Firmware](https://marlinfw.org/meta/gcode/)**) como con el **ESP32** (o bien el ESP32 detecta automáticamente el final de carrera cuando la cama llega a la posición de cambio), ejecutando la cola de trabajos de principio a fin.

## 3. Lista Completa de Materiales a Comprar (BOM)

Todos los componentes seleccionados son estándar, económicos y fáciles de conseguir en México o internacionalmente sin requerir soldadura superficial (SMD):

### 3.1 Componentes Mecánicos y de Impresión

| Categoría | Componente | Especificación Exacta | Cantidad | Función en el Sistema |
| :--- | :--- | :--- | :--- | :--- |
| **Superficie** | **[Placas de Acero Flexible PEI](https://store.creality.com/products/smooth-pei-build-plate-235-235mm)** | 235 × 235 mm (acero para muelles recubierto de PEI texturizado o liso) | 3 a 10 uds. | Placas intercambiables rígidas que sustituyen la cama blanda CMag original |
| **Fijación Cama** | **[Espaciadores de Silicona para Cama Caliente](https://www.aliexpress.com/item/1005006152753312.html)** | 16–18 mm de altura, resistentes a 200 °C (sustituyen los 4 muelles originales) | 1 kit (4 uds.) | Mantienen la altura y nivelación fijas durante la tracción mecánica del cambio |
| **Magnéticos** | **Imanes de Neodimio Rectangulares** | **20 × 10 × 2 mm**, grado N35 o N52 (según el diseño original en **[Nel 3D](https://www.youtube.com/watch?v=3vubNZdhSGA)**) | 20 a 30 uds. | Acoplamiento magnético entre los clips traseros de cada placa y el carro de arrastre |
| **Transmisión** | **Tubo Guía PTFE (Teflón Bowden)** | Diámetro interior 2.0 mm / exterior 4.0 mm, longitud **1 metro** | 1 m | Guía de baja fricción para el hilo de tracción del mecanismo |
| **Transmisión** | **Hilo de Pesca Trenzado (Braided Line)** | Polietileno trenzado de alta resistencia (50 lb / 0.35 mm, cero elongación) | 5 m | Tracción de los pestillos de liberación y brazo de enganche |
| **Tornillería** | **Kit Tornillos Métricos M3, M4 y Tuercas T** | Tornillos M3 (8, 12, 16, 20 mm) para los clips de placa + Tornillos M4×12 mm con **Tuercas en T (T-Nuts)** para perfil V-Slot 4040/2040 | 1 kit surtido | Fijación de clips ABS a las placas PEI y anclaje del chasis a la Ender 3 Pro |
| **Filamento** | **Filamento PETG o ABS + PLA+** | 1 rollo de PETG/ABS (1 kg) para los clips de placa (soportan 60–80 °C de cama) y 1 rollo de PLA+ (1 kg) para la estructura trasera | 2 kg total | Impresión de las piezas estructurales, rampa frontal y sujetadores de placa |

### 3.2 Componentes Electrónicos (Sin Soldadura Compleja)

| Componente | Modelo Recomendado | Especificación Clave | Cantidad | Función en el Sistema |
| :--- | :--- | :--- | :--- | :--- |
| **Microcontrolador** | **[ESP32-DevKitC V4](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)** | Placa de desarrollo de 30 o 38 pines con USB-C / Micro-USB (chip CP2102 o CH340) | 1 ud. | Cerebro del sistema AutoSwap; recibe órdenes desde macOS por USB o Wi-Fi y controla actuadores |
| **Base de Conexión** | **Placa de Expansión con Bornes de Tornillo para ESP32** | *ESP32 Screw Terminal Breakout Shield* (30/38 pines según el ESP32 elegido) | 1 ud. | Permite conectar todos los cables con un simple destornillador **sin usar cautín ni soldar** |
| **Actuador Principal** | **[Servomotor Metálico MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)** | Engranajes metálicos, torque de 9.4 a 11 kg·cm a 6 V, giro de 180° | 1 o 2 uds. | Tira del hilo trenzado / leva para desbloquear la siguiente placa del cargador y activar la uña expulsora |
| **Actuador Opcional** | **[Motor NEMA 17 + Driver A4988](https://pcbsync.com/nema-17-arduino/)** | Motor paso a paso 17HS4401 (40 N·cm) + módulo CNC Shield de 1 eje | Opcional (1 ud.) | Solo si deseas empuje motorizado independiente del eje Y en versiones avanzadas |
| **Sensores** | **Finales de Carrera Mecánicos (Microswitch)** | Modelo KW11-3Z con palanca metálica y 3 pines (C, NO, NC) o módulo endstop de 3 pines | 2 uds. | Sensor 1: detecta cuando la cama llega al fondo (`Y_min`). Sensor 2: detecta si quedan placas en el cargador |
| **Alimentación** | **Fuente de 5V / 6V 3A DC (Conector Jack 5.5×2.1 mm)** | Adaptador de pared 5V 3A + Adaptador de Jack hembra a bornes de tornillo | 1 ud. | Alimenta el servomotor MG996R con fuerza suficiente sin sobrecargar el puerto USB de tu Mac |
| **Cableado** | **Cables Jumper Dupont y Cable USB de Datos** | 1 pack de cables Dupont Hembra-Macho (20 cm) + 2 cables USB de datos hacia tu Mac (1 para la Ender 3 Pro y 1 para el ESP32) | 1 kit | Interconexión limpia por código de colores |

## 4. Instrucciones Detalladas de Armado (Para Principiantes en Electrónica)

Esta guía está diseñada para que puedas montar toda la parte electrónica y mecánica **usando únicamente un destornillador pequeño y llaves Allen**, sin necesidad de soldar con estaño ni tener conocimientos previos de circuitos.

### 4.1 Regla de Oro Antes de Empezar: "¿Qué es Tierra Común (GND)?"

En electrónica básica manejamos dos tipos de energía en nuestro circuito:
- **La señal de control** que sale del **[ESP32-DevKitC](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)** conectado por USB a tu Mac.
- **La fuerza muscular** de la fuente externa de 5V 3A que mueve el **[servomotor MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)**.

Para que el servomotor entienda las órdenes del ESP32, **ambos deben compartir el cable negativo (`GND` o Tierra)**. Nunca conectes el positivo (`+5V`) de la fuente externa al pin `3V3` del ESP32, pero **sí debes unir el negativo (`-`) de la fuente externa con un tornillo `GND` de la placa base del ESP32**.

### 4.2 Tabla de Conexiones Paso a Paso (Con Destornillador en la Placa de Bornes)

Inserta primero tu **[ESP32-DevKitC](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)** sobre la **Placa de Expansión con Bornes de Tornillo** asegurándote de que el puerto USB mire hacia afuera. Luego realiza estas 7 conexiones apretando los tornillos:

| Paso | Componente de Origen | Color Típico del Cable | Destino en la Placa de Tornillos / Bornera | Explicación Sencilla |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Fuente Externa 5V 3A** (Borne `-` Negativo) | Negro | Borne **`GND`** del ESP32 y cable Marrón/Negro del Servo | Crea la referencia común (`GND`) entre la fuente y el microcontrolador |
| **2** | **Fuente Externa 5V 3A** (Borne `+` Positivo) | Rojo | Cable **Rojo** central del **[Servomotor MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)** | Da energía directa al motor sin gastar corriente del USB de tu Mac |
| **3** | **[Servomotor MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)** (Cable de Señal) | Naranja o Amarillo | Borne **`GPIO 18`** (etiquetado como `D18` o `18` en el ESP32) | Por este cable el ESP32 le dice al servo a qué ángulo exacto girar (0° a 180°) |
| **4** | **Microswitch 1 (Posición Cama Trasera)** — Pin `C` (Común) | Negro o Azul | Borne **`GND`** del ESP32 | Cierra el circuito cuando la cama de la Ender 3 Pro toca la parte trasera |
| **5** | **Microswitch 1 (Posición Cama Trasera)** — Pin `NO` (Normalmente Abierto) | Verde | Borne **`GPIO 19`** (etiquetado como `D19` o `19` en el ESP32) | Avisa al ESP32 de que la cama está lista para enganchar una placa nueva |
| **6** | **Microswitch 2 (Detector de Placas en Cargador)** — Pin `C` (Común) | Negro | Borne **`GND`** del ESP32 | Cierra el circuito mientras haya al menos una placa PEI en el cargador |
| **7** | **Microswitch 2 (Detector de Placas en Cargador)** — Pin `NO` (Normalmente Abierto) | Blanco | Borne **`GPIO 21`** (etiquetado como `D21` o `21` en el ESP32) | Si se acaban las placas, detiene el ciclo para no imprimir sobre el aluminio desnudo |

### 4.3 Montaje Mecánico Paso a Paso en la Creality Ender 3 Pro

1. **Preparación de la Cama Caliente**:
   - Retira la alfombrilla magnética blanda original (*CMag*) si está deteriorada, pero **conserva la base magnética adhesiva adherida al aluminio** de la cama (o pega el pliego magnético nuevo incluido con tus **[placas de acero PEI 235 × 235 mm](https://store.creality.com/products/smooth-pei-build-plate-235-235mm)**).
   - Sustituye los 4 muelles inferiores de las ruedas de nivelación por los **4 espaciadores de silicona**, nivela la cama con una hoja de papel (`G28`) y verifica que las ruedas queden firmes.
2. **Armado de los Sujetadores de Placa (Plate Clips)**:
   - Imprime en **ABS o PETG** un sujetador trasero para cada placa PEI.
   - Inserta en las ranuras de cada sujetador **2 imanes de neodimio de 20 × 10 × 2 mm** verificando que todos tengan la **misma orientación de polaridad** (usa un plumón permanente para marcar con una "N" la cara que mira hacia atrás en todos los imanes antes de encajarlos).
   - Fija el sujetador al borde trasero de cada placa PEI de 235 × 235 mm usando 4 tornillos M3×8 mm.
3. **Instalación del Bastidor Trasero y las Uñas Expulsoras**:
   - Desliza 4 tuercas en T (*T-nuts* M4) en las ranuras laterales del perfil central **V-Slot 4040** en la parte trasera de la **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)** (justo detrás del motor del eje Y) y atornilla la torre del cargador inclinado.
   - Atornilla en el perfil frontal del eje Y el soporte de las **uñas despegadoras (wedges)** y coloca debajo una bandeja acolchada (o caja con espuma) donde caerán las placas terminadas.
4. **Enhebrado del Tubo PTFE y el Hilo Trenzado**:
   - Conecta un extremo del **tubo PTFE de 1 metro** en el soporte del **[servomotor MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)** y el otro extremo en el pestillo retenedor del cargador trasero.
   - Pasa el **hilo de pesca trenzado** por dentro del tubo PTFE, átalo al brazo del servomotor cuando esté en posición de reposo (`0°`) y ajústalo con tensión ligera en el pestillo del cargador para que al girar el servo a `120°` libere exactamente la placa inferior y active las uñas de despegue.

### 4.4 Lista de Verificación de Seguridad Antes de Encender

- **Verifica que ningún cable quede suelto** tirando suavemente de cada hilo en los bornes de tornillo.
- **Mueve la cama a mano lentamente de atrás hacia adelante** (con la impresora apagada) para comprobar que los cables del calefactor de cama no rocen con la torre trasera.
- **Conecta primero el USB del ESP32 a tu Mac** antes de enchufar la fuente de 5V 3A a la corriente.

## 5. Plan de Desarrollo de Software en macOS

El ecosistema de software en **macOS** se compone de tres módulos que trabajan en conjunto:
1. **Firmware del ESP32 (`firmware/autoswap_esp32.ino`)**: Escrito en C++ para **[PlatformIO](https://pypi.org/project/serial-interface/)** o Arduino IDE en macOS; escucha comandos por puerto serie USB (`SWAP`, `LOCK`, `RELEASE`, `STATUS`) y mueve el servomotor MG996R verificando los microswitches.
2. **Orquestador y Demonio de Impresión Continua en Python (`macos_controller/autoswap_daemon.py`)**: Script en Python 3 para macOS usando **[pySerial](https://pyserial.readthedocs.io/en/latest/pyserial_api.html)** que se conecta simultáneamente a la **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)** (`/dev/cu.usbserial-*`) y al **[ESP32-DevKitC](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)** (`/dev/cu.SLAB_USBtoUART` o `/dev/cu.wchusbserial*`), enviando trabajos G-code en cola y coordinando el cambio de placa.
3. **Generador de G-code Multipieza (`macos_controller/gcode_merger.py`)**: Equivalente local y abierto a la web **[AutoSwap GCode Manager](https://auto-swap.net/)** para unir múltiples archivos `.gcode` laminados para la Ender 3 Pro insertando la rutina de cambio de placa entre cada trabajo (ideal para imprimir desde tarjeta MicroSD o desde tu Mac).

### 5.1 Configuración del Entorno en macOS (Paso a Paso)

Abre la aplicación **Terminal** en tu Mac y ejecuta los siguientes comandos para preparar las herramientas y el entorno virtual de Python:

```bash
# 1. Instalar PlatformIO Core y Python 3 mediante Homebrew (si no los tienes)
brew install python platformio

# 2. Clonar tu repositorio y entrar a la carpeta del proyecto
git clone https://github.com/ASolisEk/AutoSwapEnder3Pro.git
cd AutoSwapEnder3Pro

# 3. Crear entorno virtual de Python e instalar pySerial
python3 -m venv .venv
source .venv/bin/activate
pip install pyserial

# 4. Identificar los puertos USB Serial conectados en macOS (Ender 3 Pro y ESP32)
ls /dev/cu.*
```

> **Nota sobre drivers en macOS**: Las placas Creality 1.1.4 / 4.2.2 / 4.2.7 y muchos ESP32 usan el chip USB-Serial **CH340** o **CP2102**. En versiones recientes de macOS (Ventura, Sonoma, Sequoia), el driver CH340 ya viene integrado de serie y aparecerá como `/dev/cu.usbserial-1410` o `/dev/cu.wchusbserial1410`.

### 5.2 Código Completo del Firmware para el ESP32 (`firmware/autoswap_esp32.ino`)

Este código se carga una sola vez desde tu Mac hacia el **[ESP32-DevKitC](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)** y gestiona los ángulos del servomotor y los dos finales de carrera:

```cpp
#include <Arduino.h>
#include <ESP32Servo.h>

// Definicion de pines (coinciden con la Tabla de Conexiones de la Seccion 4.2)
const int PIN_SERVO_SWAP     = 18; // Cable Naranja/Amarillo del Servo MG996R
const int PIN_ENDSTOP_Y_BACK = 19; // Microswitch 1: Cama en posicion trasera
const int PIN_ENDSTOP_PLATES = 21; // Microswitch 2: Presencia de placas en cargador

// Angulos calibrables del servomotor MG996R
const int ANGLE_IDLE         = 15;  // Posicion de reposo durante la impresion
const int ANGLE_EJECT_ENGAGE = 125; // Tensa el hilo para levantar uñas y liberar placa

Servo swapServo;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_ENDSTOP_Y_BACK, INPUT_PULLUP);
  pinMode(PIN_ENDSTOP_PLATES, INPUT_PULLUP);

  swapServo.setPeriodHertz(50);
  swapServo.attach(PIN_SERVO_SWAP, 500, 2400);
  swapServo.write(ANGLE_IDLE);

  Serial.println("AUTOSWAP_ESP32_READY");
}

bool hasPlatesAvailable() {
  // Con INPUT_PULLUP, LOW significa que el microswitch esta presionado por una placa
  return digitalRead(PIN_ENDSTOP_PLATES) == LOW;
}

bool isBedAtBack() {
  return digitalRead(PIN_ENDSTOP_Y_BACK) == LOW;
}

void executeSwapLatchCycle() {
  if (!hasPlatesAvailable()) {
    Serial.println("ERROR:NO_PLATES_IN_MAGAZINE");
    return;
  }
  // 1. Activar leva de expulsion y abrir retenedor de nueva placa
  swapServo.write(ANGLE_EJECT_ENGAGE);
  delay(1200);
  Serial.println("OK:LATCH_ENGAGED");
}

void releaseSwapLatch() {
  swapServo.write(ANGLE_IDLE);
  delay(800);
  Serial.println("OK:LATCH_RELEASED");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "STATUS") {
      Serial.print("STATUS:PLATES=");
      Serial.print(hasPlatesAvailable() ? "YES" : "EMPTY");
      Serial.print(",BED_BACK=");
      Serial.println(isBedAtBack() ? "YES" : "NO");
    } else if (cmd == "ENGAGE") {
      executeSwapLatchCycle();
    } else if (cmd == "RELEASE") {
      releaseSwapLatch();
    } else if (cmd == "TEST_CYCLE") {
      swapServo.write(ANGLE_EJECT_ENGAGE);
      delay(1500);
      swapServo.write(ANGLE_IDLE);
      delay(1000);
      Serial.println("OK:TEST_COMPLETE");
    }
  }
}
```

### 5.3 Secuencia G-Code de Cambio de Placa para Creality Ender 3 Pro (`gcode/ender3pro_autoswap_macro.gcode`)

Basada en los comandos estándar de **[Marlin Firmware](https://marlinfw.org/meta/gcode/)** (**[G28 Auto Home](https://marlinfw.org/docs/gcode/G028.html)**, **[G0/G1 Linear Move](https://marlinfw.org/docs/gcode/G000-G001.html)**, **[M400 Finish Moves](https://marlinfw.org/docs/gcode/M400.html)** y **[M118 Serial Print](https://marlinfw.org/docs/gcode/M118.html)**), esta secuencia ejecuta el intercambio mecánico en la **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)**:

```gcode
; =====================================================================
; SECUENCIA AUTOSWAP PARA CREALITY ENDER 3 PRO (235x235mm PEI)
; =====================================================================
M400                        ; Esperar a que terminen todos los movimientos en cola
G91                         ; Modo de coordenadas relativas
G1 E-3 F1800                ; Retraer 3 mm de filamento para evitar hilos
G1 Z15 F600                 ; Elevar boquilla 15 mm sobre la pieza terminada
G90                         ; Volver a coordenadas absolutas
G1 X10 F3000                ; Aparcar cabezal X a la izquierda fuera del area de choque

; --- FASE 1: Activar mecanismo de cambio (via USB Serial M118 o tope Z) ---
M118 //AUTOSWAP:ENGAGE      ; Envia señal por USB a la Mac para que el ESP32 active el servo
; (Si usas el modo 100% mecanico sin ESP32, descomenta la siguiente linea: G1 Z245 F600)
M400
G4 P1500                    ; Pausa de 1.5 s para que el servo MG996R posicione la leva

; --- FASE 2: Despegar placa actual y enganchar placa nueva en el fondo ---
G1 Y230 F2500               ; Avanzar cama al frente para levantar borde en las cuñas
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
```

### 5.4 Controlador y Combinador en Python para macOS (`macos_controller/autoswap_manager.py`)

Este script para **macOS** cumple dos funciones:
- **Modo `--merge`**: Une varios archivos `.gcode` en un único archivo continuo insertando la secuencia de cambio automático entre cada impresión (igual que **[AutoSwap GCode Manager](https://auto-swap.net/)**).
- **Modo `--daemon`**: Escucha el puerto USB de la **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)** en macOS con **[pySerial](https://pyserial.readthedocs.io/)** y, cuando recibe `//AUTOSWAP:ENGAGE` o `//AUTOSWAP:RELEASE` desde el comando **[M118 de Marlin](https://marlinfw.org/docs/gcode/M118.html)**, acciona automáticamente el **[ESP32-DevKitC](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)**.

```python
#!/usr/bin/env python3
"""
AutoSwapEnder3Pro - Controlador Serial y Combinador de G-Code para macOS
Licencia MIT - Copyright (c) 2026 Angel Solis Ek
"""

import argparse
import pathlib
import sys
import time
import serial

SWAP_GCODE_BLOCK = """
; --- INICIO BLOQUE AUTOSWAP ENDER 3 PRO ---
M400
G91
G1 E-3 F1800
G1 Z15 F600
G90
G1 X10 F3000
M118 //AUTOSWAP:ENGAGE
M400
G4 P1500
G1 Y230 F2500
M400
G1 Y0 F2000
M400
G4 P800
G1 Y235 F1800
M400
M118 //AUTOSWAP:RELEASE
G4 P1000
G1 Y15 F2500
G1 Y110 F3000
M400
; --- FIN BLOQUE AUTOSWAP ENDER 3 PRO ---
"""


def merge_gcode_files(input_files: list[str], clones: int, output_path: str) -> None:
    """Combina multiples archivos G-code e inserta la rutina de cambio de placa."""
    jobs = []
    for file_path in input_files:
        content = pathlib.Path(file_path).read_text(encoding="utf-8", errors="ignore")
        for _ in range(clones):
            jobs.append((pathlib.Path(file_path).name, content))

    merged_lines = [
        "; Archivo generado por AutoSwapEnder3Pro GCode Merger (macOS)",
        f"; Total de placas encadenadas: {len(jobs)}",
    ]

    for idx, (name, content) in enumerate(jobs, start=1):
        merged_lines.append(f"\n; === INICIO TRABAJO {idx}/{len(jobs)}: {name} ===")
        merged_lines.append(content)
        if idx < len(jobs):
            merged_lines.append(SWAP_GCODE_BLOCK)

    pathlib.Path(output_path).write_text("\n".join(merged_lines), encoding="utf-8")
    print(f"[OK] Archivo combinado guardado en: {output_path} ({len(jobs)} placas)")


def run_serial_bridge(printer_port: str, esp32_port: str, baud_printer: int = 115200, baud_esp32: int = 115200) -> None:
    """Escucha los comandos M118 de la Ender 3 Pro en macOS y acciona el ESP32."""
    print(f"Conectando a Ender 3 Pro en {printer_port} y ESP32 en {esp32_port}...")
    with serial.Serial(printer_port, baud_printer, timeout=1) as printer, \
         serial.Serial(esp32_port, baud_esp32, timeout=1) as esp:
        time.sleep(2.0)
        print("Puente AutoSwap activo en macOS. Esperando eventos M118...")
        while True:
            line = printer.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            print(f"[Ender3Pro] {line}")
            if "//AUTOSWAP:ENGAGE" in line:
                print("-> Activando servomotor de cambio de placa en ESP32...")
                esp.write(b"ENGAGE\n")
                resp = esp.readline().decode("utf-8", errors="ignore").strip()
                print(f"[ESP32] {resp}")
                if "ERROR:NO_PLATES" in resp:
                    printer.write(b"M112\n")  # Parada de emergencia si no hay placas
            elif "//AUTOSWAP:RELEASE" in line:
                print("-> Liberando servomotor a posicion de reposo...")
                esp.write(b"RELEASE\n")
                resp = esp.readline().decode("utf-8", errors="ignore").strip()
                print(f"[ESP32] {resp}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Herramienta AutoSwapEnder3Pro para macOS")
    sub = parser.add_subparsers(dest="mode", required=True)

    merge_p = sub.add_parser("merge", help="Unir archivos G-code con cambio automatico de placa")
    merge_p.add_argument("files", nargs="+", help="Archivos .gcode de entrada")
    merge_p.add_argument("--clones", type=int, default=1, help="Repeticiones por archivo")
    merge_p.add_argument("-o", "--output", default="produccion_autoswap.gcode", help="Archivo de salida")

    bridge_p = sub.add_parser("bridge", help="Ejecutar puente USB Serial entre Ender 3 Pro y ESP32")
    bridge_p.add_argument("--printer", required=True, help="Puerto en macOS de la Ender 3 Pro (ej. /dev/cu.usbserial-1410)")
    bridge_p.add_argument("--esp32", required=True, help="Puerto en macOS del ESP32 (ej. /dev/cu.SLAB_USBtoUART)")

    args = parser.parse_args()
    if args.mode == "merge":
        merge_gcode_files(args.files, args.clones, args.output)
    elif args.mode == "bridge":
        run_serial_bridge(args.printer, args.esp32)


if __name__ == "__main__":
    main()
```

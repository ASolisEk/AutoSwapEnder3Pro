# Investigación Técnica y Análisis de Ingeniería Inversa: AutoSwap A1 a Creality Ender 3 Pro

Documento de investigación detallada sobre el funcionamiento mecánico, magnético y de software del sistema **[Kit AutoSwap A1 de Nel 3D](https://nel-3d.com/products/autoswap-completo-a1)** (creado por **EVRENOT** en **[Cults3D](https://cults3d.com/es/modelo-3d/herramientas/autoswap-bambulab-a1-plate-changer-upgrade-kit-v1)** y **[AutoSwap GCode Manager](https://auto-swap.net/)**) a partir del análisis completo de los videos **[Convierte tu Impresora 3D en una Máquina Automática 24/7](https://www.youtube.com/watch?v=CNrtmL0N2PQ)** y **[¡AUTOMATIZA tu Bambu Lab A1 al 100%! Imprime sin parar](https://www.youtube.com/watch?v=3vubNZdhSGA)**, junto con el estudio de viabilidad para su adaptación a la **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)**.

## 1. Análisis Cronológico del Video Principal (`CNrtmL0N2PQ`)

En el video **[Convierte tu Impresora 3D en una Máquina Automática 24/7](https://www.youtube.com/watch?v=CNrtmL0N2PQ)**, Nel 3D evalúa cuatro métodos de automatización para granjas de impresión 3D:

| Tramo del Video | Sistema Analizado | Hallazgos Técnicos Clave |
| :--- | :--- | :--- |
| **`00:00 – 02:10`** | **[SwapMod para Bambu Lab A1 Mini](https://nel-3d.com/products/kit-swapmod-a1-mini)** | Coste aproximado de 70 €; tiempo de montaje de 1 a 2 horas; permite cambiar automáticamente hasta **10 placas PEI seguidas** usando los propios motores de la impresora; diseñado exclusivamente para la A1 Mini (180 × 180 mm). |
| **`02:11 – 03:16`** | **[AutoSwap para Bambu Lab A1](https://nel-3d.com/products/autoswap-completo-a1)** | Desarrollado por el creador turco **EVRENOT** ([Cults3D](https://cults3d.com/es/modelo-3d/herramientas/autoswap-bambulab-a1-plate-changer-upgrade-kit-v1)); requiere imprimir un mayor volumen de piezas estructurales por el tamaño de cama de 256 × 256 mm; coste en tienda de ~90 € (oferta) / 100 € habitual. |
| **`04:12 – 06:55`** | **Comparativa Real: Auto-Eject vs. AutoSwap (Demo en `04:48–05:10`)** | El método *Auto-Eject* (inclinar la impresora ~35° con dos soportes impresos en PLA y empujar la pieza con el cabezal) es gratuito pero obliga a **esperar entre 30 y 45 minutos** para que la cama se enfríe, no sirve para piezas planas o lotes múltiples y puede romper el cabezal si la pieza no despega. En `04:48–05:10` se muestra el **AutoSwap A1** retirando la placa terminada hacia abajo y cargando una placa virgen en **menos de 15 segundos** sin esperar enfriamiento. |
| **`07:30 – 09:01`** | **Sistema Automat (Kickstarter)** | Riel robótico externo frente a la impresora capaz de abrir y cerrar la puerta de impresoras cerradas (orientado a ABS y materiales técnicos), pero mucho más costoso y voluminoso. |

## 2. Desglose Mecánico del Kit AutoSwap A1 (`3vubNZdhSGA` y Fuentes Técnicas)

Del análisis de la guía de montaje **[¡AUTOMATIZA tu Bambu Lab A1 al 100%! Imprime sin parar](https://www.youtube.com/watch?v=3vubNZdhSGA)**, la ficha del **[Kit AutoSwap A1 en Nel 3D](https://nel-3d.com/products/autoswap-completo-a1)** y la reseña de ingeniería en **[Fabbaloo](https://www.fabbaloo.com/news/design-of-the-week-autoswap-bambu-lab-a1-plate-changer)** se extraen los componentes exactos que hacen funcionar el sistema original:

1. **Sujetador de Placa en ABS (`02:44 – 03:05` de [Nel 3D](https://www.youtube.com/watch?v=3vubNZdhSGA))**:
   - Cada placa PEI requiere atornillar en su borde trasero un adaptador impreso en **ABS** mediante **4 tornillos M3**.
   - Se utiliza ABS porque soporta sin ablandarse el calor directo de la cama caliente (60–80 °C) y los impactos repetitivos del mecanismo de enganche.
2. **Imanes de Neodimio de `20 × 10 × 2 mm` (`04:01 – 04:10` de [Nel 3D](https://www.youtube.com/watch?v=3vubNZdhSGA))**:
   - El acoplamiento entre el carro extractor y cada placa PEI se realiza mediante imanes rectangulares de neodimio de **`20 × 10 × 2 mm`** de alta potencia.
3. **Cable Bowden con Tubo PTFE de 1 m e Hilo de Pesca Trenzado (`04:10 – 04:40` de [Nel 3D](https://www.youtube.com/watch?v=3vubNZdhSGA))**:
   - Un hilo de pesca trenzado de alta resistencia al desgaste corre por el interior de **1 metro de tubo PTFE**.
   - Cuando el eje Z sube hasta el tope superior al terminar la impresión, tensa el hilo trenzado levantando el mecanismo retenedor (como confirma el reporte de usuario en **[Nel 3D](https://nel-3d.com/products/autoswap-completo-a1)**: si el cabezal no llega hasta arriba del todo, el archivo generado no activa la expulsión de la cama).
4. **Sensibilidad al Espesor y Geometría de Placas PEI (`11:22 – 11:55` de [Nel 3D](https://www.youtube.com/watch?v=3vubNZdhSGA))**:
   - Las tolerancias del gancho trasero dependen del grosor exacto de la lámina de acero para muelles (~0.5 mm) y del adhesivo magnético inferior.

## 3. Matriz de Adaptación Técnica para la Creality Ender 3 Pro

La **[Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer)** (especificaciones en **[3DPrinting.com](https://3dprinting.com/products/3d-printer/creality-ender-3-pro/)**) presenta diferencias estructurales respecto a la Bambu Lab A1 que justifican el diseño híbrido de `AutoSwapEnder3Pro`:

| Subsistema | Bambu Lab A1 (Original) | [Creality Ender 3 Pro](https://www.creality.com/products/ender-3-pro-3d-printer) | Decisión de Ingeniería en `AutoSwapEnder3Pro` |
| :--- | :--- | :--- | :--- |
| **Cama Magnética** | Placa de acero PEI 256 × 256 mm | Alfombrilla blanda *CMag* de **235 × 235 mm** | Reemplazo obligatorio por **[placas de acero flexible PEI de 235 × 235 mm](https://store.creality.com/products/smooth-pei-build-plate-235-235mm)** para permitir deslizamiento rígido |
| **Suspensión de Cama** | Fija con sensor piezoeléctrico | 4 ruedas manuales con muelles amarillos | Sustitución de muelles por **[espaciadores rígidos de silicona de 16–18 mm](https://www.aliexpress.com/item/1005006152753312.html)** para impedir que la cama se incline al tirar de las placas |
| **Chasis del Eje Y** | Riel integrado en base cerrada | Perfil de aluminio **V-Slot 4040** con motor Y trasero expuesto | Fijación del cargador trasero y de las cuñas frontales en las ranuras del perfil **V-Slot 4040** con tuercas en T (*T-nuts* M4) |
| **Accionamiento del Hilo** | Subida del eje Z al máximo (rápido en A1) | Husillo T8 lento en eje Z (riesgo de perder pasos en Z) | Incorporación de **[ESP32-DevKitC V4](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)** + **[servomotor metálico MG996R](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)** (11 kg·cm) para tensar el hilo en 1.2 segundos sin mover Z hasta 250 mm |
| **Orquestación de Trabajos** | Web **[AutoSwap GCode Manager](https://auto-swap.net/)** | Firmware **[Marlin](https://marlinfw.org/meta/gcode/)** por USB Serial / MicroSD | Herramienta local en Python (`autoswap_manager.py`) para **macOS** con **[pySerial](https://pyserial.readthedocs.io/en/latest/pyserial_api.html)** que combina G-codes y escucha el comando **[M118](https://marlinfw.org/docs/gcode/M118.html)** |

## 4. Fuentes Verificadas de la Investigación

- **Video Principal Analizado**: **[Convierte tu Impresora 3D en una Máquina Automática 24/7 — Nel 3D (YouTube)](https://www.youtube.com/watch?v=CNrtmL0N2PQ)**
- **Video de Montaje Técnico**: **[¡AUTOMATIZA tu Bambu Lab A1 al 100%! Imprime sin parar — Nel 3D (YouTube)](https://www.youtube.com/watch?v=3vubNZdhSGA)**
- **Página del Producto Comercial**: **[Kit AutoSwap A1 — Nel 3D](https://nel-3d.com/products/autoswap-completo-a1)**
- **Modelo 3D Original (EVRENOT)**: **[AutoSwap (Versión 2) BambuLab A1 Plate Changer Upgrade Kit — Cults3D](https://cults3d.com/es/modelo-3d/herramientas/autoswap-bambulab-a1-plate-changer-upgrade-kit-v1)**
- **Aplicación Web de Gestión de Colas**: **[AutoSwap — 3D Printer GCode Manager](https://auto-swap.net/)**
- **Análisis Independiente de Ingeniería**: **[Design of the Week: Autoswap Bambu Lab A1 Plate Changer — Fabbaloo](https://www.fabbaloo.com/news/design-of-the-week-autoswap-bambu-lab-a1-plate-changer)**
- **Especificaciones de la Impresora Objetivo**: **[Creality Ender 3 Pro Official](https://www.creality.com/products/ender-3-pro-3d-printer)** y **[3DPrinting.com — Creality Ender-3 Pro Specifications](https://3dprinting.com/products/3d-printer/creality-ender-3-pro/)**
- **Documentación de Hardware y Software**: **[ESP32-DevKitC V4 Guide — Espressif](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)**, **[MG996R Datasheet](https://www.handsontec.com/dataspecs/motor_fan/MG996R.pdf)**, **[Marlin Firmware G-Code Index](https://marlinfw.org/meta/gcode/)** y **[pySerial Documentation](https://pyserial.readthedocs.io/en/latest/pyserial_api.html)**

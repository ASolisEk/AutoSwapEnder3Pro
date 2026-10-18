# Lista de compras (AliExpress México) — AutoSwapEnder3Pro v3

> **Precios consultados el 17 de octubre de 2026** en [es.aliexpress.com](https://es.aliexpress.com) con región **México** (pesos, MXN). Tipo de cambio de referencia: **18,3 MXN por dólar** (FIX de Banxico ≈ 18,1–18,4 la semana del 12 de octubre de 2026).
>
> **Cómo leer los precios.** El buscador de AliExpress muestra el precio de la **variante más barata** de cada anuncio. Donde esa variante no es la que necesitas (por ejemplo, la fuente de 12 V 1 A en lugar de la de 5 A) el precio de la tabla es una **estimación de la variante correcta** y va marcado con `*`. Los precios cambian a diario, las ofertas de "nuevo comprador" no se han contado y el **envío y los impuestos** pueden variar: revisa siempre el total en el carrito. Los anuncios enlazados son ejemplos vistos ese día; si desaparecen, usa el enlace de búsqueda.
>
> **Antes de comprar:** mide tu impresora (Anexo A del plan) y haz las pruebas de fuerza T1–T3 (sección 6.5). Si `F_desl` pasa de 20 N, el eje lineal necesita un motor más fuerte o husillo.

## Resumen

| Bloque | MXN aprox. | USD aprox. |
| :--- | ---: | ---: |
| A. Impresora (7 placas, espaciadores, tornillería, filamento) | 1 580 | 86 |
| B. Estructura de la estación (perfiles, escuadras, PTFE, patas) | 1 480 | 81 |
| C. Eje lineal y ascensor (ruedas, 2 motores, correa, poleas) | 1 030 | 56 |
| D. Electrónica (UNO, CNC Shield, 2 TMC2209, servos, sensores, fuente, cableado) | 1 550 | 85 |
| **Total del sistema** | **≈ 5 640** | **≈ 308** |
| Total usando los drivers A4988 del kit en lugar de TMC2209 | ≈ 5 340 | ≈ 292 |
| E. Herramientas (si no las tienes) | 430 | 24 |

Cada placa extra (para un cargador de más niveles o repuesto) cuesta ~135 MXN + su zapata impresa.

---

## A. Para la impresora

| # | Componente | Qué elegir | Cant. | MXN c/u | Subtotal | Anuncio / búsqueda |
| :---: | :--- | :--- | :---: | ---: | ---: | :--- |
| A1 | **Placas de acero PEI 235 × 235** | Doble cara texturizada (o lisa). **Mejor con lengüeta frontal** (tipo Ender 3 V3 SE / K1); sin lengüeta también sirven (se colocan 11 mm adelantadas). Todas del **mismo modelo y lote** (mismo espesor) | 7 | 135 | 945 | [ej. 128,81](https://es.aliexpress.com/item/1005007766531020.html) · [ej. 131,37](https://es.aliexpress.com/item/1005008591794234.html) · [buscar](https://es.aliexpress.com/w/wholesale-pei-spring-steel-sheet-235x235.html) |
| A2 | Espaciadores de silicona para cama | 16 o 18 mm, juego de 8 | 1 | 31 | 31 | [ej. 30,90](https://es.aliexpress.com/item/1005005287093862.html) |
| A3 | Kit de tornillos Allen cabeza de botón | M2–M6 con tuercas (≈2 500 piezas): cubre M3 × 8/12/16, M5 × 8/10/12 | 1 | 92 | 92 | [ej. 92,38](https://es.aliexpress.com/item/1005007278965396.html) |
| A4 | Prisioneros M3 × 8 (punta plana, DIN916) | Bolsa de 50 (2 por zapata) | 1 | 25* | 25 | [ej. desde 20,51](https://es.aliexpress.com/item/1005005112644264.html) |
| A5 | Filamento **ASA** (o ABS) 1,75 mm | 1 kg (zapatas y topes: soportan el calor de la cama) | 1 | 231 | 231 | [SUNLU ASA 230,90](https://es.aliexpress.com/item/1005013260888061.html) |
| A6 | Filamento **PETG** 1,75 mm | 1 kg (resto de piezas, ~0,7 kg) | 1 | 258 | 258 | [Kingroon PETG 258,43](https://es.aliexpress.com/item/1005012697400978.html) |

> La base magnética original de la Ender 3 Pro (la lámina adhesiva negra) se reutiliza. Si está dañada, muchas placas se venden en kit con base nueva.

## B. Estructura de la estación

| # | Componente | Qué elegir | Cant. | MXN c/u | Subtotal | Anuncio / búsqueda |
| :---: | :--- | :--- | :---: | ---: | ---: | :--- |
| B1 | **Perfil de aluminio 2020 V-slot** (negro o plata) | Cortado a medida: 2 × 680, 4 × 310, 1 × 655, 1 × 270, 2 × 215, 2 × 245, 1 × 296 mm (≈ 4,8 m; lista de cortes en la guía) | 4,8 m | 210/m* | 1 010 | [ej. 10 piezas 300–1500 mm](https://es.aliexpress.com/item/1005012521582384.html) · [ej. 100–800 mm](https://es.aliexpress.com/item/1005004052530425.html) |
| B2 | Kit de escuadras 2020 + tuercas en T | 20 escuadras + 40 tuercas M5 + tornillos | 1 | 130 | 130 | [ej. 129,90](https://es.aliexpress.com/item/1005005748992965.html) |
| B3 | Tuercas en T M5 (martillo) para serie 20 | Bolsa de 100 | 1 | 64 | 64 | [ej. 64,12](https://es.aliexpress.com/item/1005007383347166.html) |
| B4 | Tornillos M5 × 35 + tuercas autoblocantes | 12 de cada (ejes de las ruedas) | 1 | 60* | 60 | [buscar](https://es.aliexpress.com/w/wholesale-m5-35mm-hex-socket-screw.html) |
| B5 | Patas niveladoras rosca **M6** | 6 unidades | 1 | 60* | 60 | [ej. desde 48,74](https://es.aliexpress.com/item/1005011786762722.html) |
| B6 | Cinta de PTFE adhesiva | 25 mm × 10 m, 0,13–0,18 mm | 1 | 62 | 62 | [ej. 61,72](https://es.aliexpress.com/item/1005007784038096.html) |
| B7 | Rodamientos 623ZZ (3 × 10 × 4) | Rodillo de la palanca del volteador | 2 | 21 | 42 | [ej. 41,50 (2)](https://es.aliexpress.com/item/1005013373114076.html) |
| B8 | Caja de recogida + espuma EVA + cartón rígido/MDF 3 mm para la rampa | Compra local (≥ 300 × 300 mm, ≤ 50 mm de alto en el lado de la estación) | 1 | 50* | 50 | Papelería / tlapalería |

## C. Eje lineal y ascensor

| # | Componente | Qué elegir | Cant. | MXN c/u | Subtotal | Anuncio / búsqueda |
| :---: | :--- | :--- | :---: | ---: | ---: | :--- |
| C1 | **Ruedas en V de POM** con rodamientos 625ZZ | Kit de 10 (tamaño estándar Openbuilds, Ø 24 mm). Se usan 12 (4 del carro + 8 del ascensor) | 2 kits | 243 | 486 | [ej. 242,90 (10)](https://es.aliexpress.com/item/1005007103968067.html) |
| C2 | Espaciadores excéntricos 6 mm | Bolsa de 10 (se usan 6) | 1 | 49 | 49 | [ej. 48,50](https://es.aliexpress.com/item/4000265390096.html) |
| C3 | Espaciadores de aluminio 6 mm para M5 | Bolsa de 10 (se usan 6) | 1 | 40* | 40 | [buscar](https://es.aliexpress.com/w/wholesale-6mm-aluminum-spacer-m5-v-wheel.html) |
| C4 | **Motor NEMA 17** 17HS4401 (≈ 40 N·cm, 1,5 A) | Con cable | 1 | 134 | 134 | [Usongshine 133,79](https://es.aliexpress.com/item/1005004586903773.html) |
| C5 | **Motor NEMA 17 con husillo T8 integrado** | **Paso 2 mm** (T8 × 2, autobloqueante), 150–200 mm, con tuerca de latón | 1 | 188* | 188 | [ej. desde 187,90](https://es.aliexpress.com/item/1005003762788198.html) |
| C6 | Kit 2 poleas GT2 20T (eje 5 mm) + 2 m de correa GT2 6 mm | Se usa 1 polea en el motor | 1 | 82 | 82 | [ej. 82,38](https://es.aliexpress.com/item/1005009939779429.html) |
| C7 | Polea loca GT2 20T **dentada**, con rodamientos, eje 3 mm | 6 mm de ancho de correa | 1 | 35* | 35 | [buscar](https://es.aliexpress.com/w/wholesale-gt2-idler-pulley-20t-3mm.html) |
| C8 | Tuerca T8 de brida, paso 2 mm (si el motor no la incluye) | Latón | 1 | 13 | 13 | [ej. 13,19](https://es.aliexpress.com/item/4000521111189.html) |

## D. Electrónica

| # | Componente | Qué elegir | Cant. | MXN c/u | Subtotal | Anuncio / búsqueda |
| :---: | :--- | :--- | :---: | ---: | ---: | :--- |
| D1 | **Arduino UNO R3** | Preferible con chip USB **ATmega16U2** (se distingue de la impresora, que usa CH340) + cable | 1 | 86 | 86 | [ej. 16U2 86,38](https://es.aliexpress.com/item/1005007544151736.html) · [CH340 50,50](https://es.aliexpress.com/item/1005003469601284.html) |
| D2 | **CNC Shield V3 + 4 drivers A4988** | Kit con disipadores | 1 | 59 | 59 | [ej. 58,59](https://es.aliexpress.com/item/1005009968121020.html) |
| D3 | Driver **TMC2209** BIGTREETECH V1.3 (opcional) | Más silencioso que A4988 | 2 | 149 | 298 | [ej. 148,90](https://es.aliexpress.com/item/1005012294697113.html) |
| D4 | **Servo MG996R** (engranaje metálico) | Volteador | 1 | 78 | 78 | [ej. 77,90](https://es.aliexpress.com/item/1005006223358432.html) |
| D5 | **Servo MG90S** (engranaje metálico) | Gancho (+1 de repuesto) | 2 | 27* | 54 | [ej. desde 26,59](https://es.aliexpress.com/item/1005007522665750.html) |
| D6 | Microinterruptores **KW11-3Z con rodillo** | Bolsa de 10 (HOME, HOME del ascensor, GANCHO_ENGANCHADO) | 1 | 55 | 55 | [ej. 55,13 (10)](https://es.aliexpress.com/item/32273125391.html) |
| D7 | **Sensor inductivo LJ8A3-2-Z/BX** (M8, NPN, normalmente abierto, 2 mm) | PLACA_EN_CAMA y PLACA_EN_DESCARGA (+1 de repuesto) | 2 | 73* | 146 | [ej. desde 72,90](https://es.aliexpress.com/item/1005013401008293.html) |
| D8 | Diodos 1N4148 | Protegen las entradas del Arduino de los sensores de 12 V | 1 bolsa | 20* | 20 | [buscar](https://es.aliexpress.com/w/wholesale-1n4148-diode.html) |
| D9 | Botón de paro tipo hongo 22 mm, contacto **NC**, con caja | | 1 | 43 | 43 | [ej. 42,65](https://es.aliexpress.com/item/1005005433584606.html) · [sin caja 12,60](https://es.aliexpress.com/item/32843542465.html) |
| D10 | **Fuente 12 V 5 A** (conector 5,5 × 2,1) | Elige la variante 5 A (60 W) | 1 | 120* | 120 | [ej. desde 118,17](https://es.aliexpress.com/item/1005013203658904.html) |
| D11 | Conector DC hembra 5,5 × 2,1 a bornes | 5 unidades | 1 | 23 | 23 | [ej. 23,33](https://es.aliexpress.com/item/1005008761529676.html) |
| D12 | **Reductor LM2596 con voltímetro** | 1 + 1 de repuesto | 2 | 31 | 62 | [ej. 30,91](https://es.aliexpress.com/item/1005007055625007.html) |
| D13 | Conectores **Wago 221** originales | Surtido 2/3/5 vías (10) | 1 | 96 | 96 | [ej. 95,79](https://es.aliexpress.com/item/1005012151944981.html) |
| D14 | Portafusibles en línea 5 × 20 + fusibles de 3 A | | 1 | 24 | 24 | [ej. 24,24](https://es.aliexpress.com/item/1005010144430566.html) |
| D15 | Cable de silicona 22 AWG, 5 colores | 5 m de cada color | 1 | 100 | 100 | [ej. 97,85](https://es.aliexpress.com/item/1005006351084127.html) |
| D16 | Cable de silicona 18 AWG rojo y negro | 2 m de cada uno | 1 | 76 | 76 | [ej. 76,30](https://es.aliexpress.com/item/1005008409314314.html) |
| D17 | Cables Dupont 20 cm (macho-hembra y hembra-hembra) | 40 + 40 | 1 | 21 | 21 | [ej. 20,51](https://es.aliexpress.com/item/1005006205169394.html) |
| D18 | Extensiones de servo 50 cm | Bolsa de 10 | 1 | 38 | 38 | [ej. 38,39](https://es.aliexpress.com/item/32948059501.html) |
| D19 | Cadena portacables 7 × 7 mm | 1 m | 1 | 79 | 79 | [ej. 78,90](https://es.aliexpress.com/item/1005012511385575.html) |
| D20 | Cable USB A–B 1 m (para el UNO) | | 1 | 20 | 20 | [ej. 19,76](https://es.aliexpress.com/item/1005009279617261.html) |
| D21 | Cable USB **de datos** para la impresora | Mini-USB (placa 1.1.x) o Micro-USB (placa 4.2.x) | 1 | 20 | 20 | [Mini-USB 19,94](https://es.aliexpress.com/item/1005003792051332.html) |
| D22 | Capacitor electrolítico 1000 µF 16 V | Estabiliza la línea de los servos | 1 | 34 | 34 | [ej. 33,97](https://es.aliexpress.com/item/1005012167135628.html) |

## E. Herramientas (si no las tienes)

| # | Herramienta | MXN | Anuncio |
| :---: | :--- | ---: | :--- |
| E1 | Multímetro digital | 62 | [ANENG SZ308](https://es.aliexpress.com/item/1005007097120431.html) |
| E2 | Calibrador (pie de rey) digital 150 mm | 94 | [ej. 93,68](https://es.aliexpress.com/item/1005013170353926.html) |
| E3 | Báscula colgante digital 50 kg (pruebas de fuerza) | 66 | [ej. 66,05](https://es.aliexpress.com/item/1005004622084461.html) |
| E4 | Pelacables automático | 105 | [ej. 105,49](https://es.aliexpress.com/item/1005009721712736.html) |
| E5 | Crimpadora de punteras + kit de punteras | 65 | [ej. 64,90](https://es.aliexpress.com/item/1005013225622520.html) |
| E6 | Galgas de espesores 0,02–1 mm | 40* | [buscar](https://es.aliexpress.com/w/wholesale-feeler-gauge.html) |
| — | Llaves Allen 1,5–5 mm, destornilladores de precisión, bridas, nivel de burbuja | — | Las de la Ender 3 Pro sirven |

## Consejos de compra

- **Agrupa el pedido** en pocas tiendas o en artículos *Choice* para pagar menos envío.
- Los **perfiles de aluminio** pesan: compara con tiendas locales o Mercado Libre, donde a veces los cortan a medida más baratos y llegan antes.
- Pide **todas las placas PEI del mismo anuncio y variante**: espesores distintos cambian la altura de la primera capa y el ajuste de la zapata.
- Si un vendedor no indica el **paso del husillo**, pregunta: debe ser **T8 × 2** (un giro = 2 mm). Con T8 × 8 el cargador puede bajar solo al apagar el motor (en ese caso pon `idle_disable` a 0).
- Comprueba que los sensores inductivos sean **NPN NO** ("BX"); los "AY/BY" (PNP) no sirven tal cual.

# AutoSwapEnder3Pro

Cambiador automático de placas PEI para la **Creality Ender 3 Pro**, inspirado en el [AutoSwap A1](https://nel-3d.com/products/autoswap-completo-a1) (EVRENOT / Nel 3D). Al terminar cada pieza, una **Estación de Cambio Frontal** retira la placa usada (con la pieza) y carga una limpia, sin esperar a que la cama se enfríe. Así la impresora puede imprimir una cola de hasta **7 trabajos seguidos** (1 placa en la cama + 6 en el cargador).

![Estación de Cambio Frontal](cad/img/ensamble.png)

## Cómo funciona

- La estación se coloca **delante** de la impresora, a la altura de la cama. No hay que modificar el firmware de la impresora.
- Un **carro** con un dedo retráctil tira de la placa usada por su **zapata** (pieza impresa en el borde de cada placa) hasta la **zona de descarga**; un **volteador** levanta el borde y la placa resbala a una caja.
- Un **cargador con ascensor** guarda 6 placas limpias en estantes; el carro empuja la siguiente hasta los **topes traseros** de la cama.
- Una **app para macOS y Windows** envía los trabajos a la impresora y ordena cada cambio, verificando 6 sensores. Ante cualquier fallo, pausa la cola y deja la impresora en estado seguro.

El razonamiento completo (por qué una cama móvil necesita un actuador propio, alternativas evaluadas, riesgos) está en el [plan detallado](PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md).

## Por dónde empezar

| Quiero... | Ve a |
| :--- | :--- |
| Comprar las piezas (precios de AliExpress México, oct-2026: ≈ 5 600 MXN / 310 USD) | [docs/BOM_ALIEXPRESS.md](docs/BOM_ALIEXPRESS.md) |
| Imprimir las piezas (28 STL listos, ~0,7 kg de PETG + 80 g de ASA) | [cad/README.md](cad/README.md) |
| Armar y calibrar paso a paso | [docs/TUTORIAL_ARMADO.md](docs/TUTORIAL_ARMADO.md) |
| Instalar y usar la app | [host/README.md](host/README.md) |
| Configurar el laminador | [slicer/README.md](slicer/README.md) |
| Regenerar las piezas con IA | [cad/PROMPTS_IA.md](cad/PROMPTS_IA.md) |
| Entender el diseño | [PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md](PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md) |

## Estado del proyecto (17-oct-2026)

| Parte | Estado |
| :--- | :--- |
| Diseño mecánico v3 (cargador con ascensor, volteador, carro con dedo en corredera) | ✅ Hecho: 16 diseños paramétricos OpenSCAD, 28 STL verificados |
| Firmware de la estación (Arduino UNO + CNC Shield V3) | ✅ Hecho: compila (RAM 41 %, flash 78 %), 20 pruebas de lógica sin hardware |
| App macOS/Windows (CLI + interfaz PySide6 + simuladores) | ✅ Hecha: 39 pruebas automáticas |
| Lista de compras con precios actuales | ✅ Hecha |
| Integración continua (macOS, Windows, Linux, firmware y CAD) | ✅ Configurada (`.github/workflows/ci.yml`) |
| Construcción física, calibración y pruebas de fiabilidad (fases 0, 1, 3, 6–8 del plan) | ⏳ Pendiente: requieren la impresora real; la guía de armado indica cada verificación |

> **Seguridad:** imprimir sin supervisión implica riesgo de incendio. Usa un firmware con protección térmica, coloca un detector de humo y supervisa las primeras colas completas.

## Estructura del repositorio

```
PLAN_DETALLADO_AUTOSWAP_ENDER3PRO.md  plan maestro (análisis, diseño, fases)
docs/        guía de armado y lista de compras
cad/         piezas impresas: .scad paramétricos, STL, imágenes, prompts para IA
firmware/    firmware de la estación (PlatformIO, Arduino UNO) con pruebas "native"
host/        app de escritorio (Python 3.11+): CLI, interfaz gráfica, simuladores, pruebas
slicer/      plantillas de G-code inicial y final para Cura, PrusaSlicer y OrcaSlicer
packaging/   scripts para crear la app instalable en macOS y Windows (PyInstaller)
legacy/      versión 1 del proyecto (ESP32), solo como referencia
```

## Prueba rápida sin hardware

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e "./host[gui]"
autoswap queue slicer/ejemplo_cuadro.gcode --copies 3 --simulate --yes
```

## Licencia

MIT — ver [LICENSE](LICENSE). El diseño original del AutoSwap A1 es de EVRENOT; este proyecto es una reinterpretación independiente para la Ender 3 Pro.

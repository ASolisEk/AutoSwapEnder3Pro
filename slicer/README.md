# Plantillas para el laminador (Cura, PrusaSlicer, OrcaSlicer)

Copia el contenido de `*_inicio.gcode` y `*_fin.gcode` en el perfil de la impresora de tu laminador:

| Laminador | Dónde se pega |
| :--- | :--- |
| **Cura** | *Preferencias → Impresoras → Ender-3 Pro → Ajustes de la máquina → G-code inicial / G-code final* |
| **PrusaSlicer** | *Ajustes de impresora → G-code personalizado → G-code inicial / final* |
| **OrcaSlicer** | *Impresora → Ajustes de la máquina → G-code de máquina → G-code inicial / final* |

## Área de impresión

| Tipo de placa | Área recomendada en el laminador | Por qué |
| :--- | :--- | :--- |
| Con **lengüeta** delantera (la zapata va en la lengüeta) | 220 × 220 mm | Toda la placa queda sobre la cama |
| **Sin lengüeta** (la placa se coloca 11 mm adelantada) | 220 × 205 mm | Los primeros 11 mm de la placa sobresalen de la cama y la zapata ocupa el borde |

En ambos casos:

- **Altura máxima de pieza: 150 mm** (la app rechaza trabajos más altos; lo limita el cargador).
- Evita imprimir en el **centro del borde delantero** (una franja de 60 × 15 mm): ahí está la zapata, que sobresale 1,9 mm. En Cura se puede marcar como *zona no permitida*; en PrusaSlicer/OrcaSlicer basta con no colocar piezas ahí.
- Deja libres las **esquinas traseras a ±70 mm del centro** (topes traseros).
- **Primera capa:** la placa nueva llega fría. La app espera `plate_warmup_s` (60 s por defecto) tras cada cambio y el G-code inicial vuelve a esperar a la cama con `M190`.

## Reglas del G-code final

El G-code final **no** debe:

- desactivar motores (`M84`, `M18`): la cama perdería su posición durante el cambio;
- apagar la cama (`M140 S0`): se mantiene caliente entre trabajos para ahorrar tiempo;
- mover la cama al frente para "presentar la pieza" (`G1 Y235`): de eso se encarga la app.

Si usas un perfil que ya trae esas órdenes, la app las detecta y las omite (las muestra en `autoswap analyze archivo.gcode`), pero es mejor dejar el perfil limpio con estas plantillas.

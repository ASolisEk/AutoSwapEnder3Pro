# Prompts para regenerar las piezas con IA

Estos prompts sirven para pedirle a un asistente de IA (generador de OpenSCAD, CadQuery/build123d, o una herramienta de "texto a CAD") que vuelva a crear o modifique cada pieza. Cada prompt es **autosuficiente**: incluye la función, las medidas, las tolerancias y lo que hay que comprobar.

**Cómo usarlos**

1. Copia primero el **contexto común** y después el prompt de la pieza.
2. Pide siempre el resultado como **código paramétrico** (OpenSCAD o CadQuery), no solo como STL: así puedes ajustar medidas.
3. Revisa el resultado con la **lista de comprobación** de cada pieza y con `python3 tools/revisar_stl.py`.
4. Imprime primero una pieza de prueba al 100 % y compárala con las piezas reales (placa, perfil, servo) antes de imprimir todo.

> La IA puede equivocarse con las medidas o la orientación. Los `.scad` de esta carpeta son la referencia: si un modelo generado no coincide con ellos en las cotas críticas (marcadas con ⚠), corrígelo.

---

## Contexto común (pégalo antes de cada prompt)

```text
Contexto: diseño piezas impresas en 3D para un cambiador automático de placas PEI para una
impresora Creality Ender 3 Pro (cama móvil de 235 x 235 mm). Las piezas se imprimen en una
Ender 3 Pro (área útil 220 x 220 x 250 mm) con boquilla de 0,4 mm, en PETG (o ABS/ASA si se indica).
Requisitos generales:
- Entrega código PARAMÉTRICO (OpenSCAD con variables al principio, o CadQuery en Python).
- Unidades en mm. Holgura de impresión general 0,3 mm. Paredes de al menos 2 mm.
- Orienta la pieza para imprimir SIN soportes y apoyada en z = 0; indica la orientación.
- Tornillería métrica: M3 (paso libre 3,4 mm; tuerca 5,5 mm entre caras -> alojamiento 5,7 mm;
  para roscar en plástico 2,7 mm), M5 (paso libre 5,4 mm; cabeza 8,5 mm -> 9,2 mm), M2 para servos
  (autorroscante, agujero 1,8 mm).
- Perfil de aluminio 2020 V-slot (20 x 20 mm, ranura de 6,2 mm, tuercas en T M5).
- Ruedas en V estándar Openbuilds (diámetro 23,9 mm, ancho 10,2 mm, rodamientos 625): en un
  perfil 2020 los centros de dos ruedas enfrentadas quedan a 39,26 mm; espaciador de 6 mm entre
  rueda y placa; un lado usa espaciador excéntrico (alojamiento de 7,2 mm).
Sistema de coordenadas de la estación: s a lo largo (0 = posición HOME del carro, crece hacia la
impresora), x a lo ancho (0 = riel lineal central), z vertical (0 = cara superior de la base de
perfiles). El plano por donde se deslizan las placas está en z = 60. La cara superior del riel
lineal está en z = 20.
Explica brevemente cada operación del código con comentarios en español.
```

---

## 1. Zapata (una por placa) — ABS/ASA

```text
Diseña la "zapata": una pieza que se sujeta al borde delantero de una placa de acero PEI de
235 x 235 x 0,6 mm sin taladrarla. Coordenadas locales: y = 0 en el borde de la placa, y < 0 hacia
dentro de la placa, y > 0 hacia fuera; z = 0 en la cara inferior de la placa.
- Cuerpo inferior: x de -24 a 24, y de -10 a 16, z de -8 a 0. ⚠ No debe sobresalir por debajo más de 8 mm.
- Ranura horizontal para la placa: alto 0,95 mm (espesor de placa + 0,35), abierta hacia -y,
  profundidad 10 mm. Pared frontal en y de 0,3 a 16 con la altura total de la pieza.
- Labio superior: x de -20 a 20, y de -10 a 1, 1,5 mm de espesor encima de la ranura.
  ⚠ La parte superior no puede sobresalir más de 1,9 mm por encima de la cara superior de la placa.
- Bolsillo para el dedo, abierto hacia abajo: x de -5,5 a 5,5, y de 2 a 10, 6 mm de profundidad,
  con chaflán de entrada de 1,2 mm.
- Dos prisioneros M3 x 8 verticales desde abajo en (x = ±12, y = -5): taladro de 3,4 mm y tuerca
  M3 atrapada a z = -4 que se introduce por un canal desde cada cara lateral. El prisionero empuja la
  placa contra el labio.
- Chaflanes de 1 mm en las aristas inferiores (los rodillos de los sensores pasan por debajo).
- Imprimir boca abajo (labio sobre la cama).
Comprobación: medidas exteriores 48 x 26 x 10,4 mm; el dedo de 6 x 5 mm entra en el bolsillo con
holgura; una placa de 0,6 mm entra en la ranura sin forzar.
```

## 2. Tope trasero (2 unidades) — ABS/ASA

```text
Diseña un tope que se pinza al borde trasero de la cama de aluminio de la Ender 3 Pro (aluminio
de 3 mm + base magnética de 1 mm). Coordenadas: y = 0 en el borde trasero de la cama, y < 0 hacia
el frente; z = 0 en la cara inferior del aluminio. Ancho 30 mm (x de -15 a 15).
- Bloque trasero: y de 0,3 a 10,3, z de -9 a 5,8 (5,8 = 4 + 1,8).
- Mordaza superior (cara de tope): y de -3 a 1, z de 4 a 5,8; apoya 3 mm sobre la base magnética y
  sobresale 1,8 mm. ⚠ La cara en y = -3 es la referencia contra la que se empuja la placa.
- Mordaza inferior: y de -9 a 2, z de -9 a -0,3, con un tornillo M3 vertical en y = -5 que aprieta
  contra la cara inferior del aluminio y tuerca M3 atrapada (canal abierto hacia -y).
- Ranura para el canto de la cama: alto 4,3 mm.
- Chaflán de 0,5 mm en la arista superior de la cara de tope.
- Imprimir apoyada sobre la cara trasera (y = 10,3) para no necesitar soportes.
Comprobación: entra en un canto de 4 mm; la cara de tope queda 1,8 mm sobre la base magnética.
```

## 3. Carro (base) — PETG

```text
Diseña la placa de un carro que corre sobre un perfil 2020 horizontal con 4 ruedas en V.
Coordenadas: x = 0 eje del perfil, y a lo largo del perfil (+y hacia la impresora), z = 0 cara
superior del perfil.
- Placa: x de -40 a 32, y de -40 a 40, z de 1,1 a 6,1 (5 mm), esquinas redondeadas r = 4.
- Ruedas: centros en (x = ±19,63, y = ±25); lado +x taladro 5,3 mm (fijas), lado -x taladro 7,2 mm
  (espaciador excéntrico). ⚠ La distancia entre centros a través del perfil es 39,26 mm.
- Paso para un dedo vertical de 7 x 9 mm centrado en (0, 30): agujero 7,6 x 9,6.
- 4 tornillos M3 para la torre en (-30, 6), (-30, 36), (10, 6), (10, 36) con tuerca hexagonal
  embutida por debajo.
- Brazo lateral para la correa: x de -46 a -36, y de -40 a -8, que baja hasta z = -16. Dos ranuras
  verticales de 1,6 mm de ancho centradas en x = -41,63 (tramo de un lazo de correa GT2 cuyo centro
  está en x = -48), abiertas por abajo, alto 7,5 mm, largo 12 mm, en y de -38 a -26 y de -22 a -10,
  con dientes GT2 (semicilindros r = 0,55 cada 2 mm) en la pared -x, y una ranura transversal para
  brida.
- Oreja para cadena portacables en el extremo -y con 2 taladros M3 a 10 mm.
- Imprimir boca abajo (cara superior apoyada en la cama).
Comprobación: medidas 78 x 92 x 22 mm; las ruedas no tocan el brazo de la correa.
```

## 4. Torre del gancho — PETG

```text
Diseña una torre que se atornilla encima del carro anterior (cara superior del carro en z = 6,1;
mismas coordenadas). Contiene un "dedo" vertical que sube y baja 8 mm, movido por un servo MG90S.
- Base: x de -38 a 14, y de 0 a 40, 2 mm de espesor, con los 4 taladros M3 del carro.
- Canal del dedo: 7,5 x 9,5 mm centrado en (0, 30), que atraviesa la base; paredes de 3 mm;
  altura de la torre hasta z = 30. ⚠ Nada de la torre puede superar z = 30.
- En la pared -x del canal, una ranura vertical de 4,4 mm (y de 27,8 a 32,2) y de z = 8,8 a 19,6,
  por donde entra un pasador M2 que mueve el dedo (yugo escocés).
- Cuna para un servo MG90S tumbado: eje del servo a lo largo de x, en y = 22, z = 14,2; cara superior
  del servo en x = -13; cuerpo de 22,8 x 12,2 x 22,5 mm hacia -x; pared vertical (x de -16,9 a -13)
  con una ventana para el cuerpo; las pestañas (32,4 mm en total, 2,5 mm de espesor, taladros a
  27,8 mm) apoyan en su cara -x y se fijan con autorroscantes M2 a lo largo de x.
- Soporte vertical para un microinterruptor KW11-3Z con rodillo en la cara +x (x de 11 a 14,
  y de 4 a 24), con dos ranuras M2 verticales separadas 9,5 mm, regulables ±3 mm.
Comprobación: un dedo de 7 x 9 mm desliza sin juego lateral apreciable; el servo encaja en la cuna.
```

## 5. Dedo del gancho — PETG (100 % relleno)

```text
Diseña una corredera vertical: sección inferior 7 (x) x 9 (y) x 17 mm de alto; encima una punta
de 6 x 5 x 5,8 mm con chaflán de 0,8 mm en la parte superior. Ranura horizontal abierta hacia -x
para un pasador M2: centrada a 4 mm de la base, 3,2 mm de profundidad, 4,6 mm de largo (en y) y
2,4 mm de alto. Altura total 22,8 mm. Imprimir de pie.
```

## 6. Soportes del eje lineal (motor y polea loca) — PETG

```text
Diseña dos piezas para un lazo de correa GT2 horizontal (poleas con eje vertical), cuya banda de
6 mm está entre z = 6 y z = 12 sobre la cara superior de un travesaño 2020.
A) Soporte del motor NEMA 17 boca abajo (eje hacia abajo): placa de 46 x 46 x 4 mm a z = 16 con
   agujero central ranurado (23 mm, ±4 mm a lo largo de y para tensar la correa) y 4 taladros M3
   ranurados en cuadrado de 31 mm; dos paredes laterales de 4 mm hasta la base; pie de 50 x 20 mm
   con 2 taladros M5 (separados 30 mm) para tuercas en T del travesaño.
B) Soporte de la polea loca GT2 20T (eje M3 vertical): placa inferior y placa superior en voladizo
   (a z = 15 … 18,5) con el taladro del eje M3 y tuerca atrapada abajo; pared trasera; pie con dos
   taladros M5 ranurados ±2 mm en x, a 6 mm del eje de la polea.
Comprobación: la polea gira libre entre las placas; la correa pasa entre z = 6 y 12.
```

## 7. Tapa del riel derecho — PETG

```text
Diseña una tapa de 135 mm de largo que va encima de un perfil 2020 (x = 0 centro del perfil, z = 0
cara superior del perfil). Grosor 4 mm; ancho desde x = -22 hasta x = 8,5, y una ceja redondeada de
2,5 x 1,5 mm en x de 8,5 a 11. En la parte inferior, una lengüeta de 5,7 x 1,5 mm que encaja en la
ranura superior del perfil. Chaflán de entrada en ambos extremos de la cara superior (caída de
0,8 mm en 4 mm). Dos tornillos M5 avellanados a 20 mm de cada extremo. Imprimir de lado para que
la cara superior (por donde desliza la placa) salga lisa.
```

## 8. Pedestales — PETG

```text
A) Pedestal del riel: levanta un perfil 2020 de modo que su cara inferior quede 36 mm por encima de
   la cara superior de un travesaño 2020. Columna de 20 x 20 mm, pie de 28 x 20 x 4 mm, mejillas
   laterales que abrazan el perfil superior con un M5 horizontal a cada lado y un M5 vertical al
   travesaño (con ventana para meter la llave).
B) Pedestal de bisagra: sostiene un eje horizontal M5 (a lo largo de s) a 48 mm sobre el travesaño;
   espesor 10 mm en s; pie de 36 x 10 mm con 2 M5; repisa de tope cuya cara superior queda a 52 mm,
   entre 6 y 16 mm del eje hacia el centro de la estación.
```

## 9. Volteador (tapa basculante) — PETG

```text
Diseña una tapa basculante de 240 mm de largo (s de 280 a 520) partida en dos mitades de 120 mm.
Gira sobre un eje horizontal a lo largo de s situado en x = -128, z = 48.
- Superficie superior plana en z = 60, de x = -123 a x = -25, 4 mm de espesor.
- Pared guía en el borde exterior: x de -123 a -119,5, 5 mm por encima de la superficie.
- Tubo de bisagra de 12 mm de diámetro exterior y 5,3 mm interior alrededor del eje, unido a la
  superficie con un alma.
- Nervios inferiores de 3 x 4 mm cada 40 mm (en x) y 2 longitudinales; pista de contacto continua de
  3 mm de espesor bajo la superficie, de x = -118 a x = -70 (por ella rueda la palanca del servo).
- Orejas de tope de 10 x 5 x 4 mm en los extremos exteriores (x de -122 a -112, z de 52 a 56).
- Pieza de unión de 66 x 36 x 3 mm con 6 tornillos M3 bajo la junta de las dos mitades.
- Imprimir cada mitad de pie, sobre el extremo sin oreja, con borde de adherencia.
```

## 10. Soporte del servo del volteador y palanca — PETG

```text
A) Soporte para un servo MG996R (caja 40,7 x 19,7 x 37 mm; orejas a 27,5 mm de la base, 2,5 mm de
   espesor, taladros a 48,5 x 10 mm). El servo queda con su eje horizontal a lo largo de s, en
   x = -110, z = 32, el lado largo de la caja en vertical y el eje a 10,2 mm de su extremo superior.
   Placa vertical (perpendicular a s) con ventana para el cuerpo; las orejas apoyan en su cara +s.
   Base de 25 x 34 mm atornillada a un travesaño 2020 con 2 M5. ⚠ Nada del soporte puede superar
   z = 52 (por encima pasa el volteador).
B) Palanca: disco de 26 mm x 4 mm con 8 ranuras radiales para fijarla al disco del servo, brazo de
   35 mm y, en la punta, taladro de 2,7 mm para un tornillo M3 que sostiene un rodamiento 623ZZ.
```

## 11. Peine del cargador — PETG

```text
Diseña la pared de un cargador de placas: 121 mm de largo (s), pared de 3 mm en x de 119 a 122 y
6 estantes horizontales que vuelan 10 mm hacia el centro (x de 109 a 119), 2,5 mm de espesor, con
la cara superior del estante k a z = 14·k (paso de 14 mm). Refuerzos de 4 x 3 mm bajo cada estante
en tres puntos. Chaflanes de entrada en ambos extremos de cada estante. Arriba (z de 76 a 96) una
zona engrosada hacia dentro con 2 tornillos M5 horizontales (cabeza hacia dentro) para fijarla a
un perfil 2020 longitudinal colocado en x de 122 a 142. Generar versión derecha y su simétrica
izquierda. Imprimir tumbada sobre la cara exterior.
Comprobación: una placa de 235 mm de ancho cabe entre dos peines enfrentados (caras interiores en
x = ±119) apoyando 8 mm por lado.
```

## 12. Ascensor del cargador — PETG

```text
A) Placa de 70 x 64 x 6 mm que corre por un poste 2020 vertical con 4 ruedas en V (ejes a lo largo de
   x, en s = ±19,63 y z = ±25 respecto al centro; lado -s con espaciador excéntrico). La placa está
   en x de 147,9 a 153,9 (el poste en x de 155 a 175). Taco hasta x = 142 con 2 tornillos M5 para
   atornillar un perfil 2020 longitudinal (x de 122 a 142) y 2 taladros M5 arriba para una escuadra.
   Versión izquierda simétrica con una prolongación en +s (hasta s = +75) y 2 taladros M3 para el
   soporte de la tuerca.
B) Soporte de tuerca de brida T8 (cuerpo 10,4 mm, brida 22 mm, 4 taladros M3 en círculo de 16 mm)
   cuyo eje queda en x = 165, s = +59 respecto al poste, atornillado a la prolongación con 2 M3.
C) Soporte de NEMA 17 con husillo T8 integrado (eje hacia arriba): placa de 46 x 46 x 5 mm a 42 mm de
   altura, pared y pie con 2 M5 a un perfil 2020 de la base.
```

## 13. Soportes de sensores — PETG

```text
A) Soporte de microinterruptor KW11-3Z: pie de 20 x 34 x 4 mm con ranura M5 de 12 mm y pestaña
   vertical de 4 mm con 2 ranuras M2 separadas 9,5 mm (regulables ±4 mm).
B) Soporte de sensor inductivo M8 (LJ8A3-2-Z/BX): pestaña horizontal de 5 mm con agujero de 8,4 mm
   a 34 mm sobre un pie con 2 M5; el agujero queda 7 mm desplazado del eje del travesaño.
C) Igual que B pero para atornillarse a la cara lateral de un perfil (2 M5 a lo largo de la ranura)
   con la pestaña a 11 mm y el agujero a 14 mm del perfil.
```

## 14. Caja de la electrónica — PETG o PLA

```text
Caja para Arduino UNO + CNC Shield V3 + reductor LM2596: interior 150 x 100 x 52 mm, pared 2,4 mm,
suelo 3 mm. Postes de 6 mm con taladro de 2,7 mm en las posiciones oficiales del UNO (13,97/2,54;
15,24/50,8; 66,04/7,62; 66,04/35,56 mm desde su esquina). Ventana para el USB-B, agujero de 8 mm
para un conector DC de panel, 6 ranuras de salida de cables de 20-24 x 9 mm, rejilla inferior, 2
orejas con M5 para un perfil 2020. Tapa con 4 tornillos M3, rejilla y agujero para ventilador de
40 mm sobre los drivers.
```

## 15. Pie nivelador — PETG

```text
Pie lateral para un perfil 2020: placa vertical de 5 x 40 x 20 mm que se atornilla a la ranura
lateral del perfil (M5 horizontal a 10 mm de altura, con hueco para la cabeza), y un ala horizontal
de 22 x 40 x 8 mm en la parte superior (z de 12 a 20) que sobresale hacia fuera, con un taladro
vertical de 6,4 mm y una tuerca M6 atrapada por arriba para una pata niveladora M6. Refuerzos
triangulares en los extremos. Así el perfil puede quedar casi a ras de la mesa.
```

---

## Prompt para revisar un modelo generado

```text
Revisa este código CAD de una pieza imprimible. Comprueba: (1) que todas las cotas críticas
coinciden con la especificación que te doy; (2) que no hay paredes de menos de 2 mm salvo donde se
pide; (3) que la pieza apoya en z = 0 y se imprime sin soportes en la orientación indicada; (4) que
los agujeros de tornillo tienen la holgura correcta (M3 3,4 mm, M5 5,4 mm); (5) que cabe en
220 x 220 x 250 mm. Devuelve una lista de errores y el código corregido.
```

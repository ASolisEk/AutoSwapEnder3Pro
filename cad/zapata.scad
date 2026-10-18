// =====================================================================
// ZAPATA - se sujeta al borde delantero de cada placa PEI (1 por placa)
// Material: ABS o ASA (PETG como minimo). 4 perimetros, 40 % relleno.
// Imprimir en la orientacion del STL (labio superior apoyado en la cama).
//
// Funcion: el dedo del carro entra en el BOLSILLO inferior para tirar de la
// placa (expulsar) y para empujarla (cargar). La placa queda pinzada entre el
// labio superior y 2 prisioneros M3 x 8 (sin taladrar la placa).
//
// Coordenadas: y = 0 en el borde de la placa; y < 0 hacia la cama (encima de
// la placa); y > 0 hacia la estacion. z = 0 en la cara inferior de la placa.
// =====================================================================
include <lib/comun.scad>

abrazadera = min(10, voladizo - 1); // tramo que pinza la placa (debe quedar delante de la cama)
frente     = 16;    // cuanto sobresale hacia la estacion desde el borde de la placa
ancho_inf  = 48;    // ancho del cuerpo inferior (los rodillos de los sensores pisan aqui)
ancho_lab  = 40;    // ancho del labio superior
bajo       = zapata_bajo;    // 8 mm por debajo de la placa
labio      = 1.5;   // espesor del labio (queda 1.85 mm por encima de la placa)
ranura_h   = placa_esp + 0.35;
alto       = ranura_h + labio;
// bolsillo del dedo
bol_x      = 11;    // ancho (el dedo mide 6)
bol_y0     = 2;     // empieza 2 mm por delante del borde de la placa
bol_y      = 8;     // largo (el dedo mide 5)
bol_h      = zapata_bolsillo;
// prisioneros
pris_x     = 12;
pris_y     = -abrazadera / 2;
tuerca_z   = -4;

module zapata() {
  difference() {
    union() {
      // cuerpo inferior
      translate([-ancho_inf / 2, -abrazadera, -bajo]) caja_r([ancho_inf, abrazadera + frente, bajo], 2);
      // pared frontal (el borde de la placa apoya aqui al empujar)
      translate([-ancho_inf / 2, 0.3, 0]) caja_r([ancho_inf, frente - 0.3, alto], 2);
      // labio superior
      translate([-ancho_lab / 2, -abrazadera, ranura_h]) caja_r([ancho_lab, abrazadera + 1, labio], 1.5);
    }
    // bolsillo del dedo con chaflan de entrada
    translate([-bol_x / 2, bol_y0, -bajo - 0.1]) cube([bol_x, bol_y, bol_h + 0.1]);
    hull() {
      translate([-bol_x / 2, bol_y0, -bajo - 0.1]) cube([bol_x, bol_y, 0.01]);
      translate([-bol_x / 2 - 1.2, bol_y0 - 1.2, -bajo - 0.1]) cube([bol_x + 2.4, bol_y + 2.4, 0.01]);
      translate([-bol_x / 2, bol_y0, -bajo + 1.2]) cube([bol_x, bol_y, 0.01]);
    }
    // prisioneros M3 desde abajo + tuercas insertadas por los costados
    for (sx = [-1, 1]) {
      translate([sx * pris_x, pris_y, -bajo - 0.1]) cylinder(d = m3, h = bajo + 0.2);
      translate([sx * pris_x, pris_y, tuerca_z - m3_tuerca_h / 2 - 0.1]) rotate([0, 0, 30])
        hexagono(m3_tuerca, m3_tuerca_h + 0.2);
      // canal para meter la tuerca desde el lateral
      translate([sx > 0 ? sx * pris_x : -ancho_inf / 2 - 1, pris_y - m3_tuerca / 2, tuerca_z - m3_tuerca_h / 2 - 0.1])
        cube([ancho_inf / 2 - pris_x + 1, m3_tuerca, m3_tuerca_h + 0.2]);
    }
    // chaflanes inferiores (los rodillos de los sensores y las transiciones no se enganchan)
    for (sy = [-abrazadera, frente]) translate([0, sy, -bajo]) rotate([45, 0, 0])
      cube([ancho_inf + 2, 1.6, 1.6], center = true);
    for (sx = [-ancho_inf / 2, ancho_inf / 2]) translate([sx, (frente - abrazadera) / 2, -bajo]) rotate([0, 45, 0])
      cube([1.6, abrazadera + frente + 2, 1.6], center = true);
  }
}

// Orientacion de impresion: boca abajo (el labio apoyado en la cama de la impresora)
rotate([180, 0, 0]) translate([0, 0, -alto]) zapata();

// =====================================================================
// CARRO (BASE) - placa con 4 ruedas en V que corre sobre el riel lineal 2020
// Material: PETG. 5 perimetros, 40 % relleno. Imprimir boca abajo (como sale
// el STL: cara superior apoyada en la cama, sin soportes).
//
// - Ruedas: lado +x fijas (M5 + espaciador 6 mm), lado -x con espaciador excentrico.
// - Brazo lateral (lado -x) con 2 pinzas de correa GT2: la correa forma un lazo
//   horizontal a un lado del riel (x = -48), asi el motor y la polea loca no
//   estorban en los extremos (ver docs/TUTORIAL_ARMADO.md, fase 4).
// - Encima se atornilla carro_torre.scad (4 x M3 con tuerca por debajo).
//
// Coordenadas: x = 0 eje del riel; y a lo largo del riel (+y hacia la impresora);
// z = 0 cara superior del riel lineal.
// =====================================================================
include <lib/comun.scad>

placa_z0   = -10 + rueda_ancho / 2 + espaciador_h;  // = 1.1: cara inferior de la placa
placa_h    = 5;
placa_x    = [-40, 32];
placa_y    = [-40, 40];
rueda_y    = 25;          // ruedas en y = +-25
dedo       = [0, 30];     // posicion (x, y) del dedo del gancho
dedo_paso  = [7.6, 9.6];  // agujero para el dedo
lazo_x     = -48;         // centro del lazo de correa
correa_x   = lazo_x + 6.37;  // tramo que se pinza (paso primitivo GT2 20T = 12.73)
correa_z   = [-14, -8];   // banda de la correa (6 mm)
brazo_x    = [-46, -36];
brazo_y    = [-40, -8];      // solo en la mitad HOME: asi no choca con la polea loca
torre_tornillos = [[-30, 6], [-30, 36], [10, 6], [10, 36]];

module pinza_correa(y0, largo = 12) {
  // ranura vertical abierta por abajo, con dientes GT2 en la pared exterior
  translate([correa_x - 0.8, y0, correa_z[0] - 1.5]) cube([1.6, largo, correa_z[1] - correa_z[0] + 1.5]);
}

module dientes(y0, largo = 12) {
  for (i = [0:2:largo - 1]) translate([correa_x - 0.8, y0 + i + 1, correa_z[0] - 1.5])
    cylinder(r = 0.55, h = correa_z[1] - correa_z[0] + 1.5, $fn = 12);
}

module carro_base() {
  difference() {
    union() {
      translate([placa_x[0], placa_y[0], placa_z0])
        caja_r([placa_x[1] - placa_x[0], placa_y[1] - placa_y[0], placa_h], 4);
      // brazo de la correa
      translate([brazo_x[0], brazo_y[0], correa_z[0] - 2])
        caja_r([brazo_x[1] - brazo_x[0], brazo_y[1] - brazo_y[0], placa_z0 + placa_h - correa_z[0] + 2], 2);
      // oreja para la cadena portacables (extremo HOME)
      translate([-40, placa_y[0] - 12, placa_z0]) caja_r([22, 14, placa_h], 3);
    }
    // ruedas
    for (sy = [-1, 1]) {
      translate([rueda_sep / 2, sy * rueda_y, placa_z0 - 1]) cylinder(d = 5.3, h = placa_h + 2);
      translate([-rueda_sep / 2, sy * rueda_y, placa_z0 - 1]) cylinder(d = excentrica_d, h = placa_h + 2);
    }
    // paso del dedo
    translate([dedo[0] - dedo_paso[0] / 2, dedo[1] - dedo_paso[1] / 2, placa_z0 - 1])
      cube([dedo_paso[0], dedo_paso[1], placa_h + 2]);
    // tornillos de la torre: tuerca M3 por debajo
    for (p = torre_tornillos) translate([p[0], p[1], placa_z0]) taladro_m3_tuerca(placa_h);
    // pinzas de correa en los dos extremos del brazo + bridas
    for (y0 = [brazo_y[0] + 2, brazo_y[1] - 14]) {
      pinza_correa(y0);
      translate([brazo_x[0] - 1, y0 + 3, correa_z[0] - 2.1]) cube([brazo_x[1] - brazo_x[0] + 2, 3.5, 2.2]);
    }
    // cadena portacables
    for (i = [-34, -24]) translate([i, placa_y[0] - 5, placa_z0 - 1]) cylinder(d = m3, h = placa_h + 2);
  }
  // dientes GT2 (se suman despues del vaciado)
  for (y0 = [brazo_y[0] + 2, brazo_y[1] - 14]) intersection() {
    dientes(y0);
    translate([correa_x - 0.8, y0, correa_z[0] - 1.5]) cube([0.6, 12, 10]);
  }
}

// Orientacion de impresion: boca abajo
rotate([180, 0, 0]) translate([0, 0, -(placa_z0 + placa_h)]) carro_base();

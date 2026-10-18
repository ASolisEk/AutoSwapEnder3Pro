// =====================================================================
// ASCENSOR DEL CARGADOR - sube y baja los peines de 14 en 14 mm
// Material: PETG. 5 perimetros, 40 %. Imprimir como sale el STL.
//   pieza = "placa_der" : placa con 4 ruedas en V para el poste derecho
//   pieza = "placa_izq" : placa izquierda (simetrica) con prolongacion para la tuerca
//   pieza = "tuerca"    : soporte de la tuerca de brida T8 (va en la placa izquierda)
//   pieza = "motor"     : soporte del NEMA 17 con husillo T8 integrado (eje hacia arriba)
//
// Esquema (como el eje Z de la Ender 3): dos postes 2020 verticales en s = 141,
// x = +-165. En cada poste corre una placa con 4 ruedas. Cada placa lleva
// atornillado el perfil 2020 longitudinal de su peine (x 122-142) y, arriba, el
// travesaño "arco" (2020 a lo ancho, con 2 escuadras) que une ambas placas. El
// motor (lado izquierdo, s = 200) mueve la tuerca T8. Usa husillo T8 de PASO 2 mm:
// es autobloqueante y el cargador no baja solo con el motor sin corriente.
//
// Coordenadas de las placas: x de la estacion (lado derecho), y = s - 141,
// z = 0 en el centro de la placa.
// =====================================================================
include <lib/comun.scad>

pieza = "placa_der";

poste_x  = 165;
placa_x  = [poste_x - rueda_ancho / 2 - espaciador_h - 6, poste_x - rueda_ancho / 2 - espaciador_h];
riel_x   = [122, 142];     // perfil longitudinal del peine
alto     = 70;
ancho    = 64;
ruedas_z = 25;
husillo_y = 200 - 141;     // eje del husillo (y local)
ext_y    = [ancho / 2 - 4, husillo_y + 16];   // prolongacion de la placa izquierda
tuerca   = [10.4, 22, 16, 3.5];  // tuerca T8 de brida: cuerpo, brida, circulo de taladros, taladros

module placa(prolongacion) {
  e = placa_x[1] - placa_x[0];
  difference() {
    union() {
      translate([placa_x[0], -ancho / 2, -alto / 2]) caja_r([e, ancho, alto], 4);
      // taco hasta el perfil del peine
      translate([riel_x[1], -ancho / 2 + 6, -19]) cube([placa_x[0] - riel_x[1] + 0.01, ancho - 12, 28]);
      if (prolongacion) translate([placa_x[0], ext_y[0], -10]) caja_r([e, ext_y[1] - ext_y[0], 20], 3);
    }
    // ruedas (eje a lo largo de x): lado +s fijas, lado -s excentricas
    for (sz = [-1, 1]) {
      translate([placa_x[0] - 1, rueda_sep / 2, sz * ruedas_z]) rotate([0, 90, 0]) cylinder(d = 5.3, h = e + 2);
      translate([placa_x[0] - 1, -rueda_sep / 2, sz * ruedas_z]) rotate([0, 90, 0]) cylinder(d = excentrica_d, h = e + 2);
    }
    // M5 al perfil del peine (cabeza en la cara del poste, entre las ruedas)
    for (sy = [-10, 10]) translate([riel_x[1] - 1, sy, -5]) rotate([0, 90, 0]) {
      cylinder(d = m5, h = 20);
      translate([0, 0, placa_x[1] - riel_x[1] - 1.5]) cylinder(d = m5_cabeza + 0.6, h = 5);
    }
    // escuadra del arco (2 x M5 arriba)
    for (sy = [-10, 10]) translate([placa_x[0] - 1, sy, alto / 2 - 8]) rotate([0, 90, 0]) cylinder(d = m5, h = e + 2);
    // M3 para el soporte de la tuerca
    if (prolongacion) for (sy = [husillo_y - 9, husillo_y + 9]) translate([placa_x[0] - 1, sy, 0])
      rotate([0, 90, 0]) cylinder(d = m3, h = e + 2);
  }
}

module soporte_tuerca() {
  // en coordenadas del lado derecho (se usa reflejado en el izquierdo)
  difference() {
    union() {
      translate([placa_x[1], husillo_y - 14, -6]) cube([poste_x - placa_x[1], 28, 12]);
      translate([poste_x, husillo_y, -6]) cylinder(d = tuerca[1] + 8, h = 12);
    }
    translate([poste_x, husillo_y, -7]) cylinder(d = tuerca[0] + 0.6, h = 14);
    for (a = [45 : 90 : 360]) translate([poste_x, husillo_y, -7]) rotate([0, 0, a])
      translate([tuerca[2] / 2, 0, 0]) cylinder(d = m3_rosca, h = 14);
    for (sy = [husillo_y - 9, husillo_y + 9]) translate([placa_x[1] - 1, sy, 0]) rotate([0, 90, 0]) {
      cylinder(d = m3, h = 30);
      translate([0, 0, 6]) hexagono(m3_tuerca, 30);
    }
  }
}

module soporte_motor() {
  // coordenadas: eje del motor en (0, 0); la cara del motor queda en z = h
  e = 5;
  h = 42;
  difference() {
    union() {
      translate([-23, -23, h]) caja_r([46, 46, e], 3);
      translate([-23, 23, 0]) cube([46, e, h + e]);          // pared (lado +s)
      translate([-13, 23, 0]) caja_r([26, 30, 4], 2);        // pie sobre el perfil de la base
      for (sx = [-23, 23 - 4]) hull() {
        translate([sx, 23, 0]) cube([4, 1, h + e]);
        translate([sx, 23 - 15, h]) cube([4, 15, 1]);
      }
    }
    translate([0, 0, h - 1]) cylinder(d = 23, h = e + 2);
    for (sx = [-15.5, 15.5], sy = [-15.5, 15.5]) translate([sx, sy, h - 1]) cylinder(d = m3, h = e + 2);
    for (sy = [36, 47]) translate([0, sy, -0.1]) cylinder(d = m5, h = 5);
  }
}

if (pieza == "placa_der") rotate([0, 90, 0]) translate([-placa_x[1], 0, 0]) placa(false);
else if (pieza == "placa_izq") rotate([0, -90, 0]) translate([placa_x[1], 0, 0]) mirror([1, 0, 0]) placa(true);
else if (pieza == "tuerca") translate([0, 0, 6]) mirror([1, 0, 0]) soporte_tuerca();
else soporte_motor();

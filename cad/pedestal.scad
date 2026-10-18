// =====================================================================
// PEDESTALES de la zona de descarga (sobre los travesaños de la base)
// Material: PETG. 4 perimetros, 40 %. Imprimir como sale el STL.
//   pieza = "riel"    : sostiene el perfil 2020 del riel derecho (cara superior a
//                       PLANO - 4 mm). Imprimir 3 (travesaños s = 270, 400, 540).
//   pieza = "bisagra" : sostiene el eje del volteador (tornillo M5 x 30 que entra
//                       en el tubo de la bisagra) y tiene un tope donde descansa
//                       el volteador cerrado. Imprimir 2 (s = 270 y s = 540).
//   pieza = "calza"   : suplemento de 5 mm para el riel lineal (si hiciera falta).
// Coordenadas: z = 0 cara superior del travesaño.
// =====================================================================
include <lib/comun.scad>

pieza = "riel";  // "riel" | "bisagra" | "calza"

module pedestal_riel() {
  alto = PLANO - 4 - 20;   // = 36: el perfil 2020 apoya encima
  difference() {
    union() {
      translate([-14, -10, 0]) caja_r([28, 20, 4], 2);   // pie
      translate([-10, -10, 0]) cube([20, 20, alto]);    // columna
      // mejillas que abrazan el perfil
      for (sx = [-1, 1]) translate([sx > 0 ? 10 : -14, -10, alto - 12]) cube([4, 20, 22]);
    }
    // perfil 2020 encima
    translate([-10.15, -11, alto]) cube([20.3, 22, 30]);
    // M5 vertical al travesaño (cabeza dentro de la columna, acceso por la ventana)
    translate([0, 0, -0.1]) cylinder(d = m5, h = 20);
    translate([-6, -11, 6]) cube([12, 22, 10]);
    // M5 horizontales a las ranuras laterales del perfil
    for (sx = [-1, 1]) translate([sx * 8, 0, alto + 10]) rotate([0, 90, 0]) cylinder(d = m5, h = 10, center = true);
  }
}

module pedestal_bisagra() {
  eje_z = PLANO - 12;   // = 48: eje del volteador (x = 0 aqui = x -128 de la estacion)
  difference() {
    union() {
      translate([-15, -5, 0]) caja_r([36, 10, 4], 2);
      hull() {
        translate([-8, -5, 0]) cube([16, 10, 1]);
        translate([0, -5, eje_z]) rotate([-90, 0, 0]) cylinder(d = 14, h = 10);
      }
      // repisa de tope: la oreja del volteador cerrado apoya encima (z = PLANO - 8)
      hull() {
        translate([4, -5, 0]) cube([4, 10, 1]);
        translate([6, -5, PLANO - 16]) cube([10, 10, 8]);
      }
    }
    translate([0, -6, eje_z]) rotate([-90, 0, 0]) cylinder(d = m5, h = 12);
    for (sx = [-10, 14]) translate([sx, 0, -0.1]) cylinder(d = m5, h = 5);
  }
}

module calza() {
  difference() {
    caja_rc([20, 40, 5], 2);
    for (sy = [-12, 12]) translate([0, sy, -0.1]) cylinder(d = m5, h = 6);
  }
}

if (pieza == "riel") pedestal_riel();
else if (pieza == "bisagra") pedestal_bisagra();
else calza();

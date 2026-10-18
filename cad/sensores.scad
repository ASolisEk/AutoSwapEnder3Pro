// =====================================================================
// SOPORTES DE SENSORES
// Material: PETG. 4 perimetros, 40 %. Imprimir como sale el STL.
//   pieza = "final_carrera" : microinterruptor KW11-3Z sobre un perfil 2020
//                             (HOME del carro y HOME del ascensor). Imprimir 2.
//   pieza = "inductivo_cama" : sensor inductivo M8 (PLACA_EN_CAMA) sobre el
//                             travesaño del lado de la impresora: detecta el acero
//                             del voladizo de la placa asentada (x = +60, s = 541).
//   pieza = "inductivo_descarga" : sensor inductivo M8 (PLACA_EN_DESCARGA) en la
//                             cara interior del riel derecho (x = 92, s = 400).
// Sensor recomendado: LJ8A3-2-Z/BX de 5 V (NPN, normalmente abierto, alcance 2 mm).
// Se fija con sus dos tuercas M8 a la pestaña: asi se regula la altura (la cara
// del sensor debe quedar 1-1.5 mm por debajo de la placa).
// =====================================================================
include <lib/comun.scad>

pieza = "final_carrera";

module final_carrera() {
  difference() {
    union() {
      caja_rc([20, 34, 4], 3);
      translate([-10, 10, 0]) cube([20, 4, 24]);
    }
    // ranura M5 a la tuerca en T (regulable +-6 mm)
    translate([0, -4, -0.1]) rotate([0, 0, 90]) ranura(12, m5, 5);
    // taladros M2 del interruptor (ranurados en altura)
    for (sx = [-4.75, 4.75]) translate([sx, 9, 15]) rotate([-90, 0, 0])
      hull() for (dz = [-4, 4]) translate([0, dz, 0]) cylinder(d = 2.2, h = 6);
  }
}

// Pestaña con agujero M8 a una altura dada sobre el pie.
module inductivo(alto, voladizo_tab, pie_vertical) {
  difference() {
    union() {
      if (pie_vertical) {
        // pie atornillado a la cara lateral de un perfil (2 x M5)
        translate([-3, -15, 0]) cube([6, 30, alto + 5]);
      } else {
        translate([-15, -10, 0]) caja_r([30, 20, 4], 2);
        translate([-6, -10, 0]) cube([12, 20, alto + 5]);
      }
      // pestaña horizontal
      translate([0, -11, alto]) caja_r([voladizo_tab + 9, 22, 5], 3);
      hull() {
        translate([0, -2, alto - 10]) cube([1, 4, 10]);
        translate([0, -2, alto]) cube([voladizo_tab - 6, 4, 1]);
      }
    }
    translate([voladizo_tab, 0, alto - 1]) cylinder(d = 8.4, h = 7);
    if (pie_vertical) {
      for (sy = [-9, 9]) translate([-4, sy, 6]) rotate([0, 90, 0]) cylinder(d = m5, h = 8);
    } else {
      for (sx = [-11, 11]) translate([sx, 0, -0.1]) cylinder(d = m5, h = 5);
    }
  }
}

// Variante para el travesaño del lado de la impresora: el sensor queda 7 mm por
// delante del eje del travesaño (s = 542), bajo el voladizo de acero de la placa.
module inductivo_cama() {
  alto = 34;
  difference() {
    union() {
      translate([-15, -10, 0]) caja_r([30, 20, 4], 2);
      translate([-8, -10, 0]) cube([16, 7, alto + 5]);
      translate([-11, -10, alto]) caja_r([22, 22, 5], 3);
    }
    translate([0, 7, alto - 1]) cylinder(d = 8.4, h = 7);
    for (sx = [-11, 11]) translate([sx, 0, -0.1]) cylinder(d = m5, h = 5);
  }
}

if (pieza == "final_carrera") final_carrera();
else if (pieza == "inductivo_cama") inductivo_cama();
// Variante para la cara interior del riel derecho: los 2 tornillos M5 van a la
// ranura lateral del perfil (6 mm sobre la base de la pieza); la pestaña queda
// 5 mm por debajo del plano de las placas.
else inductivo(alto = 11, voladizo_tab = 14, pie_vertical = true);

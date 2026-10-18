// =====================================================================
// CAJA DE LA ELECTRONICA - Arduino UNO + CNC Shield V3 + reductor LM2596 + Wagos
// Material: PETG o PLA. 3 perimetros, 20 %.
//   pieza = "caja" | "tapa"
// - Postes para el UNO (taladros oficiales) y para el LM2596 (ranurados).
// - Ventana para el USB-B del UNO, agujero para conector DC de panel (5.5 x 2.1),
//   3 ranuras de salida de cables con pasabridas.
// - Tapa con rejilla sobre los drivers y soporte para ventilador de 40 mm (opcional).
// - 2 orejas con M5 para atornillarla a un perfil 2020.
// =====================================================================
include <lib/comun.scad>

pieza = "caja";

int   = [150, 100, 52];   // interior
pared = 2.4;
suelo = 3;
r     = 4;
uno   = [6, 8];           // esquina del UNO dentro de la caja
uno_taladros = [[13.97, 2.54], [15.24, 50.8], [66.04, 7.62], [66.04, 35.56]];
lm    = [95, 60];         // esquina del LM2596 (43 x 21)
poste_h = 6;

ext = [int[0] + 2 * pared, int[1] + 2 * pared, int[2] + suelo];

module caja() {
  difference() {
    union() {
      caja_r(ext, r);
      // orejas M5
      for (sx = [-12, ext[0]]) translate([sx, ext[1] / 2 - 12, 0]) caja_r([12, 24, 4], 3);
    }
    translate([pared, pared, suelo]) caja_r([int[0], int[1], int[2] + 1], r - 1);
    // USB-B del UNO (lado izquierdo) y conector DC de panel
    translate([-1, pared + uno[1] + 31.7, suelo + poste_h + 1]) cube([pared + 2, 13, 12]);
    translate([-1, pared + 80, suelo + 25]) rotate([0, 90, 0]) cylinder(d = 8, h = pared + 2);
    // ranuras de cables (lado derecho y trasero)
    for (sz = [0, 1, 2]) translate([ext[0] - pared - 1, 15 + sz * 28, suelo + 30]) cube([pared + 2, 20, 9]);
    for (sx = [20, 60, 100]) translate([sx, ext[1] - pared - 1, suelo + 30]) cube([24, pared + 2, 9]);
    // orejas
    for (sx = [-6, ext[0] + 6]) translate([sx, ext[1] / 2, -0.1]) cylinder(d = m5, h = 5);
    // tornillos de la tapa
    for (p = [[r + 2, r + 2], [ext[0] - r - 2, r + 2], [r + 2, ext[1] - r - 2], [ext[0] - r - 2, ext[1] - r - 2]])
      translate([p[0], p[1], ext[2] - 10]) cylinder(d = m3_rosca, h = 11);
    // ventilacion inferior
    for (i = [0 : 6]) translate([40 + i * 10, 20, -1]) cube([4, 40, suelo + 2]);
  }
  // postes del UNO
  for (t = uno_taladros) translate([pared + uno[0] + t[0], pared + uno[1] + t[1], 0]) difference() {
    cylinder(d = 6, h = suelo + poste_h);
    translate([0, 0, 1]) cylinder(d = m3_rosca, h = suelo + poste_h);
  }
  // postes del LM2596 (taladros en esquinas opuestas, ranurados para distintos modelos)
  for (p = [[3, 3], [40, 18]]) translate([pared + lm[0] + p[0], pared + lm[1] + p[1], 0]) difference() {
    cylinder(d = 7, h = suelo + poste_h);
    translate([0, 0, 1]) hull() for (dx = [-1.5, 1.5]) translate([dx, 0, 0]) cylinder(d = m3_rosca, h = suelo + poste_h);
  }
  // esquineros para los tornillos de la tapa
  for (p = [[r + 2, r + 2], [ext[0] - r - 2, r + 2], [r + 2, ext[1] - r - 2], [ext[0] - r - 2, ext[1] - r - 2]])
    translate([p[0], p[1], ext[2] - 12]) difference() {
      cylinder(d = 8, h = 12);
      translate([0, 0, 1]) cylinder(d = m3_rosca, h = 12);
    }
}

module tapa() {
  e = 2.4;
  difference() {
    union() {
      caja_r([ext[0], ext[1], e], r);
      translate([pared + 0.3, pared + 0.3, e]) difference() {
        caja_r([int[0] - 0.6, int[1] - 0.6, 3], r - 1);
        translate([1.6, 1.6, -1]) caja_r([int[0] - 3.8, int[1] - 3.8, 5], r - 2);
      }
    }
    for (p = [[r + 2, r + 2], [ext[0] - r - 2, r + 2], [r + 2, ext[1] - r - 2], [ext[0] - r - 2, ext[1] - r - 2]])
      translate([p[0], p[1], -1]) cylinder(d = m3, h = e + 5);
    // ventilador de 40 mm sobre los drivers (taladros a 32 mm)
    translate([pared + uno[0] + 40, pared + uno[1] + 27, -1]) {
      cylinder(d = 37, h = e + 2);
      for (sx = [-16, 16], sy = [-16, 16]) translate([sx, sy, 0]) cylinder(d = m3, h = e + 2);
    }
    // rejilla
    for (i = [0 : 5]) translate([95 + i * 8, 15, -1]) cube([4, 70, e + 2]);
  }
}

if (pieza == "caja") caja(); else tapa();

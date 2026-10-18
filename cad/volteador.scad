// =====================================================================
// VOLTEADOR - tapa basculante del lado izquierdo de la zona de descarga
// Material: PETG. 3 perimetros, 25 %. Imprimir las 2 mitades + la union.
//   pieza = "mitad1" (s 280-400, lado HOME) | "mitad2" (s 400-520) | "union"
//
// Funcionamiento: la placa usada queda apoyada en el volteador (izquierda) y en
// la tapa del riel derecho. El servo MG996R (volteador_servo.scad) empuja el
// volteador hacia arriba girando sobre su bisagra (x = -128): el borde izquierdo
// de la placa sube, la placa pivota sobre la ceja del riel derecho y resbala a
// la caja. Pega cinta de PTFE en la superficie superior.
// Coordenadas = las de la estacion (x, s, z); eje de la bisagra en x = -128,
// z = PLANO - 12. Superficie superior en z = PLANO.
// =====================================================================
include <lib/comun.scad>

pieza = "mitad1";

eje = [-128, PLANO - 12];
x_int = -25;           // borde interior (canal central libre para el carro)
x_ext = -123;
grueso = 4;
s_ini = 280; s_mitad = 400; s_fin = 520;
pared_guia = [-123, -119.5, 5];   // la placa (x >= -117.5) queda a 2 mm
tubo = [12, 5.3];

module mitad(s0, s1, oreja0, oreja1) {
  largo = s1 - s0;
  difference() {
    union() {
      // superficie
      translate([x_ext, s0, PLANO - grueso]) cube([x_int - x_ext, largo, grueso]);
      // pared guia
      translate([pared_guia[0], s0, PLANO - 0.01]) cube([pared_guia[1] - pared_guia[0], largo, pared_guia[2]]);
      // tubo de la bisagra + alma
      translate([eje[0], s0, eje[1]]) rotate([-90, 0, 0]) cylinder(d = tubo[0], h = largo);
      hull() {
        translate([eje[0], s0, eje[1]]) rotate([-90, 0, 0]) cylinder(d = 8, h = largo);
        translate([eje[0] - 2, s0, PLANO - grueso]) cube([10, largo, grueso]);
      }
      // nervios inferiores (cada 40 mm) y nervio longitudinal
      for (s = [s0 : 40 : s1 - 1]) translate([x_ext + 4, s, PLANO - grueso - 4]) cube([x_int - x_ext - 8, 3, 4]);
      translate([x_ext + 4, s1 - 3, PLANO - grueso - 4]) cube([x_int - x_ext - 8, 3, 4]);
      translate([-100, s0, PLANO - grueso - 4]) cube([3, largo, 4]);
      translate([x_int - 4, s0, PLANO - grueso - 4]) cube([3, largo, 4]);
      // pista de contacto de la palanca del servo (el rodillo rueda aqui)
      translate([-118, s0, PLANO - grueso - 3]) cube([48, largo, 3]);
      // orejas de tope (apoyan en la repisa de los pedestales con el volteador cerrado)
      if (oreja0) translate([-122, s0 - 5, PLANO - 8]) cube([10, 5.01, 4]);
      if (oreja1) translate([-122, s1 - 0.01, PLANO - 8]) cube([10, 5.01, 4]);
    }
    translate([eje[0], s0 - 1, eje[1]]) rotate([-90, 0, 0]) cylinder(d = tubo[1], h = largo + 2);
    // agujeros para la union (M3 autorroscante)
    for (dx = [-85, -60, -35]) translate([dx, s0 == s_ini ? s1 - 10 : s0 + 10, PLANO - grueso - 4.1])
      cylinder(d = m3_rosca, h = grueso + 3);
  }
}

module union_mitades() {
  difference() {
    translate([-92, s_mitad - 18, PLANO - grueso - 7]) caja_r([66, 36, 3], 3);
    for (dx = [-85, -60, -35], ds = [-10, 10]) translate([dx, s_mitad + ds, PLANO - 20]) cylinder(d = m3, h = 30);
  }
}

// Orientacion de impresion: de pie sobre el extremo SIN oreja (tubo y superficie
// verticales, nervios con voladizo de 4 mm). Usa borde de adherencia (brim).
if (pieza == "mitad1") translate([0, 0, s_mitad]) rotate([-90, 0, 0]) translate([128, 0, -PLANO]) mitad(s_ini, s_mitad, true, false);
else if (pieza == "mitad2") translate([0, 0, -s_mitad]) rotate([90, 0, 0]) translate([128, 0, -PLANO]) mitad(s_mitad, s_fin, false, true);
else translate([0, -s_mitad, -(PLANO - grueso - 7)]) union_mitades();

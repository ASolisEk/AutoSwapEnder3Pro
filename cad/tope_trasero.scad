// =====================================================================
// TOPE TRASERO - se pinza al borde trasero de la cama (imprimir 2, se
// colocan a +-70 mm del centro, lejos de la salida del cable de la cama)
// Material: ABS o ASA (la cama llega a 60-100 °C). 4 perimetros, 40 %.
//
// La placa nueva se empuja hasta tocar la CARA DE TOPE: eso fija su
// posicion en Y. La mordaza superior apoya 3 mm sobre la base magnetica y
// sobresale 1.8 mm; un tornillo M3 por debajo aprieta contra el aluminio.
//
// Coordenadas: y = 0 en el borde trasero de la cama, y < 0 hacia el frente,
// z = 0 en la cara inferior del aluminio de la cama.
// =====================================================================
include <lib/comun.scad>

cama_esp   = 3.0;   // espesor del aluminio (mide el tuyo: Anexo A, A9)
base_mag   = 1.0;   // espesor de la base magnetica
adelanto   = 3;     // la mordaza superior entra 3 mm sobre la base magnetica
alto_tope  = 1.8;   // cuanto sobresale la cara de tope sobre la base magnetica
ancho      = 30;
fondo      = 10;    // bloque por detras del borde de la cama
mord_inf   = 9;     // largo de la mordaza inferior bajo la cama
bajo       = 9;     // grueso por debajo de la cama
tornillo_y = -5;

z_mag = cama_esp + base_mag;
z_top = z_mag + alto_tope;

module tope() {
  difference() {
    union() {
      // bloque trasero
      translate([-ancho / 2, 0.3, -bajo]) caja_r([ancho, fondo, bajo + z_top], 2);
      // mordaza superior = cara de tope
      translate([-ancho / 2, -adelanto, z_mag]) cube([ancho, adelanto + 1, alto_tope]);
      // mordaza inferior
      translate([-ancho / 2, -mord_inf, -bajo]) caja_r([ancho, mord_inf + 2, bajo - 0.3], 2);
    }
    // ranura donde entra el canto de la cama (con holgura)
    translate([-ancho / 2 - 1, -mord_inf - 1, -0.3]) cube([ancho + 2, mord_inf + 1.3, z_mag + 0.3]);
    // chaflan en la arista superior de la cara de tope (guia la placa)
    translate([0, -adelanto, z_top]) rotate([45, 0, 0]) cube([ancho + 2, 0.8, 0.8], center = true);
    // tornillo de apriete M3 desde abajo + tuerca
    translate([0, tornillo_y, -bajo - 0.1]) cylinder(d = m3, h = bajo + 0.2);
    translate([0, tornillo_y, -bajo / 2 - m3_tuerca_h / 2]) rotate([0, 0, 30]) hexagono(m3_tuerca, m3_tuerca_h + 0.2);
    translate([-m3_tuerca / 2, tornillo_y - mord_inf, -bajo / 2 - m3_tuerca_h / 2]) cube([m3_tuerca, mord_inf, m3_tuerca_h + 0.2]);
  }
}

// Orientacion de impresion: apoyado sobre la cara trasera (sin soportes)
rotate([-90, 0, 0]) translate([0, -fondo - 0.3, 0]) tope();

// =====================================================================
// SOPORTES DEL EJE LINEAL (motor y polea loca) - lazo de correa lateral
// Material: PETG. 4 perimetros, 30 %. Imprimir como sale el STL.
//   pieza = "motor" : soporte del NEMA 17 (boca abajo, eje hacia abajo) sobre el
//                     travesaño HOME. Agujeros ranurados: deslizando el motor se
//                     tensa la correa.
//   pieza = "polea" : soporte de la polea loca GT2 20T (eje M3 vertical) sobre el
//                     travesaño del lado de la impresora.
// El lazo de correa es horizontal y va a un lado del riel (centro en x = -48),
// a 6-12 mm sobre la base (14-8 mm por debajo de la cara superior del riel).
// Coordenadas locales: origen en el centro de la polea, z = 0 en la cara
// superior del travesaño.
// =====================================================================
include <lib/comun.scad>

pieza = "motor";  // "motor" | "polea"

banda = [6, 12];   // banda de la correa sobre la base
tension = 4;       // recorrido de tension (+-) del motor

module soporte_motor() {
  w = 46;        // ancho de la placa del motor
  h_placa = 16;  // cara inferior de la placa del motor (el motor apoya encima)
  e = 4;
  difference() {
    union() {
      // pie sobre el travesaño (20 mm de ancho en s)
      translate([-w / 2 - 2, -10, 0]) caja_r([w + 4, 20, e], 2);
      // paredes laterales
      for (sx = [-1, 1]) translate([sx > 0 ? w / 2 - e : -w / 2, -w / 2, 0]) cube([e, w, h_placa + e]);
      // placa del motor
      translate([-w / 2, -w / 2, h_placa]) caja_r([w, w, e], 3);
    }
    // paso de la polea y del eje (ranurado para tensar)
    translate([0, 0, h_placa - 1]) hull() for (dy = [-tension, tension]) translate([0, dy, 0]) cylinder(d = 23, h = e + 2);
    // tornillos M3 del motor (31 mm), ranurados en s
    for (sx = [-15.5, 15.5], sy = [-15.5, 15.5]) translate([sx, sy, h_placa - 1])
      hull() for (dy = [-tension, tension]) translate([0, dy, 0]) cylinder(d = m3, h = e + 2);
    // tornillos M5 al travesaño
    for (sx = [-15, 15]) translate([sx, 0, 0]) taladro_m5(e, 0.01);
    // hueco central del pie (la polea baja hasta z = 5)
    translate([-w / 2 + e, -9, -1]) cube([w - 2 * e, 18, e + 2]);
  }
}

module soporte_polea() {
  e = 3.5;
  ancho = 26;
  difference() {
    union() {
      // pie (sobre el travesaño)
      translate([-ancho / 2, -6, 0]) caja_r([ancho, 20, e], 2);
      // pared trasera (lado impresora)
      translate([-ancho / 2, 10, 0]) cube([ancho, e, banda[1] + 6.5]);
      // placa superior en voladizo sobre la polea
      translate([-ancho / 2, -11, banda[1] + 3]) caja_r([ancho, 11 + 10 + e, e], 2);
      // placa inferior bajo la polea
      translate([-ancho / 2, -11, 0]) caja_r([ancho, 17, e], 2);
    }
    // eje M3 de la polea
    translate([0, 0, -1]) cylinder(d = m3, h = 40);
    translate([0, 0, -0.1]) rotate([0, 0, 30]) hexagono(m3_tuerca, m3_tuerca_h + 0.1);
    // tornillos M5 al travesaño (ranurados en x para alinear con el motor)
    for (sx = [-1, 1]) translate([sx * 8, 6, -0.1]) hull() for (dx = [-2, 2]) translate([dx, 0, 0])
      cylinder(d = m5, h = e + 0.2);
  }
}

if (pieza == "motor") soporte_motor();
else soporte_polea();

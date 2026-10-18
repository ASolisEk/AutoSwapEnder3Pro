// =====================================================================
// PIE NIVELADOR LATERAL - en el costado de los largueros (imprimir 6)
// Material: PETG. 4 perimetros, 50 %. Imprimir como sale el STL.
//
// Se atornilla a la ranura LATERAL exterior del perfil 2020 (M5 x 10 + tuerca en
// T) y sostiene una pata niveladora M6 vertical a su lado. Asi la base puede
// quedar desde casi a ras de mesa hasta ~20 mm de altura:
//     altura de la base (h) = A3 + 0.5 - 80 mm
// (A3 = altura de la base magnetica de la cama sobre la mesa, Anexo A).
// Si h sale negativa, pon la impresora sobre una tabla de MDF del grosor que falte.
// =====================================================================
include <lib/comun.scad>

m6_tuerca = 10.2;   // M6: entre caras + holgura
m6_h      = 5.2;
largo     = 40;     // a lo largo del perfil
ala       = 22;     // cuanto sale hacia fuera (la pata M6 va en el centro del ala)

difference() {
  union() {
    // placa que apoya en la cara lateral del perfil (20 mm de alto)
    translate([0, -largo / 2, 0]) cube([5, largo, 20]);
    // ala horizontal arriba, donde rosca la pata
    translate([0, -largo / 2, 12]) caja_r([5 + ala, largo, 8], 3);
    // refuerzos
    for (sy = [-largo / 2, largo / 2 - 4]) hull() {
      translate([0, sy, 0]) cube([5, 4, 20]);
      translate([0, sy, 12]) cube([5 + ala - 3, 4, 8]);
    }
  }
  // M5 a la ranura lateral del perfil (centro a 10 mm de altura)
  translate([-1, 0, 10]) rotate([0, 90, 0]) {
    cylinder(d = m5, h = 8);
    translate([0, 0, 4]) cylinder(d = m5_cabeza + 0.6, h = 30);
  }
  // pata M6 vertical + tuerca atrapada por arriba
  translate([5 + ala / 2 + 1, 0, -1]) cylinder(d = 6.4, h = 30);
  translate([5 + ala / 2 + 1, 0, 20 - m6_h]) rotate([0, 0, 30]) hexagono(m6_tuerca, m6_h + 0.1);
}

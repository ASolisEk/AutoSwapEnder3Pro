// =====================================================================
// TAPA DEL RIEL DERECHO (zona de descarga) - imprimir 2 tramos
// Material: PETG. 3 perimetros, 30 %. Pegar cinta de PTFE en la cara superior.
//
// Va encima del perfil 2020 derecho de la zona de descarga. Su cara superior
// es el plano de transferencia (las placas se deslizan sobre ella). La ceja
// exterior (1.5 mm) guia la placa al cargar y hace de bisagra cuando el
// volteador levanta el lado izquierdo: la placa resbala por encima y cae a la caja.
// Coordenadas locales: x = 0 en el centro del perfil, y a lo largo, z = 0 en la
// cara superior del perfil.
// =====================================================================
include <lib/comun.scad>

largo   = 135;     // dos tramos cubren la zona de descarga (s 265-535)
grueso  = 4;       // = PLANO - cara superior del perfil
dentro  = 12;      // cuanto entra hacia el centro de la estacion desde el perfil
ceja    = [2.5, 1.5];   // ancho y alto de la ceja (la placa queda a 1 mm de ella)
chaflan = [4, 0.8];     // chaflan de entrada en los extremos (largo, caida)
x_ceja  = 8.5;     // la cara interior de la ceja queda en x = 118.5 de la estacion (perfil en x = 110)

module tapa() {
  difference() {
    union() {
      translate([-10 - dentro, 0, 0]) cube([10 + dentro + x_ceja, largo, grueso]);
      // ceja redondeada
      translate([x_ceja, 0, 0]) cube([ceja[0] - ceja[1] / 2, largo, grueso + ceja[1] - ceja[1] / 2]);
      translate([x_ceja + ceja[0] - ceja[1] / 2, 0, grueso]) rotate([-90, 0, 0])
        cylinder(r = ceja[1] / 2 + 0.01, h = largo);
      translate([x_ceja, 0, grueso]) cube([ceja[0] - ceja[1] / 2, largo, ceja[1]]);
      // lengüeta que encaja en la ranura superior del perfil (alinea la tapa)
      translate([-ranura_ancho / 2 + 0.25, 0, -1.5]) cube([ranura_ancho - 0.5, largo, 1.6]);
    }
    // chaflanes de entrada en ambos extremos (la placa nunca tropieza con el canto)
    for (y = [0, largo]) translate([-10 - dentro - 1, y, grueso]) hull() {
      translate([0, -0.01, -chaflan[1]]) cube([10 + dentro + x_ceja + ceja[0] + 2, 0.02, chaflan[1] + 3]);
      translate([0, y == 0 ? chaflan[0] : -chaflan[0], 0]) cube([10 + dentro + x_ceja + ceja[0] + 2, 0.01, 3]);
    }
    // tornillos M5 avellanados a tuercas en T del perfil
    for (y = [20, largo - 20]) translate([0, y, -2]) {
      cylinder(d = m5, h = grueso + 3);
      translate([0, 0, grueso + 2 - 2.8]) cylinder(d1 = m5, d2 = 10.5, h = 2.81);
    }
  }
}

// Orientacion de impresion: de lado (la superficie de deslizamiento queda lisa)
rotate([0, -90, 0]) translate([10 + dentro, 0, 0]) tapa();

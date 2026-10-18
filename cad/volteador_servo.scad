// =====================================================================
// SERVO DEL VOLTEADOR (MG996R) - soporte + palanca con rodillo
// Material: PETG. 5 perimetros, 50 %.
//   pieza = "soporte" : se atornilla al travesaño s = 400 (2 x M5 + tuercas en T).
//                       El servo va de pie (eje a lo largo de s), con el eje en
//                       x = -110, z = PLANO - 28, y la palanca gira en el plano s = 440.
//   pieza = "palanca" : brazo de 35 mm que se atornilla al disco del servo; en la
//                       punta lleva un rodillo (rodamiento 623ZZ + tornillo M3 x 10)
//                       que rueda por la pista inferior del volteador.
// Reposo: la palanca apunta hacia +x (horizontal). Al girar ~90-120 grados sube y
// levanta el volteador (calibrar flap_closed_deg / flap_open_deg en la estacion).
// =====================================================================
include <lib/comun.scad>

pieza = "soporte";

eje = [-110, PLANO - 28];   // (x, z) del eje del servo
s_palanca = 440;           // plano de giro de la palanca
// MG996R
sv_l = 40.7; sv_w = 19.7; sv_h = 37.0;   // largo, ancho, alto de la caja
sv_eje_ext = 10.2;   // eje a 10.2 mm del extremo
sv_oreja = 27.5;     // de la base del servo a la cara superior de las orejas
sv_oreja_e = 2.5;
sv_orejas = [48.5, 10];  // separacion de taladros (a lo largo, a lo ancho)
s_base = s_palanca - 4 - sv_h;   // cara inferior del servo (s)
s_oreja = s_base + sv_oreja - sv_oreja_e;  // las orejas apoyan en la cara +s de la placa
// servo con su largo en vertical: el eje queda a 10.2 mm del extremo superior
z_cuerpo = [eje[1] - (sv_l - sv_eje_ext), eje[1] + sv_eje_ext];
z_centro = (z_cuerpo[0] + z_cuerpo[1]) / 2;

module soporte() {
  placa_x = [-121, -96];
  difference() {
    union() {
      // base sobre el travesaño (s 390-410) que se prolonga hasta la placa de orejas
      translate([placa_x[0], 390, 0]) caja_r([placa_x[1] - placa_x[0], s_oreja - 390, 5], 2);
      // placa de orejas
      translate([placa_x[0], s_oreja - 5, -6]) cube([placa_x[1] - placa_x[0], 5, z_centro + sv_orejas[0] / 2 + 3 + 6]);
      // escuadras
      for (x = [placa_x[0], placa_x[1] - 4]) hull() {
        translate([x, 392, 0]) cube([4, 1, 5]);
        translate([x, s_oreja - 5, 0]) cube([4, 1, z_cuerpo[1]]);
      }
    }
    // ventana del cuerpo
    translate([eje[0] - sv_w / 2 - 0.3, s_oreja - 6, z_cuerpo[0] - 0.3]) cube([sv_w + 0.6, 7, sv_l + 0.6]);
    // taladros de las orejas (M4 o M3 con arandela)
    for (dz = [-sv_orejas[0] / 2, sv_orejas[0] / 2], dx = [-sv_orejas[1] / 2, sv_orejas[1] / 2])
      translate([eje[0] + dx, s_oreja - 6, z_centro + dz]) rotate([-90, 0, 0]) cylinder(d = 3.6, h = 7);
    // M5 al travesaño (centrado en s = 400)
    for (x = [-116, -101]) translate([x, 400, 0]) taladro_m5(5, 0.01);
  }
}

module palanca() {
  largo = 35;
  difference() {
    union() {
      cylinder(d = 26, h = 4);
      hull() {
        cylinder(d = 12, h = 6);
        translate([largo, 0, 0]) cylinder(d = 10, h = 6);
      }
    }
    // centro (tornillo del eje y estria)
    translate([0, 0, -1]) cylinder(d = 7.5, h = 10);
    // ranuras radiales para atornillar al disco del servo (M2 / autorroscantes)
    for (a = [0 : 45 : 359]) rotate([0, 0, a + 22.5]) translate([7, 0, -1]) hull() {
      cylinder(d = 2.2, h = 10);
      translate([4, 0, 0]) cylinder(d = 2.2, h = 10);
    }
    // eje del rodillo 623ZZ (M3) en la punta
    translate([largo, 0, -1]) cylinder(d = m3_rosca, h = 10);
  }
}

// Orientacion de impresion: la cara de las orejas (+s) apoyada en la cama
if (pieza == "soporte") translate([0, 0, s_oreja]) rotate([-90, 0, 0]) soporte();
else palanca();

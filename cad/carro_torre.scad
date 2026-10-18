// =====================================================================
// TORRE DEL GANCHO - va atornillada encima de carro_base (4 x M3 x 12)
// Material: PETG. 4 perimetros, 40 %. Imprimir como sale el STL.
//
// El DEDO (dedo_gancho.scad) sube y baja dentro del canal de la torre. Las
// fuerzas de tirar/empujar la placa las aguantan las paredes del canal, NO los
// engranajes del servo (regla DR5). El servo MG90S mueve el dedo con un
// "yugo escoces": un tornillo M2 x 12 en el brazo del servo entra en la ranura
// horizontal del dedo.
// A la derecha, soporte para el microinterruptor de rodillo GANCHO_ENGANCHADO.
//
// Coordenadas = las de carro_base (z = 0 en la cara superior del riel).
// =====================================================================
include <lib/comun.scad>

base_z    = 6.1;            // cara superior de carro_base
base_h    = 2;
dedo      = [0, 30];
canal     = [7.5, 9.5];     // el dedo mide 7 x 9
pared     = 3;
torre_top = ZP - zapata_bajo - 2;   // = 30: 2 mm por debajo de las zapatas
eje_servo = [-13, 22, base_z + base_h + 6.1];  // cara superior del servo y su eje (y, z)
servo_l   = 22.8; servo_w = 12.2; servo_h = 22.5;
servo_lado_eje = 5.9;       // distancia del eje al extremo del cuerpo
pestanas  = 32.4;           // largo total con pestañas
pestana_e = 2.5;
pestana_z = 3.9;            // distancia de la pestaña a la cara superior
torre_tornillos = [[-30, 6], [-30, 36], [10, 6], [10, 36]];

servo_y0 = eje_servo[1] - (servo_l - servo_lado_eje);  // extremo del cuerpo en -y
servo_cy = servo_y0 + servo_l / 2;

module carro_torre() {
  difference() {
    union() {
      // base
      translate([-38, 0, base_z]) caja_r([52, 40, base_h], 3);
      // torre del dedo
      translate([dedo[0] - canal[0] / 2 - pared, dedo[1] - canal[1] / 2 - pared, base_z])
        caja_r([canal[0] + 2 * pared, canal[1] + 2 * pared, torre_top - base_z], 1.5);
      // pared de la cuna del servo (las pestañas apoyan en su cara -x)
      translate([eje_servo[0] - pestana_z, servo_cy - pestanas / 2 - 1, base_z])
        cube([pestana_z, pestanas + 2, eje_servo[2] + servo_w / 2 + 2 - base_z]);
      // soporte del microinterruptor GANCHO_ENGANCHADO (cara +x)
      translate([11, 4, base_z]) cube([3, 20, 20]);
      // escuadra entre torre y base
      translate([dedo[0] + canal[0] / 2 + pared - 0.5, dedo[1] - 2, base_z]) cube([4, 4, 12]);
    }
    // canal del dedo (atraviesa la base)
    translate([dedo[0] - canal[0] / 2, dedo[1] - canal[1] / 2, base_z - 1]) cube([canal[0], canal[1], 50]);
    // ranura de la pared -x para el pasador del yugo
    translate([dedo[0] - canal[0] / 2 - pared - 1, dedo[1] - 2.2, eje_servo[2] - 5.4])
      cube([pared + 2, 4.4, 10.8]);
    // ventana del cuerpo del servo
    translate([eje_servo[0] - pestana_z - 1, servo_cy - servo_l / 2 - 0.3, base_z + base_h - 0.01])
      cube([pestana_z + 2, servo_l + 0.6, servo_w + 0.4]);
    // tornillos de las pestañas (autorroscantes M2, a lo largo de x)
    for (sy = [-1, 1]) translate([eje_servo[0] - pestana_z - 1, servo_cy + sy * 13.9, eje_servo[2]])
      rotate([0, 90, 0]) cylinder(d = m2_paso, h = pestana_z + 2);
    // tornillos a carro_base (cabeza por arriba)
    for (p = torre_tornillos) translate([p[0], p[1], base_z - 1]) cylinder(d = m3, h = base_h + 2);
    // microinterruptor: 2 ranuras verticales M2 (regulables +-3 mm)
    for (sy = [-4.75, 4.75]) translate([10, 14 + sy, 18]) rotate([0, 90, 0])
      hull() for (dz = [-3, 3]) translate([dz, 0, 0]) cylinder(d = 2.2, h = 5);
  }
}

// Orientacion de impresion: base apoyada en la cama
translate([0, 0, -base_z]) carro_torre();

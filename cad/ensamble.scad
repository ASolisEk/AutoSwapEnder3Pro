// =====================================================================
// ENSAMBLE DE LA ESTACION (solo para visualizar y comprobar interferencias)
// No se imprime. Abre este archivo en OpenSCAD y cambia los parametros:
//   dedo_s  : posicion del dedo del carro (0 = HOME, 530 = cama)
//   u       : descenso del ascensor (5 + 14 * nivel)
//   abrir   : angulo del volteador (0 = cerrado)
// Coordenadas: s a lo largo (0 = HOME), x a lo ancho, z = 0 cara superior de la base.
// =====================================================================
include <lib/comun.scad>
use <zapata.scad>
use <tope_trasero.scad>
use <carro_base.scad>
use <carro_torre.scad>
use <dedo_gancho.scad>
use <riel_tapa.scad>
use <volteador.scad>
use <peine.scad>

dedo_s = 15;      // s_mag
u      = 5;       // nivel 0
abrir  = 0;
placas = 6;
ver_impresora = true;

S_BED = 530; S_DROP = 275; S_MAG = 15;

// perfil 2020 tumbado a lo largo de s (eje en x, z)
module perfil_s(x, z, s0, s1) { translate([x, s0, z]) rotate([-90, 0, 0]) perfil2020(s1 - s0); }
// perfil a lo largo de x
module perfil_x(s, z, x0, x1) { translate([x0, s, z]) rotate([0, 90, 0]) perfil2020(x1 - x0); }
module perfil_z(x, s, z0, z1) { translate([x, s, z0]) perfil2020(z1 - z0); }

// placa PEI con su zapata; borde de la zapata en s = s_borde, sentido +1 hacia la impresora
module placa_con_zapata(s_borde, z, hacia_impresora = true) {
  color("gold") translate([-placa_ancho / 2, hacia_impresora ? s_borde : s_borde - placa_largo, z])
    cube([placa_ancho, placa_largo, placa_esp]);
  color("dimgray") translate([0, s_borde, z])
    if (hacia_impresora) mirror([0, 1, 0]) zapata(); else zapata();
}

// ---------------- base
color("silver") {
  perfil_s(-165, -10, -135, 545);
  perfil_s(165, -10, -135, 545);
  for (s = [-110, 265, 400, 535]) perfil_x(s, -10, -155, 155);
  perfil_s(0, 10, -120, 535);                    // riel lineal
  perfil_s(110, 46, 265, 535);                   // riel derecho de descarga
  for (sx = [-1, 1]) perfil_z(sx * 165, 141, 0, 215);   // postes del ascensor
}

// ---------------- carro
translate([0, dedo_s - 30, RIEL_SUP]) {
  color("orange") carro_base();
  color("seagreen") carro_torre();
  color("red") translate([0, 30, 6.2]) dedo();
}

// ---------------- zona de descarga
color("lightblue") for (s0 = [265, 400]) translate([110, s0, 56]) tapa();
color("steelblue") translate([-128, 0, PLANO - 12]) rotate([0, -abrir, 0]) translate([128, 0, -(PLANO - 12)]) {
  mitad(280, 400, true, false);
  mitad(400, 520, false, true);
}

// ---------------- cargador (ascensor)
z0 = PLANO + 5 - u;   // estante 0
for (lado = [1, -1]) {
  for (s0 = [20, 141]) color("plum") translate([0, s0, z0]) if (lado > 0) peine(); else mirror([1, 0, 0]) peine();
  color("silver") perfil_s(lado * 132, z0 + 86, 20, 262);
}
color("silver") perfil_x(141, z0 + 86 + 32, -148, 148);   // arco
for (k = [0 : placas - 1]) placa_con_zapata(S_MAG + 6, z0 + k * paso_estante, true);

// ---------------- placa en la cama y la cama de la Ender 3 Pro en Y = 235
if (ver_impresora) {
  placa_con_zapata(S_BED + 6, PLANO - 0.5, true);
  color("darkslategray") translate([-117.5, S_BED + 6 + voladizo, PLANO - 0.5 - 4]) cube([235, 235, 4]);
  color("dimgray") for (sx = [-70, 70]) translate([sx, S_BED + 6 + voladizo + 235, PLANO - 0.5 - 4]) rotate([0, 0, 180]) tope();
}

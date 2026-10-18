// =====================================================================
// AutoSwapEnder3Pro - parametros y utilidades comunes de las piezas
// Licencia MIT. Unidades: milimetros.
//
// Sistema de coordenadas de la ESTACION (el mismo en todas las piezas que
// se montan en ella):
//   s : a lo largo de la estacion, 0 = HOME del carro, crece hacia la impresora
//   x : a lo ancho, 0 = eje central (riel lineal), +x = lado de la caja de descarga
//   z : vertical, 0 = cara superior de la base de perfiles 2020 ("b" en la guia)
// El plano de transferencia (superficie por la que se deslizan las placas)
// esta en z = PLANO. Se ajusta a la altura de la cama de la impresora con las
// patas niveladoras, NO cambiando estas piezas.
// =====================================================================

$fn = 48;

// ----------------------------------------------------- placas y cama
placa_ancho  = 235;     // placa PEI
placa_largo  = 235;
placa_esp    = 0.6;     // espesor real de tus placas (mide con calibrador; 0.5 a 0.75)
voladizo     = 11;      // cuanto sobresale la placa (o su lengüeta) por delante de la cama

// ----------------------------------------------------- estacion (alturas sobre la base)
PLANO        = 60;      // plano de transferencia sobre la cara superior de la base
RIEL_SUP     = 20;      // cara superior del riel lineal (2020 apoyado en los travesaños)
ZP           = PLANO - RIEL_SUP;  // = 40: plano de transferencia sobre el riel lineal

// zapata (debe coincidir con zapata.scad)
zapata_bajo  = 8;       // cuanto cuelga la zapata por debajo de la placa
zapata_bolsillo = 6;    // profundidad del bolsillo para el dedo (desde abajo)

// cargador (ascensor)
paso_estante = 14;      // distancia vertical entre placas en el cargador
niveles      = 6;       // placas que caben en el cargador

// ----------------------------------------------------- perfil y tornilleria
perfil      = 20;       // perfil de aluminio 2020
ranura_ancho = 6.2;     // boca de la ranura (serie 20)
holgura     = 0.3;      // holgura general de impresion

m2_paso     = 1.8;   // agujero para autorroscante M2 (servos)
m3          = 3.4;   // paso libre M3
m3_rosca    = 2.7;   // para roscar M3 directamente en plastico
m3_tuerca   = 5.7;   // M3: entre caras + holgura
m3_tuerca_h = 2.6;
m3_cabeza   = 6.2;
m4          = 4.4;
m5          = 5.4;   // paso libre M5
m5_cabeza   = 9.2;
m5_tuerca   = 8.2;   // M5: entre caras + holgura

// ruedas en V estandar (Openbuilds "Solid V Wheel" + rodamientos 625)
rueda_d      = 23.9;
rueda_ancho  = 10.2;
rueda_sep    = 39.26;   // distancia entre centros de ruedas a ambos lados de un 2020
excentrica_d = 7.2;     // alojamiento del espaciador excentrico
espaciador_h = 6;       // espaciador (excentrico o fijo) entre rueda y placa

// ----------------------------------------------------- utilidades

// Caja con aristas verticales redondeadas (r) apoyada en z=0.
module caja_r(size, r = 2) {
  r2 = min(r, size[0] / 2 - 0.01, size[1] / 2 - 0.01);
  hull() for (ix = [r2, size[0] - r2], iy = [r2, size[1] - r2])
    translate([ix, iy, 0]) cylinder(r = r2, h = size[2]);
}

// Igual pero centrada en x e y.
module caja_rc(size, r = 2) { translate([-size[0] / 2, -size[1] / 2, 0]) caja_r(size, r); }

// Prisma hexagonal para tuercas (ec = medida entre caras).
module hexagono(ec, h) { cylinder(d = ec / cos(30), h = h, $fn = 6); }

// Ranura (agujero alargado) a lo largo de x.
module ranura(largo, d, h) {
  hull() for (i = [-largo / 2, largo / 2]) translate([i, 0, 0]) cylinder(d = d, h = h);
}

// Taladro M5 con avellanado para la cabeza (para atornillar a un perfil con tuerca en T).
module taladro_m5(h, cabeza = 4) {
  translate([0, 0, -0.1]) cylinder(d = m5, h = h + 0.2);
  translate([0, 0, h - cabeza]) cylinder(d = m5_cabeza + 0.6, h = cabeza + 0.1);
}

// Taladro M3 pasante con alojamiento de tuerca hexagonal por debajo.
module taladro_m3_tuerca(h, prof_tuerca = m3_tuerca_h + 0.2) {
  translate([0, 0, -0.1]) cylinder(d = m3, h = h + 0.2);
  translate([0, 0, -0.1]) hexagono(m3_tuerca, prof_tuerca + 0.1);
}

// Perfil 2020 de referencia (solo para ensamble y comprobaciones visuales).
module perfil2020(largo) {
  difference() {
    translate([-10, -10, 0]) cube([20, 20, largo]);
    for (a = [0, 90, 180, 270]) rotate([0, 0, a])
      translate([10 - 1.8, -ranura_ancho / 2, -1]) cube([2, ranura_ancho, largo + 2]);
    translate([0, 0, -1]) cylinder(d = 4.2, h = largo + 2);
  }
}

// Microinterruptor KW11-3Z con palanca de rodillo (referencia: 20 x 6.4 x 10 mm,
// taladros M2 a 9.5 mm). Agujeros de montaje, con la cara de montaje en z=0.
module taladros_kw11(h = 10) {
  for (i = [-4.75, 4.75]) translate([i, 0, -0.1]) cylinder(d = 2.2, h = h + 0.2);
}

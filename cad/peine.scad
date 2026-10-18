// =====================================================================
// PEINE DEL CARGADOR - paredes con estantes donde descansan las placas limpias
// Material: PETG. 3 perimetros, 25 %. Imprimir 4: 2 derechos y 2 izquierdos
// (lado = "der" | "izq"); cada lado son 2 tramos de 121 mm.
// Imprimir tumbado sobre la cara exterior (los estantes quedan hacia arriba).
//
// Cada placa apoya sus margenes laterales (8 mm) sobre un estante. Paso vertical
// 14 mm: la zapata (8 mm por debajo y 1.85 por encima de su placa) nunca toca la
// placa de arriba. El ascensor baja el peine de 14 en 14 mm para dejar cada placa
// a la altura del plano de transferencia. Pegar PTFE en los estantes es opcional.
//
// Coordenadas: x de la estacion (lado derecho, x > 0), s local (0..largo),
// z local = 0 en la cara superior del estante 0 (el mas bajo).
// Arriba se atornilla al perfil 2020 longitudinal del ascensor (x 122-142).
// =====================================================================
include <lib/comun.scad>

lado  = "der";
largo = 121;
cara  = 119;          // cara interior de la pared (la placa llega a 117.5)
estante = [10, 2.5];  // vuelo hacia el centro y espesor
pared = 3;
z_perfil = paso_estante * (niveles - 1) + 6;   // cara inferior del perfil del ascensor
alto = z_perfil + 20;

module peine() {
  difference() {
    union() {
      // pared
      translate([cara, 0, -6]) cube([pared, largo, alto + 6]);
      // estantes
      for (k = [0 : niveles - 1]) translate([cara - estante[0], 0, k * paso_estante - estante[1]])
        cube([estante[0] + 0.01, largo, estante[1]]);
      // refuerzos verticales (cada 30 mm) debajo de cada estante
      for (s = [8, largo / 2, largo - 8], k = [0 : niveles - 1])
        translate([cara - 4, s - 1.5, k * paso_estante - estante[1] - 4]) cube([4.01, 3, 4]);
      // zona de atornillado al perfil (engrosada hacia dentro, por encima de todas las placas)
      translate([cara - 4, 0, z_perfil]) cube([pared + 4, largo, 20]);
    }
    // chaflanes de entrada/salida en cada estante (la placa entra y sale sin tropezar)
    for (k = [0 : niveles - 1], s = [0, largo]) translate([cara - estante[0] - 1, s, k * paso_estante])
      rotate([45, 0, 0]) cube([estante[0] + 2, 2.2, 2.2], center = false);
    // tornillos M5 al perfil (cabeza hacia dentro, por encima de todas las placas)
    for (s = [20, largo - 20]) translate([cara - 1, s, z_perfil + 10]) rotate([0, 90, 0]) {
      cylinder(d = m5, h = 20);
      translate([0, 0, -10]) cylinder(d = m5_cabeza + 0.6, h = 10 + 3);
    }
  }
}

module colocado() { if (lado == "der") peine(); else mirror([1, 0, 0]) peine(); }

// Orientacion de impresion: la cara exterior apoyada en la cama
rotate([0, lado == "der" ? 90 : -90, 0]) translate([lado == "der" ? -(cara + pared) : cara + pared, 0, 0]) colocado();

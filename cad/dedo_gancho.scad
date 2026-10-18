// =====================================================================
// DEDO DEL GANCHO - corredera vertical que entra en el bolsillo de la zapata
// Material: PETG (o ASA). 100 % relleno. Imprimir de pie como sale el STL.
//
// Seccion inferior 7 x 9 mm (corre en el canal de carro_torre), punta 6 x 5 mm
// (entra en el bolsillo de 11 x 8 de la zapata). La ranura horizontal recibe el
// tornillo M2 del brazo del servo (yugo escoces): carrera 8 mm con +-30 grados.
// Altura total 22.8 mm: abajo la punta queda 3 mm bajo la zapata; arriba entra 5 mm.
// =====================================================================
include <lib/comun.scad>

inf      = [7, 9, 17];    // seccion inferior (x, y, alto)
punta    = [6, 5, 5.8];   // punta
ranura_z = 4;             // centro de la ranura del yugo sobre la base del dedo
ranura   = [3.2, 4.6, 2.4];  // profundidad (desde la cara -x), largo (y), alto (z)

module dedo() {
  difference() {
    union() {
      translate([-inf[0] / 2, -inf[1] / 2, 0]) cube(inf);
      // punta con chaflan para centrarse en el bolsillo
      hull() {
        translate([-punta[0] / 2, -punta[1] / 2, inf[2] - 0.01]) cube([punta[0], punta[1], punta[2] - 1]);
        translate([-punta[0] / 2 + 0.8, -punta[1] / 2 + 0.8, inf[2]]) cube([punta[0] - 1.6, punta[1] - 1.6, punta[2]]);
      }
    }
    // ranura del yugo (abierta hacia -x)
    translate([-inf[0] / 2 - 0.1, -ranura[1] / 2, ranura_z - ranura[2] / 2]) cube([ranura[0] + 0.1, ranura[1], ranura[2]]);
  }
}

dedo();

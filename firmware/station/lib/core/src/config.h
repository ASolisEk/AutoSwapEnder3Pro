// Parametros configurables de la estacion (CFG LIST / GET / SET / SAVE / DEFAULTS).
// Todos se guardan como float en la EEPROM con un CRC; las mascaras son enteros.
#pragma once

#include "compat.h"

// X(ENUM, "nombre", por_defecto, minimo, maximo)
#define AUTOSWAP_CFG_KEYS(X)                                   \
  X(STEPS_PER_MM, "steps_per_mm", 40, 1, 2000)                 \
  X(LIFT_STEPS_PER_MM, "lift_steps_per_mm", 800, 1, 5000)      \
  X(TRAVEL_MM_S, "travel_mm_s", 80, 5, 200)                    \
  X(PUSH_MM_S, "push_mm_s", 25, 2, 100)                        \
  X(FINAL_MM_S, "final_mm_s", 8, 1, 50)                        \
  X(ACCEL_MM_S2, "accel_mm_s2", 300, 10, 3000)                 \
  X(HOME_MM_S, "home_mm_s", 15, 2, 60)                         \
  X(LIFT_MM_S, "lift_mm_s", 4, 0.5, 15)                        \
  X(LIFT_ACCEL_MM_S2, "lift_accel_mm_s2", 20, 1, 200)          \
  X(LIFT_HOME_MM_S, "lift_home_mm_s", 2, 0.5, 10)              \
  X(S_MAG, "s_mag", 15, 0, 1000)                               \
  X(S_DROP, "s_drop", 275, 0, 1000)                            \
  X(S_BED, "s_bed", 530, 0, 1000)                              \
  X(S_PARK, "s_park", 285, 0, 1000)                            \
  X(S_MAX, "s_max", 545, 10, 1000)                             \
  X(APPROACH_MM, "approach_mm", 20, 1, 100)                    \
  X(SEAT_OVERSHOOT_MM, "seat_overshoot_mm", 1, 0, 10)          \
  X(LIFT_ZERO_MM, "lift_zero_mm", 5, 0, 200)                   \
  X(LIFT_PITCH_MM, "lift_pitch_mm", 14, 5, 50)                 \
  X(SLOTS, "slots", 6, 1, 12)                                  \
  X(LIFT_MAX_MM, "lift_max_mm", 85, 5, 300)                    \
  X(HOOK_UP_DEG, "hook_up_deg", 120, 0, 180)                   \
  X(HOOK_DOWN_DEG, "hook_down_deg", 60, 0, 180)                \
  X(FLAP_CLOSED_DEG, "flap_closed_deg", 30, 0, 180)            \
  X(FLAP_OPEN_DEG, "flap_open_deg", 95, 0, 180)                \
  X(HOOK_MS, "hook_ms", 350, 50, 5000)                         \
  X(FLAP_MS, "flap_ms", 1500, 100, 10000)                      \
  X(SERVO_HOLD_MS, "servo_hold_ms", 800, 100, 10000)           \
  X(STEP_TIMEOUT_S, "step_timeout_s", 30, 2, 300)              \
  X(HOST_TIMEOUT_S, "host_timeout_s", 6, 0, 120)               \
  X(INV_MASK, "inv_mask", 32, 0, 63)                           \
  X(SENSOR_MASK, "sensor_mask", 63, 0, 63)                     \
  X(DIR_MASK, "dir_mask", 0, 0, 3)                             \
  X(IDLE_DISABLE, "idle_disable", 1, 0, 1)                     \
  X(HEARTBEAT_MS, "heartbeat_ms", 1000, 0, 60000)

namespace cfg {

#define AUTOSWAP_CFG_ENUM(id, name, def, lo, hi) id,
enum Key : uint8_t { AUTOSWAP_CFG_KEYS(AUTOSWAP_CFG_ENUM) COUNT };
#undef AUTOSWAP_CFG_ENUM

// Version del formato en EEPROM: cambiala si cambias la lista de claves.
const uint8_t FORMAT_VERSION = 2;

}  // namespace cfg

class Config {
 public:
  float v[cfg::COUNT];

  void defaults();
  // Devuelve false si el valor esta fuera de rango.
  bool set(uint8_t key, float value);
  float get(uint8_t key) const { return v[key]; }
  int32_t geti(uint8_t key) const { return (int32_t)(v[key] + (v[key] >= 0 ? 0.5f : -0.5f)); }
  uint16_t crc() const;

  // Busca una clave por nombre; -1 si no existe.
  static int8_t find(const char* name);
  // Copia el nombre de la clave en out (terminado en '\0').
  static void name(uint8_t key, char* out, uint8_t size);
};

uint16_t crc16(const uint8_t* data, uint16_t len, uint16_t crc = 0xFFFF);

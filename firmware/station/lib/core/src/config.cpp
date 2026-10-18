#include "config.h"

namespace {

#define AUTOSWAP_CFG_NAME(id, name, def, lo, hi) const char NAME_##id[] PROGMEM = name;
AUTOSWAP_CFG_KEYS(AUTOSWAP_CFG_NAME)
#undef AUTOSWAP_CFG_NAME

#define AUTOSWAP_CFG_NAME_PTR(id, name, def, lo, hi) NAME_##id,
const char* const NAMES[] PROGMEM = {AUTOSWAP_CFG_KEYS(AUTOSWAP_CFG_NAME_PTR)};
#undef AUTOSWAP_CFG_NAME_PTR

#define AUTOSWAP_CFG_DEF(id, name, def, lo, hi) (float)(def),
const float DEFAULTS[] PROGMEM = {AUTOSWAP_CFG_KEYS(AUTOSWAP_CFG_DEF)};
#undef AUTOSWAP_CFG_DEF

#define AUTOSWAP_CFG_MIN(id, name, def, lo, hi) (float)(lo),
const float MINS[] PROGMEM = {AUTOSWAP_CFG_KEYS(AUTOSWAP_CFG_MIN)};
#undef AUTOSWAP_CFG_MIN

#define AUTOSWAP_CFG_MAX(id, name, def, lo, hi) (float)(hi),
const float MAXS[] PROGMEM = {AUTOSWAP_CFG_KEYS(AUTOSWAP_CFG_MAX)};
#undef AUTOSWAP_CFG_MAX

}  // namespace

void Config::defaults() {
  for (uint8_t k = 0; k < cfg::COUNT; k++) v[k] = pgm_read_float(&DEFAULTS[k]);
}

bool Config::set(uint8_t key, float value) {
  if (key >= cfg::COUNT) return false;
  if (value != value) return false;  // NaN
  if (value < pgm_read_float(&MINS[key]) || value > pgm_read_float(&MAXS[key])) return false;
  v[key] = value;
  return true;
}

uint16_t Config::crc() const {
  return crc16(reinterpret_cast<const uint8_t*>(v), sizeof(v));
}

int8_t Config::find(const char* name) {
  for (uint8_t k = 0; k < cfg::COUNT; k++) {
    const char* p = (const char*)pgm_read_ptr(&NAMES[k]);
    if (strcmp_P(name, p) == 0) return (int8_t)k;
  }
  return -1;
}

void Config::name(uint8_t key, char* out, uint8_t size) {
  if (size == 0) return;
  out[0] = '\0';
  if (key >= cfg::COUNT) return;
  const char* p = (const char*)pgm_read_ptr(&NAMES[key]);
  strncpy_P(out, p, size - 1);
  out[size - 1] = '\0';
}

uint16_t crc16(const uint8_t* data, uint16_t len, uint16_t crc) {
  // CRC-16/CCITT-FALSE
  for (uint16_t i = 0; i < len; i++) {
    crc ^= (uint16_t)data[i] << 8;
    for (uint8_t b = 0; b < 8; b++) crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
  }
  return crc;
}

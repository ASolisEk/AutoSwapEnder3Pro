// Logica de la Estacion de Cambio Frontal: protocolo serie, secuencias
// HOME / EJECT / LOAD / LIFT y seguridad. No depende de Arduino: todo el acceso
// al hardware pasa por Hal, asi que se prueba en el ordenador ("pio test -e native").
#pragma once

#include "hal.h"

#define AUTOSWAP_FW_VERSION "0.2.0"
#define AUTOSWAP_PROTO 2

namespace err {
enum Code : uint8_t {
  NONE = 0,
  NOT_HOMED,        // E01
  STOP_ACTIVE,      // E02
  TIMEOUT,          // E03
  NO_PLATE_ON_BED,  // E04
  BED_OCCUPIED,     // E05
  MAGAZINE_EMPTY,   // E06
  EJECT_FAIL,       // E07
  DROP_JAM,         // E08
  SEAT_FAIL,        // E09
  BUSY,             // E10
  BAD_ARG,          // E11
  UNKNOWN_CMD,      // E12
  LIMIT,            // E13
  HOST_TIMEOUT,     // E14
  HOME_FAIL,        // E15
  HOOK_MISS,        // E16
  LIFT_HOME_FAIL,   // E17
  HALTED,           // E18
  IN_FAULT,         // E19
  EEPROM,           // E20
  COUNT
};
}  // namespace err

enum class Action : uint8_t { NONE, HOME, EJECT, LOAD, MOVE, LIFT };

// Texto de salida de una linea (sin memoria dinamica: el UNO tiene 2 KB de RAM).
class Line {
 public:
  Line() : n_(0) { buf_[0] = '\0'; }
  Line& s(const char* text);
  Line& p(const char* progmemText);  // cadena en PROGMEM (PSTR)
  Line& c(char ch);
  Line& u(uint32_t value);
  Line& i(int32_t value);
  Line& f(float value, uint8_t decimals = 2);
  Line& code(uint8_t errorCode);  // "E07 EJECT_FAIL"
  const char* str() const { return buf_; }

 private:
  char buf_[160];
  uint8_t n_;
};

class Station {
 public:
  explicit Station(Hal& hal) : hal_(hal) {}

  void begin();
  void onLine(char* line);  // una orden del ordenador, sin '\n'
  void tick();              // llamar en cada vuelta de loop()

  // Consultas (pruebas y main.cpp)
  Action action() const { return action_; }
  bool inFault() const { return fault_ != err::NONE; }
  uint8_t fault() const { return fault_; }
  bool homed() const { return carriageHomed_ && liftHomed_; }
  uint8_t level() const { return level_; }
  bool hookUp() const { return hookUp_; }
  bool flapOpen() const { return flapOpen_; }
  bool sensor(uint8_t id);
  float carriageMm();
  float liftMm();
  Config& config() { return cfg_; }

 private:
  // --- ordenes ---
  void cmdStatus(uint16_t id);
  void cmdCfg(uint16_t id, char** args, uint8_t n);
  void cmdMove(uint16_t id, char** args, uint8_t n, bool absolute);
  void cmdLift(uint16_t id, char** args, uint8_t n);
  bool canStartAction(uint16_t id, bool needHomed);
  void startAction(Action a, uint16_t id);

  // --- secuencias (maquinas de estados sin bloqueo) ---
  void tickHome();
  void tickEject();
  void tickLoad();
  void tickMove();
  void tickLift();
  // Homing generico de un eje; devuelve true cuando termina (o falla).
  bool tickHomeAxis(uint8_t axis, uint8_t base);

  // --- ayudas ---
  bool check(uint8_t sensorId, bool expected);
  bool startCarriage(float mm, float mmPerS, bool limit = true);
  bool startLift(float mm, float mmPerS, bool limit = true);
  bool arrived(uint8_t axis) { return !hal_.moving(axis); }
  void stopAxis(uint8_t axis) { hal_.setPosition(axis, hal_.position(axis)); }
  float levelMm(uint8_t lvl) const;
  void next() { phase_++; phaseStart_ = hal_.now(); phaseLimitMs_ = 0; }
  void waitMs(uint32_t ms) { waitUntil_ = hal_.now() + ms; }
  bool waited() const { return (int32_t)(hal_.now() - waitUntil_) >= 0; }
  void hookUpCmd();
  void hookDownCmd();
  void flapOpenCmd();
  void flapCloseCmd();
  void applyConfig();
  void finish();
  void fail(uint8_t code);
  void reply(uint16_t id, const char* progmemText);
  void replyErr(uint16_t id, uint8_t code);
  void emit(Line& line);
  const char* stateName() const;  // PROGMEM
  const char* actionName() const; // PROGMEM

  Hal& hal_;
  Config cfg_;
  Action action_ = Action::NONE;
  uint8_t phase_ = 0;
  uint8_t liftMode_ = 0;
  uint16_t actionId_ = 0;
  uint32_t phaseStart_ = 0;
  uint32_t phaseLimitMs_ = 0;
  uint32_t waitUntil_ = 0;
  uint32_t lastHost_ = 0;
  uint32_t lastBeat_ = 0;
  uint32_t servoReleaseAt_[hw::SERVO_COUNT] = {0, 0};
  float moveTarget_ = 0;
  float moveSpeed_ = 0;
  uint8_t fault_ = err::NONE;
  uint8_t level_ = 0;
  uint8_t liftTargetLevel_ = 0;
  bool carriageHomed_ = false;
  bool liftHomed_ = false;
  bool hookUp_ = false;
  bool flapOpen_ = false;
  bool hostArmed_ = false;
};

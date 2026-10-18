#include "station.h"

namespace {

// Compara sin distinguir mayusculas un texto en RAM con uno en PROGMEM (PSTR).
bool ieqP(const char* a, const char* progmemB) {
  for (;;) {
    char x = *a++;
    char y = (char)pgm_read_byte(progmemB++);
    if (x >= 'a' && x <= 'z') x = (char)(x - 32);
    if (y >= 'a' && y <= 'z') y = (char)(y - 32);
    if (x != y) return false;
    if (!x) return true;
  }
}

bool parseFloat(const char* text, float& out) {
  if (!text || !*text) return false;
  char* end = nullptr;
  double v = strtod(text, &end);
  if (end == text || *end != '\0') return false;
  out = (float)v;
  return true;
}

bool parseId(const char* text, uint16_t& out) {
  uint32_t v = 0;
  if (!*text) return false;
  for (const char* p = text; *p; p++) {
    if (*p < '0' || *p > '9') return false;
    v = v * 10 + (uint32_t)(*p - '0');
    if (v > 65535UL) return false;
  }
  out = (uint16_t)v;
  return true;
}

float fabsf_(float v) { return v < 0 ? -v : v; }

const char* errName(uint8_t code) {
  switch (code) {
    case err::NONE: return PSTR("NONE");
    case err::NOT_HOMED: return PSTR("NOT_HOMED");
    case err::STOP_ACTIVE: return PSTR("STOP_ACTIVE");
    case err::TIMEOUT: return PSTR("TIMEOUT");
    case err::NO_PLATE_ON_BED: return PSTR("NO_PLATE_ON_BED");
    case err::BED_OCCUPIED: return PSTR("BED_OCCUPIED");
    case err::MAGAZINE_EMPTY: return PSTR("MAGAZINE_EMPTY");
    case err::EJECT_FAIL: return PSTR("EJECT_FAIL");
    case err::DROP_JAM: return PSTR("DROP_JAM");
    case err::SEAT_FAIL: return PSTR("SEAT_FAIL");
    case err::BUSY: return PSTR("BUSY");
    case err::BAD_ARG: return PSTR("BAD_ARG");
    case err::UNKNOWN_CMD: return PSTR("UNKNOWN_CMD");
    case err::LIMIT: return PSTR("LIMIT");
    case err::HOST_TIMEOUT: return PSTR("HOST_TIMEOUT");
    case err::HOME_FAIL: return PSTR("HOME_FAIL");
    case err::HOOK_MISS: return PSTR("HOOK_MISS");
    case err::LIFT_HOME_FAIL: return PSTR("LIFT_HOME_FAIL");
    case err::HALTED: return PSTR("HALTED");
    case err::IN_FAULT: return PSTR("IN_FAULT");
    case err::EEPROM: return PSTR("EEPROM");
    default: return PSTR("UNKNOWN");
  }
}

// Modos de la accion LIFT
const uint8_t LIFT_HOME_MODE = 0;
const uint8_t LIFT_LEVEL_MODE = 1;
const uint8_t LIFT_GOTO_MODE = 2;

}  // namespace

// ---------------------------------------------------------------- Line

Line& Line::c(char ch) {
  if (n_ < sizeof(buf_) - 1) {
    buf_[n_++] = ch;
    buf_[n_] = '\0';
  }
  return *this;
}

Line& Line::s(const char* text) {
  while (*text) c(*text++);
  return *this;
}

Line& Line::p(const char* progmemText) {
  for (;;) {
    char ch = (char)pgm_read_byte(progmemText++);
    if (!ch) break;
    c(ch);
  }
  return *this;
}

Line& Line::u(uint32_t value) {
  char tmp[11];
  uint8_t k = 0;
  do {
    tmp[k++] = (char)('0' + value % 10);
    value /= 10;
  } while (value && k < sizeof(tmp));
  while (k) c(tmp[--k]);
  return *this;
}

Line& Line::i(int32_t value) {
  if (value < 0) {
    c('-');
    return u((uint32_t)(-(value + 1)) + 1);
  }
  return u((uint32_t)value);
}

Line& Line::f(float value, uint8_t decimals) {
  if (value != value) return s("nan");
  if (value < 0) {
    c('-');
    value = -value;
  }
  uint32_t mul = 1;
  for (uint8_t d = 0; d < decimals; d++) mul *= 10;
  uint32_t scaled = (uint32_t)(value * (float)mul + 0.5f);
  u(scaled / mul);
  if (decimals) {
    char tmp[10];
    uint32_t frac = scaled % mul;
    for (int8_t k = (int8_t)decimals - 1; k >= 0; k--) {
      tmp[k] = (char)('0' + frac % 10);
      frac /= 10;
    }
    // quitar ceros sobrantes ("40.000" -> "40", "2.500" -> "2.5")
    int8_t last = (int8_t)decimals - 1;
    while (last >= 0 && tmp[last] == '0') last--;
    if (last >= 0) {
      c('.');
      for (int8_t k = 0; k <= last; k++) c(tmp[k]);
    }
  }
  return *this;
}

Line& Line::code(uint8_t errorCode) {
  c('E');
  c((char)('0' + errorCode / 10));
  c((char)('0' + errorCode % 10));
  c(' ');
  return p(errName(errorCode));
}

// ---------------------------------------------------------------- Station: basicos

void Station::begin() {
  Config stored;
  bool ok = hal_.loadConfig(stored);
  if (ok) {
    Config check;
    check.defaults();
    for (uint8_t k = 0; k < cfg::COUNT && ok; k++) ok = check.set(k, stored.v[k]);
  }
  if (ok) {
    cfg_ = stored;
  } else {
    cfg_.defaults();
  }
  applyConfig();
  hal_.enableDrivers(false);
  hookDownCmd();
  flapCloseCmd();
  lastHost_ = lastBeat_ = hal_.now();
  Line l;
  l.p(PSTR("* READY AUTOSWAP-STATION fw=" AUTOSWAP_FW_VERSION " proto=")).u(AUTOSWAP_PROTO).p(PSTR(" cfg="));
  l.p(ok ? PSTR("eeprom") : PSTR("defaults"));
  emit(l);
}

bool Station::sensor(uint8_t id) {
  bool raw = hal_.rawActive(id);
  bool inv = (cfg_.geti(cfg::INV_MASK) >> id) & 1;
  return raw != inv;
}

bool Station::check(uint8_t sensorId, bool expected) {
  // PLATE_DROP y HOOK_ENGAGED son opcionales: si estan desactivados en sensor_mask no se comprueban.
  if ((sensorId == hw::PLATE_DROP || sensorId == hw::HOOK_ENGAGED) &&
      !((cfg_.geti(cfg::SENSOR_MASK) >> sensorId) & 1)) {
    return true;
  }
  return sensor(sensorId) == expected;
}

float Station::carriageMm() { return (float)hal_.position(hw::CARRIAGE) / cfg_.get(cfg::STEPS_PER_MM); }

float Station::liftMm() { return (float)hal_.position(hw::LIFT) / cfg_.get(cfg::LIFT_STEPS_PER_MM); }

float Station::levelMm(uint8_t lvl) const {
  return cfg_.get(cfg::LIFT_ZERO_MM) + (float)lvl * cfg_.get(cfg::LIFT_PITCH_MM);
}

void Station::applyConfig() {
  int32_t dir = cfg_.geti(cfg::DIR_MASK);
  hal_.setDirInvert(hw::CARRIAGE, dir & 1);
  hal_.setDirInvert(hw::LIFT, (dir >> 1) & 1);
}

void Station::emit(Line& line) {
  hal_.write(line.str());
  hal_.write("\n");
}

void Station::reply(uint16_t id, const char* progmemText) {
  Line l;
  l.u(id).c(' ').p(progmemText);
  emit(l);
}

void Station::replyErr(uint16_t id, uint8_t code) {
  Line l;
  l.u(id).p(PSTR(" ERR ")).code(code);
  emit(l);
}

const char* Station::actionName() const {
  switch (action_) {
    case Action::HOME: return PSTR("HOME");
    case Action::EJECT: return PSTR("EJECT");
    case Action::LOAD: return PSTR("LOAD");
    case Action::MOVE: return PSTR("MOVE");
    case Action::LIFT: return PSTR("LIFT");
    default: return PSTR("NONE");
  }
}

const char* Station::stateName() const {
  switch (action_) {
    case Action::HOME: return PSTR("HOMING");
    case Action::EJECT: return PSTR("EJECTING");
    case Action::LOAD: return PSTR("LOADING");
    case Action::MOVE: return PSTR("MOVING");
    case Action::LIFT: return PSTR("LIFTING");
    default: break;
  }
  if (fault_ != err::NONE) return PSTR("FAULT");
  return homed() ? PSTR("IDLE") : PSTR("UNHOMED");
}

// ---------------------------------------------------------------- actuadores

void Station::hookUpCmd() {
  hal_.servoWrite(hw::SERVO_HOOK, (uint8_t)cfg_.geti(cfg::HOOK_UP_DEG));
  hookUp_ = true;
  servoReleaseAt_[hw::SERVO_HOOK] = 0;  // arriba se mantiene con fuerza
}

void Station::hookDownCmd() {
  hal_.servoWrite(hw::SERVO_HOOK, (uint8_t)cfg_.geti(cfg::HOOK_DOWN_DEG));
  hookUp_ = false;
  servoReleaseAt_[hw::SERVO_HOOK] = hal_.now() + (uint32_t)cfg_.geti(cfg::SERVO_HOLD_MS) + 1;
}

void Station::flapOpenCmd() {
  hal_.servoWrite(hw::SERVO_FLAP, (uint8_t)cfg_.geti(cfg::FLAP_OPEN_DEG));
  flapOpen_ = true;
  servoReleaseAt_[hw::SERVO_FLAP] = 0;
}

void Station::flapCloseCmd() {
  hal_.servoWrite(hw::SERVO_FLAP, (uint8_t)cfg_.geti(cfg::FLAP_CLOSED_DEG));
  flapOpen_ = false;
  servoReleaseAt_[hw::SERVO_FLAP] = hal_.now() + (uint32_t)cfg_.geti(cfg::SERVO_HOLD_MS) + 1;
}

bool Station::startCarriage(float mm, float mmPerS, bool limit) {
  if (limit && (mm < -0.01f || mm > cfg_.get(cfg::S_MAX) + 0.01f)) {
    fail(err::LIMIT);
    return false;
  }
  const float spm = cfg_.get(cfg::STEPS_PER_MM);
  const float from = carriageMm();
  hal_.enableDrivers(true);
  hal_.moveTo(hw::CARRIAGE, (int32_t)(mm * spm + (mm >= 0 ? 0.5f : -0.5f)), mmPerS * spm,
              cfg_.get(cfg::ACCEL_MM_S2) * spm);
  phaseLimitMs_ = (uint32_t)(fabsf_(mm - from) / mmPerS * 1500.0f) + 3000;
  return true;
}

bool Station::startLift(float mm, float mmPerS, bool limit) {
  if (limit && (mm < -0.01f || mm > cfg_.get(cfg::LIFT_MAX_MM) + 0.01f)) {
    fail(err::LIMIT);
    return false;
  }
  const float spm = cfg_.get(cfg::LIFT_STEPS_PER_MM);
  const float from = liftMm();
  hal_.enableDrivers(true);
  hal_.moveTo(hw::LIFT, (int32_t)(mm * spm + (mm >= 0 ? 0.5f : -0.5f)), mmPerS * spm,
              cfg_.get(cfg::LIFT_ACCEL_MM_S2) * spm);
  phaseLimitMs_ = (uint32_t)(fabsf_(mm - from) / mmPerS * 1500.0f) + 3000;
  return true;
}

// ---------------------------------------------------------------- ciclo principal

void Station::tick() {
  const uint32_t now = hal_.now();

  if (sensor(hw::STOP) && fault_ != err::STOP_ACTIVE) fail(err::STOP_ACTIVE);

  for (uint8_t s = 0; s < hw::SERVO_COUNT; s++) {
    if (servoReleaseAt_[s] && (int32_t)(now - servoReleaseAt_[s]) >= 0) {
      hal_.servoRelease(s);
      servoReleaseAt_[s] = 0;
    }
  }

  if (action_ != Action::NONE) {
    const uint32_t hostTimeout = (uint32_t)cfg_.geti(cfg::HOST_TIMEOUT_S) * 1000UL;
    if (hostArmed_ && hostTimeout && now - lastHost_ > hostTimeout) {
      fail(err::HOST_TIMEOUT);
    } else {
      uint32_t limit = (uint32_t)cfg_.geti(cfg::STEP_TIMEOUT_S) * 1000UL;
      if (phaseLimitMs_ > limit) limit = phaseLimitMs_;
      if (now - phaseStart_ > limit) fail(err::TIMEOUT);
    }
  }

  switch (action_) {
    case Action::HOME: tickHome(); break;
    case Action::EJECT: tickEject(); break;
    case Action::LOAD: tickLoad(); break;
    case Action::MOVE: tickMove(); break;
    case Action::LIFT: tickLift(); break;
    default: break;
  }

  const uint32_t beat = (uint32_t)cfg_.geti(cfg::HEARTBEAT_MS);
  if (beat && action_ == Action::NONE && !hal_.moving(hw::CARRIAGE) && !hal_.moving(hw::LIFT) &&
      now - lastBeat_ >= beat) {
    lastBeat_ = now;
    cmdStatus(0xFFFF);  // 0xFFFF = latido espontaneo ("* STATUS ...")
  }
}

void Station::finish() {
  Line l;
  l.u(actionId_).p(PSTR(" DONE ")).p(actionName());
  emit(l);
  action_ = Action::NONE;
  if (cfg_.geti(cfg::IDLE_DISABLE)) hal_.enableDrivers(false);
  lastBeat_ = hal_.now();
}

void Station::fail(uint8_t code) {
  stopAxis(hw::CARRIAGE);
  stopAxis(hw::LIFT);
  hal_.enableDrivers(false);
  // El volteador se suelta siempre (cae sobre su tope). Con STOP se suelta tambien el
  // gancho; en otras fallas el gancho conserva su posicion para no mover la placa.
  hal_.servoRelease(hw::SERVO_FLAP);
  servoReleaseAt_[hw::SERVO_FLAP] = 0;
  flapOpen_ = false;
  if (code == err::STOP_ACTIVE || code == err::HALTED) {
    hal_.servoRelease(hw::SERVO_HOOK);
    servoReleaseAt_[hw::SERVO_HOOK] = 0;
  }
  if (action_ != Action::NONE) replyErr(actionId_, code);
  Line a;
  a.p(PSTR("* FAULT ")).code(code).p(PSTR(" action=")).p(actionName()).p(PSTR(" step=")).u(phase_);
  emit(a);
  fault_ = code;
  action_ = Action::NONE;
}

// ---------------------------------------------------------------- ordenes

void Station::onLine(char* line) {
  lastHost_ = hal_.now();

  char* tok[8];
  uint8_t n = 0;
  char* p = line;
  while (*p && n < 8) {
    while (*p == ' ' || *p == '\t' || *p == '\r') *p++ = '\0';
    if (!*p) break;
    tok[n++] = p;
    while (*p && *p != ' ' && *p != '\t' && *p != '\r') p++;
  }
  if (n == 0) return;

  uint16_t id = 0;
  uint8_t first = 0;
  if (parseId(tok[0], id)) first = 1;  // sin numero de orden: id 0 (uso manual en consola)
  if (first >= n) {
    replyErr(id, err::UNKNOWN_CMD);
    return;
  }
  const char* cmd = tok[first];
  char** args = &tok[first + 1];
  const uint8_t nargs = (uint8_t)(n - first - 1);

  if (ieqP(cmd, PSTR("PING"))) {
    hostArmed_ = true;
    reply(id, PSTR("OK PONG"));
  } else if (ieqP(cmd, PSTR("HELLO"))) {
    Line l;
    l.u(id).p(PSTR(" OK AUTOSWAP-STATION fw=" AUTOSWAP_FW_VERSION " proto=")).u(AUTOSWAP_PROTO);
    emit(l);
  } else if (ieqP(cmd, PSTR("STATUS"))) {
    cmdStatus(id);
  } else if (ieqP(cmd, PSTR("HOME"))) {
    if (canStartAction(id, false)) startAction(Action::HOME, id);
  } else if (ieqP(cmd, PSTR("EJECT"))) {
    if (!canStartAction(id, true)) return;
    if (!sensor(hw::PLATE_BED)) {
      replyErr(id, err::NO_PLATE_ON_BED);
      return;
    }
    startAction(Action::EJECT, id);
  } else if (ieqP(cmd, PSTR("LOAD"))) {
    if (!canStartAction(id, true)) return;
    if (sensor(hw::PLATE_BED)) {
      replyErr(id, err::BED_OCCUPIED);
      return;
    }
    if (level_ >= cfg_.geti(cfg::SLOTS)) {
      replyErr(id, err::MAGAZINE_EMPTY);
      return;
    }
    startAction(Action::LOAD, id);
  } else if (ieqP(cmd, PSTR("MOVE"))) {
    cmdMove(id, args, nargs, false);
  } else if (ieqP(cmd, PSTR("GOTO"))) {
    cmdMove(id, args, nargs, true);
  } else if (ieqP(cmd, PSTR("LIFT"))) {
    cmdLift(id, args, nargs);
  } else if (ieqP(cmd, PSTR("HOOK")) || ieqP(cmd, PSTR("FLAP"))) {
    const bool hook = ieqP(cmd, PSTR("HOOK"));
    if (action_ != Action::NONE) {
      replyErr(id, err::BUSY);
    } else if (sensor(hw::STOP)) {
      replyErr(id, err::STOP_ACTIVE);
    } else if (nargs == 1 && (ieqP(args[0], hook ? PSTR("UP") : PSTR("OPEN")))) {
      if (hook) hookUpCmd(); else flapOpenCmd();
      reply(id, PSTR("OK"));
    } else if (nargs == 1 && (ieqP(args[0], hook ? PSTR("DOWN") : PSTR("CLOSE")))) {
      if (hook) hookDownCmd(); else flapCloseCmd();
      reply(id, PSTR("OK"));
    } else {
      replyErr(id, err::BAD_ARG);
    }
  } else if (ieqP(cmd, PSTR("STOP"))) {
    fail(err::HALTED);
    reply(id, PSTR("OK"));
  } else if (ieqP(cmd, PSTR("RESET"))) {
    if (action_ != Action::NONE) {
      replyErr(id, err::BUSY);
    } else if (sensor(hw::STOP)) {
      replyErr(id, err::STOP_ACTIVE);
    } else {
      fault_ = err::NONE;
      carriageHomed_ = false;
      liftHomed_ = false;
      reply(id, PSTR("OK"));
    }
  } else if (ieqP(cmd, PSTR("CFG"))) {
    cmdCfg(id, args, nargs);
  } else {
    replyErr(id, err::UNKNOWN_CMD);
  }
}

bool Station::canStartAction(uint16_t id, bool needHomed) {
  if (action_ != Action::NONE) {
    replyErr(id, err::BUSY);
  } else if (sensor(hw::STOP)) {
    replyErr(id, err::STOP_ACTIVE);
  } else if (fault_ != err::NONE) {
    replyErr(id, err::IN_FAULT);
  } else if (needHomed && !homed()) {
    replyErr(id, err::NOT_HOMED);
  } else {
    return true;
  }
  return false;
}

void Station::startAction(Action a, uint16_t id) {
  action_ = a;
  actionId_ = id;
  phase_ = 0;
  phaseStart_ = hal_.now();
  phaseLimitMs_ = 0;
  reply(id, PSTR("ACCEPTED"));
}

void Station::cmdStatus(uint16_t id) {
  Line l;
  if (id == 0xFFFF) {
    l.p(PSTR("* STATUS "));
  } else {
    l.u(id).p(PSTR(" OK "));
  }
  l.p(PSTR("state=")).p(stateName());
  l.p(PSTR(" homed=")).u(homed() ? 1 : 0);
  l.p(PSTR(" pos=")).f(carriageMm(), 1);
  l.p(PSTR(" lift=")).f(liftMm(), 2);
  l.p(PSTR(" level=")).u(level_);
  l.p(PSTR(" slots=")).u((uint32_t)cfg_.geti(cfg::SLOTS));
  l.p(PSTR(" bed=")).u(sensor(hw::PLATE_BED));
  l.p(PSTR(" drop=")).u(sensor(hw::PLATE_DROP));
  l.p(PSTR(" eng=")).u(sensor(hw::HOOK_ENGAGED));
  l.p(PSTR(" sw=")).u(sensor(hw::HOME)).u(sensor(hw::LIFT_HOME));
  l.p(PSTR(" hook=")).p(hookUp_ ? PSTR("up") : PSTR("down"));
  l.p(PSTR(" flap=")).p(flapOpen_ ? PSTR("open") : PSTR("closed"));
  l.p(PSTR(" stop=")).u(sensor(hw::STOP));
  l.p(PSTR(" err="));
  if (fault_ == err::NONE) {
    l.p(PSTR("none"));
  } else {
    l.c('E').u(fault_ / 10).u(fault_ % 10);
  }
  emit(l);
}

void Station::cmdCfg(uint16_t id, char** args, uint8_t n) {
  char name[24];
  if (n >= 1 && ieqP(args[0], PSTR("LIST"))) {
    for (uint8_t k = 0; k < cfg::COUNT; k++) {
      Config::name(k, name, sizeof(name));
      Line l;
      l.u(id).p(PSTR(" CFG ")).s(name).c('=').f(cfg_.get(k), 3);
      emit(l);
    }
    Line l;
    l.u(id).p(PSTR(" OK n=")).u(cfg::COUNT);
    emit(l);
    return;
  }
  if (n == 2 && ieqP(args[0], PSTR("GET"))) {
    int8_t k = Config::find(args[1]);
    if (k < 0) {
      replyErr(id, err::BAD_ARG);
      return;
    }
    Line l;
    l.u(id).p(PSTR(" OK ")).s(args[1]).c('=').f(cfg_.get((uint8_t)k), 3);
    emit(l);
    return;
  }
  if (n == 3 && ieqP(args[0], PSTR("SET"))) {
    if (action_ != Action::NONE) {
      replyErr(id, err::BUSY);
      return;
    }
    int8_t k = Config::find(args[1]);
    float value;
    if (k < 0 || !parseFloat(args[2], value) || !cfg_.set((uint8_t)k, value)) {
      replyErr(id, err::BAD_ARG);
      return;
    }
    applyConfig();
    Line l;
    l.u(id).p(PSTR(" OK ")).s(args[1]).c('=').f(cfg_.get((uint8_t)k), 3);
    emit(l);
    return;
  }
  if (n == 1 && ieqP(args[0], PSTR("SAVE"))) {
    if (hal_.saveConfig(cfg_)) {
      reply(id, PSTR("OK"));
    } else {
      replyErr(id, err::EEPROM);
    }
    return;
  }
  if (n == 1 && ieqP(args[0], PSTR("DEFAULTS"))) {
    if (action_ != Action::NONE) {
      replyErr(id, err::BUSY);
      return;
    }
    cfg_.defaults();
    applyConfig();
    reply(id, PSTR("OK"));
    return;
  }
  replyErr(id, err::BAD_ARG);
}

void Station::cmdMove(uint16_t id, char** args, uint8_t n, bool absolute) {
  float mm, speed = cfg_.get(cfg::TRAVEL_MM_S);
  if (n < 1 || n > 2 || !parseFloat(args[0], mm) || (n == 2 && (!parseFloat(args[1], speed) || speed <= 0))) {
    replyErr(id, err::BAD_ARG);
    return;
  }
  if (speed > 200) speed = 200;
  if (!canStartAction(id, false)) return;
  float target;
  if (absolute) {
    if (!carriageHomed_) {
      replyErr(id, err::NOT_HOMED);
      return;
    }
    target = mm;
  } else {
    target = carriageMm() + mm;
    if (!carriageHomed_ && fabsf_(mm) > 20.0f) {  // sin HOME solo pasos cortos
      replyErr(id, err::LIMIT);
      return;
    }
  }
  if (carriageHomed_ && (target < 0 || target > cfg_.get(cfg::S_MAX))) {
    replyErr(id, err::LIMIT);
    return;
  }
  moveTarget_ = target;
  moveSpeed_ = speed;
  startAction(Action::MOVE, id);
}

void Station::cmdLift(uint16_t id, char** args, uint8_t n) {
  if (n < 1) {
    replyErr(id, err::BAD_ARG);
    return;
  }
  if (ieqP(args[0], PSTR("HOME")) && n == 1) {
    if (!canStartAction(id, false)) return;
    liftMode_ = LIFT_HOME_MODE;
    startAction(Action::LIFT, id);
    return;
  }
  const bool next = ieqP(args[0], PSTR("NEXT")) && n == 1;
  const bool level = ieqP(args[0], PSTR("LEVEL")) && n == 2;
  const bool go = ieqP(args[0], PSTR("GOTO")) && (n == 2 || n == 3);
  const bool rel = ieqP(args[0], PSTR("MOVE")) && (n == 2 || n == 3);
  if (!next && !level && !go && !rel) {
    replyErr(id, err::BAD_ARG);
    return;
  }
  float value = 0, speed = cfg_.get(cfg::LIFT_MM_S);
  if ((level || go || rel) && !parseFloat(args[1], value)) {
    replyErr(id, err::BAD_ARG);
    return;
  }
  if ((go || rel) && n == 3 && (!parseFloat(args[2], speed) || speed <= 0)) {
    replyErr(id, err::BAD_ARG);
    return;
  }
  if (speed > 15) speed = 15;
  if (!canStartAction(id, false)) return;

  if (rel && !liftHomed_) {
    if (fabsf_(value) > 5.0f) {
      replyErr(id, err::LIMIT);
      return;
    }
    moveTarget_ = liftMm() + value;
    moveSpeed_ = speed;
    liftMode_ = LIFT_GOTO_MODE;
    startAction(Action::LIFT, id);
    return;
  }
  // El resto exige el ascensor con HOME y el carro con HOME (para apartarlo del cargador).
  if (!liftHomed_ || !carriageHomed_) {
    replyErr(id, err::NOT_HOMED);
    return;
  }
  if (next || level) {
    int32_t target = next ? (int32_t)level_ + 1 : (int32_t)(value + 0.5f);
    if (target < 0 || target >= cfg_.geti(cfg::SLOTS) || levelMm((uint8_t)target) > cfg_.get(cfg::LIFT_MAX_MM)) {
      replyErr(id, err::LIMIT);
      return;
    }
    liftTargetLevel_ = (uint8_t)target;
    moveTarget_ = levelMm(liftTargetLevel_);
    moveSpeed_ = cfg_.get(cfg::LIFT_MM_S);
    liftMode_ = LIFT_LEVEL_MODE;
  } else {
    float target = go ? value : liftMm() + value;
    if (target < 0 || target > cfg_.get(cfg::LIFT_MAX_MM)) {
      replyErr(id, err::LIMIT);
      return;
    }
    moveTarget_ = target;
    moveSpeed_ = speed;
    liftMode_ = LIFT_GOTO_MODE;
  }
  startAction(Action::LIFT, id);
}

// ---------------------------------------------------------------- secuencias

bool Station::tickHomeAxis(uint8_t axis, uint8_t base) {
  const bool lift = axis == hw::LIFT;
  const uint8_t sw = lift ? (uint8_t)hw::LIFT_HOME : (uint8_t)hw::HOME;
  const float speed = lift ? cfg_.get(cfg::LIFT_HOME_MM_S) : cfg_.get(cfg::HOME_MM_S);
  const uint8_t errCode = lift ? (uint8_t)err::LIFT_HOME_FAIL : (uint8_t)err::HOME_FAIL;
  const float span = lift ? cfg_.get(cfg::LIFT_MAX_MM) + 20.0f : cfg_.get(cfg::S_MAX) + 60.0f;
  const float pos = lift ? liftMm() : carriageMm();

  switch (phase_ - base) {
    case 0:  // si ya esta pulsado, apartarse primero
      if (sensor(sw)) {
        next();
        lift ? startLift(pos + 5, speed, false) : startCarriage(pos + 5, speed, false);
      } else {
        phase_ = (uint8_t)(base + 1);
        next();
      }
      break;
    case 1:
      if (arrived(axis)) {
        if (sensor(sw)) {
          fail(errCode);
        } else {
          next();
        }
      }
      break;
    case 2:  // aproximacion rapida hacia el sensor
      next();
      lift ? startLift(pos - span, speed, false) : startCarriage(pos - span, speed, false);
      break;
    case 3:
      if (sensor(sw)) {
        hal_.setPosition(axis, 0);
        next();
        lift ? startLift(3, speed, false) : startCarriage(3, speed, false);
      } else if (arrived(axis)) {
        fail(errCode);
      }
      break;
    case 4:  // retroceso y segunda aproximacion lenta (mas precisa)
      if (arrived(axis)) {
        next();
        lift ? startLift(-6, speed / 4, false) : startCarriage(-6, speed / 4, false);
      }
      break;
    case 5:
      if (sensor(sw)) {
        hal_.setPosition(axis, 0);
        if (lift) liftHomed_ = true; else carriageHomed_ = true;
        return true;
      }
      if (arrived(axis)) fail(errCode);
      break;
  }
  return false;
}

void Station::tickHome() {
  if (phase_ == 0) {
    hookDownCmd();
    flapCloseCmd();
    carriageHomed_ = false;
    liftHomed_ = false;
    waitMs((uint32_t)cfg_.geti(cfg::HOOK_MS));
    next();
  } else if (phase_ == 1) {
    if (waited()) next();
  } else if (phase_ <= 7) {  // 2..7: HOME del carro
    if (tickHomeAxis(hw::CARRIAGE, 2)) {
      next();
      startCarriage(cfg_.get(cfg::S_PARK), cfg_.get(cfg::TRAVEL_MM_S));
    }
  } else if (phase_ == 8) {  // carro aparcado fuera del cargador
    if (arrived(hw::CARRIAGE)) next();
  } else if (phase_ <= 14) {  // 9..14: HOME del ascensor
    if (tickHomeAxis(hw::LIFT, 9)) {
      next();
      startLift(levelMm(level_), cfg_.get(cfg::LIFT_MM_S));
    }
  } else if (phase_ == 15) {
    if (arrived(hw::LIFT)) finish();
  }
}

void Station::tickEject() {
  const float travel = cfg_.get(cfg::TRAVEL_MM_S);
  switch (phase_) {
    case 0:  // gancho abajo y acercarse a la zapata de la placa de la cama
      hookDownCmd();
      flapCloseCmd();
      next();
      startCarriage(cfg_.get(cfg::S_BED) - cfg_.get(cfg::APPROACH_MM), travel);
      break;
    case 1:
      if (arrived(hw::CARRIAGE)) {
        next();
        startCarriage(cfg_.get(cfg::S_BED), cfg_.get(cfg::FINAL_MM_S));
      }
      break;
    case 2:  // subir el dedo dentro de la ranura de la zapata
      if (arrived(hw::CARRIAGE)) {
        hookUpCmd();
        waitMs((uint32_t)cfg_.geti(cfg::HOOK_MS));
        next();
      }
      break;
    case 3:
      if (!waited()) break;
      if (!check(hw::HOOK_ENGAGED, true)) {
        fail(err::HOOK_MISS);
        break;
      }
      next();
      startCarriage(cfg_.get(cfg::S_DROP), cfg_.get(cfg::PUSH_MM_S));  // tirar de la placa
      break;
    case 4:
      if (!arrived(hw::CARRIAGE)) break;
      if (sensor(hw::PLATE_BED) || !check(hw::HOOK_ENGAGED, true) || !check(hw::PLATE_DROP, true)) {
        fail(err::EJECT_FAIL);
        break;
      }
      hookDownCmd();
      waitMs((uint32_t)cfg_.geti(cfg::HOOK_MS));
      next();
      break;
    case 5:  // volteador: levanta el borde izquierdo y la placa resbala a la caja
      if (waited()) {
        flapOpenCmd();
        waitMs((uint32_t)cfg_.geti(cfg::FLAP_MS));
        next();
      }
      break;
    case 6:
      if (waited()) {
        flapCloseCmd();
        waitMs((uint32_t)cfg_.geti(cfg::FLAP_MS) / 2);
        next();
      }
      break;
    case 7:
      if (!waited()) break;
      if (!check(hw::PLATE_DROP, false) || !check(hw::HOOK_ENGAGED, false)) {
        fail(err::DROP_JAM);
        break;
      }
      next();
      startCarriage(cfg_.get(cfg::S_PARK), travel);
      break;
    case 8:
      if (arrived(hw::CARRIAGE)) finish();
      break;
  }
}

void Station::tickLoad() {
  const float travel = cfg_.get(cfg::TRAVEL_MM_S);
  switch (phase_) {
    case 0: {  // apartar el carro del cargador antes de mover el ascensor
      hookDownCmd();
      flapCloseCmd();
      const bool park = carriageMm() < cfg_.get(cfg::S_PARK) - 1.0f;
      next();
      if (park) startCarriage(cfg_.get(cfg::S_PARK), travel);
      break;
    }
    case 1:
      if (arrived(hw::CARRIAGE)) {
        next();
        startLift(levelMm(level_), cfg_.get(cfg::LIFT_MM_S));
      }
      break;
    case 2:
      if (arrived(hw::LIFT)) {
        next();
        startCarriage(cfg_.get(cfg::S_MAG), travel);
      }
      break;
    case 3:  // dedo arriba en la zapata de la placa del nivel actual
      if (arrived(hw::CARRIAGE)) {
        hookUpCmd();
        waitMs((uint32_t)cfg_.geti(cfg::HOOK_MS));
        next();
      }
      break;
    case 4:
      if (!waited()) break;
      if (!check(hw::HOOK_ENGAGED, true)) {
        hookDownCmd();
        fail(err::MAGAZINE_EMPTY);
        break;
      }
      next();
      startCarriage(cfg_.get(cfg::S_BED) - cfg_.get(cfg::APPROACH_MM), cfg_.get(cfg::PUSH_MM_S));
      break;
    case 5:
      if (arrived(hw::CARRIAGE)) {
        next();
        startCarriage(cfg_.get(cfg::S_BED) + cfg_.get(cfg::SEAT_OVERSHOOT_MM), cfg_.get(cfg::FINAL_MM_S));
      }
      break;
    case 6:  // aproximacion lenta hasta la posicion calibrada (placa contra el tope trasero)
      if (!arrived(hw::CARRIAGE)) break;
      if (!sensor(hw::PLATE_BED)) {  // el rodillo de PLACA_EN_CAMA confirma la zapata en su sitio
        fail(err::SEAT_FAIL);
        break;
      }
      hookDownCmd();
      waitMs((uint32_t)cfg_.geti(cfg::HOOK_MS));
      next();
      break;
    case 7:
      if (!waited()) break;
      level_++;
      next();
      startCarriage(cfg_.get(cfg::S_PARK), travel);
      break;
    case 8:  // dejar listo el siguiente nivel mientras la impresora calienta
      if (!arrived(hw::CARRIAGE)) break;
      next();
      if (level_ < cfg_.geti(cfg::SLOTS)) startLift(levelMm(level_), cfg_.get(cfg::LIFT_MM_S));
      break;
    case 9:
      if (!arrived(hw::LIFT)) break;
      if (!sensor(hw::PLATE_BED)) {
        fail(err::SEAT_FAIL);
        break;
      }
      finish();
      break;
  }
}

void Station::tickMove() {
  if (phase_ == 0) {
    next();
    startCarriage(moveTarget_, moveSpeed_, carriageHomed_);
  } else if (arrived(hw::CARRIAGE)) {
    finish();
  }
}

void Station::tickLift() {
  if (liftMode_ == LIFT_HOME_MODE) {
    if (phase_ <= 5) {
      if (tickHomeAxis(hw::LIFT, 0)) {
        next();
        startLift(levelMm(level_), cfg_.get(cfg::LIFT_MM_S));
      }
    } else if (arrived(hw::LIFT)) {
      finish();
    }
    return;
  }
  switch (phase_) {
    case 0: {
      const bool park = carriageHomed_ && carriageMm() < cfg_.get(cfg::S_PARK) - 1.0f;
      next();
      if (park) {
        hookDownCmd();
        startCarriage(cfg_.get(cfg::S_PARK), cfg_.get(cfg::TRAVEL_MM_S));
      }
      break;
    }
    case 1:
      if (arrived(hw::CARRIAGE)) {
        next();
        startLift(moveTarget_, moveSpeed_, liftHomed_);
      }
      break;
    case 2:
      if (arrived(hw::LIFT)) {
        if (liftMode_ == LIFT_LEVEL_MODE) level_ = liftTargetLevel_;
        finish();
      }
      break;
  }
}

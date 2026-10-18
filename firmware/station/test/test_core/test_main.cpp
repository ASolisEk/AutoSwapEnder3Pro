// Pruebas de la logica de la estacion sin hardware: pio test -e native
// FakeHal simula los dos ejes, los servos, los sensores y el recorrido de las placas.
#include <unity.h>

#include <cmath>
#include <string>

#include "station.h"

namespace {

const float DT_MS = 10;

struct FakeAxis {
  float world = 0;  // posicion fisica en pasos
  float target = 0;
  float speed = 0;
  int32_t offset = 0;  // posicion logica = world + offset
};

class FakeHal : public Hal {
 public:
  // --- estado del "mundo" ---
  uint32_t t = 0;
  FakeAxis ax[hw::AXIS_COUNT];
  bool enabled = false;
  int servoDeg[hw::SERVO_COUNT] = {-1, -1};
  bool servoOn[hw::SERVO_COUNT] = {false, false};
  bool stopPressed = false;
  std::string out;
  bool storedValid = false;
  Config stored;

  // Placa en transito o en la cama/descarga (posicion de su zapata en mm de carro)
  bool plate = true;
  float shoe = 530;
  bool engaged = false;
  int magazine[12] = {1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0};
  int dropped = 0;
  // Fallos que se pueden inyectar
  bool failEngage = false;
  bool failDrop = false;
  bool failSeat = false;

  Station* station = nullptr;

  float carriageMm() { return ax[0].world / cfgv(cfg::STEPS_PER_MM); }
  float liftMm() { return ax[1].world / cfgv(cfg::LIFT_STEPS_PER_MM); }
  float cfgv(uint8_t k) { return station->config().get(k); }

  void advance() {
    t += (uint32_t)DT_MS;
    for (uint8_t a = 0; a < hw::AXIS_COUNT; a++) {
      FakeAxis& x = ax[a];
      if (!enabled) continue;
      float d = x.target - x.world;
      float maxStep = x.speed * DT_MS / 1000.0f;
      if (std::fabs(d) <= maxStep) x.world = x.target; else x.world += (d > 0 ? maxStep : -maxStep);
      // topes mecanicos detras de los sensores HOME
      float minWorld = -2.0f * (a == 0 ? cfgv(cfg::STEPS_PER_MM) : cfgv(cfg::LIFT_STEPS_PER_MM));
      if (x.world < minWorld) x.world = minWorld;
    }
    if (engaged && plate) {
      float c = carriageMm();
      float limit = failSeat ? cfgv(cfg::S_BED) - 10 : cfgv(cfg::S_BED);
      shoe = c > limit ? limit : c;
    }
  }

  // --- Hal ---
  uint32_t now() override { return t; }
  bool rawActive(uint8_t s) override {
    switch (s) {
      case hw::HOME: return carriageMm() <= 0.0f;
      case hw::LIFT_HOME: return liftMm() <= 0.0f;
      case hw::PLATE_BED: return plate && shoe >= cfgv(cfg::S_BED) - 0.5f;
      case hw::PLATE_DROP: return plate && std::fabs(shoe - cfgv(cfg::S_DROP)) <= 5.0f;
      case hw::HOOK_ENGAGED: return engaged;
      case hw::STOP: return !stopPressed;  // contacto NC a GND
    }
    return false;
  }
  void moveTo(uint8_t a, int32_t target, float speed, float) override {
    ax[a].target = (float)(target - ax[a].offset);
    ax[a].speed = speed;
  }
  bool moving(uint8_t a) override { return std::fabs(ax[a].target - ax[a].world) > 0.5f; }
  int32_t position(uint8_t a) override { return (int32_t)std::lround(ax[a].world) + ax[a].offset; }
  void setPosition(uint8_t a, int32_t steps) override {
    ax[a].offset = steps - (int32_t)std::lround(ax[a].world);
    ax[a].target = ax[a].world;
  }
  void enableDrivers(bool on) override { enabled = on; }
  void setDirInvert(uint8_t, bool) override {}
  void servoWrite(uint8_t s, uint8_t deg) override {
    servoDeg[s] = deg;
    servoOn[s] = true;
    if (s == hw::SERVO_HOOK) {
      const bool up = deg > 90;
      if (up && !engaged) tryEngage();
      if (!up) engaged = false;
    } else if (deg > 60 && plate && !engaged && !failDrop && std::fabs(shoe - cfgv(cfg::S_DROP)) <= 5.0f) {
      plate = false;  // el volteador tira la placa a la caja
      dropped++;
    }
  }
  void servoRelease(uint8_t s) override { servoOn[s] = false; }
  void write(const char* text) override { out += text; }
  bool loadConfig(Config& c) override {
    if (storedValid) c = stored;
    return storedValid;
  }
  bool saveConfig(const Config& c) override {
    stored = c;
    storedValid = true;
    return true;
  }

  void tryEngage() {
    if (failEngage) return;
    const float c = carriageMm();
    if (plate && std::fabs(c - shoe) < 3.0f) {
      engaged = true;
      return;
    }
    if (!plate && std::fabs(c - cfgv(cfg::S_MAG)) < 3.0f) {
      for (int k = 0; k < 12; k++) {
        const float lvl = cfgv(cfg::LIFT_ZERO_MM) + k * cfgv(cfg::LIFT_PITCH_MM);
        if (std::fabs(liftMm() - lvl) < 0.5f && magazine[k]) {
          magazine[k] = 0;
          plate = true;
          shoe = c;
          engaged = true;
          return;
        }
      }
    }
  }
};

FakeHal* fake;
Station* st;

void send(const char* cmd) {
  char buf[96];
  strncpy(buf, cmd, sizeof(buf) - 1);
  buf[sizeof(buf) - 1] = '\0';
  st->onLine(buf);
}

bool runUntil(const char* token, uint32_t maxMs) {
  const uint32_t end = fake->t + maxMs;
  while (fake->t < end) {
    if (fake->out.find(token) != std::string::npos) return true;
    fake->advance();
    st->tick();
  }
  return fake->out.find(token) != std::string::npos;
}

void run(uint32_t ms) {
  const uint32_t end = fake->t + ms;
  while (fake->t < end) {
    fake->advance();
    st->tick();
  }
}

void homeOk() {
  send("1 HOME");
  TEST_ASSERT_TRUE_MESSAGE(runUntil("1 DONE HOME", 240000), fake->out.c_str());
  fake->out.clear();
}

}  // namespace

void setUp() {
  fake = new FakeHal();
  st = new Station(*fake);
  fake->station = st;
  st->config().defaults();  // FakeHal::cfgv necesita valores antes de begin()
  fake->ax[0].world = 100 * 40;  // carro a 100 mm del HOME
  fake->ax[0].target = fake->ax[0].world;
  fake->ax[1].world = 30 * 800;  // ascensor 30 mm por debajo de su tope
  fake->ax[1].target = fake->ax[1].world;
  st->begin();
}

void tearDown() {
  delete st;
  delete fake;
}

void test_boot_and_hello() {
  TEST_ASSERT_TRUE(fake->out.find("* READY AUTOSWAP-STATION fw=" AUTOSWAP_FW_VERSION " proto=2 cfg=defaults") !=
                   std::string::npos);
  fake->out.clear();
  send("7 HELLO");
  TEST_ASSERT_EQUAL_STRING("7 OK AUTOSWAP-STATION fw=" AUTOSWAP_FW_VERSION " proto=2\n", fake->out.c_str());
  fake->out.clear();
  send("ping");  // sin id y en minusculas (uso manual)
  TEST_ASSERT_EQUAL_STRING("0 OK PONG\n", fake->out.c_str());
}

void test_line_formatting() {
  Line a;
  a.f(40.0f, 3).c(' ').f(2.5f, 3).c(' ').f(-1.25f, 2).c(' ').i(-7).c(' ').code(err::EJECT_FAIL);
  TEST_ASSERT_EQUAL_STRING("40 2.5 -1.25 -7 E07 EJECT_FAIL", a.str());
}

void test_status_fields() {
  fake->out.clear();
  send("3 STATUS");
  const std::string& o = fake->out;
  TEST_ASSERT_TRUE(o.rfind("3 OK state=UNHOMED homed=0", 0) == 0);
  TEST_ASSERT_TRUE(o.find(" bed=1 ") != std::string::npos);
  TEST_ASSERT_TRUE(o.find(" hook=down flap=closed stop=0 err=none") != std::string::npos);
}

void test_cfg_commands() {
  fake->out.clear();
  send("2 CFG SET steps_per_mm 80");
  TEST_ASSERT_EQUAL_STRING("2 OK steps_per_mm=80\n", fake->out.c_str());
  fake->out.clear();
  send("3 CFG SET steps_per_mm 99999");
  TEST_ASSERT_EQUAL_STRING("3 ERR E11 BAD_ARG\n", fake->out.c_str());
  fake->out.clear();
  send("4 CFG GET nope");
  TEST_ASSERT_EQUAL_STRING("4 ERR E11 BAD_ARG\n", fake->out.c_str());
  fake->out.clear();
  send("5 CFG SAVE");
  TEST_ASSERT_EQUAL_STRING("5 OK\n", fake->out.c_str());
  TEST_ASSERT_TRUE(fake->storedValid);
  TEST_ASSERT_EQUAL_FLOAT(80, fake->stored.get(cfg::STEPS_PER_MM));
  fake->out.clear();
  send("6 CFG LIST");
  TEST_ASSERT_TRUE(fake->out.find("6 CFG s_bed=530\n") != std::string::npos);
  TEST_ASSERT_TRUE(fake->out.find("6 OK n=35\n") != std::string::npos);
}

void test_config_from_eeprom_and_corrupt() {
  Config c;
  c.defaults();
  TEST_ASSERT_TRUE(c.set(cfg::S_BED, 512));
  TEST_ASSERT_FALSE(c.set(cfg::S_BED, -5));
  TEST_ASSERT_EQUAL_INT(cfg::S_BED, Config::find("s_bed"));
  TEST_ASSERT_EQUAL_INT(-1, Config::find("s_bedx"));
  fake->stored = c;
  fake->storedValid = true;
  Station s2(*fake);
  fake->out.clear();
  s2.begin();
  TEST_ASSERT_EQUAL_FLOAT(512, s2.config().get(cfg::S_BED));
  TEST_ASSERT_TRUE(fake->out.find("cfg=eeprom") != std::string::npos);
  // Valor fuera de rango en la EEPROM -> valores por defecto
  fake->stored.v[cfg::SLOTS] = 99;
  Station s3(*fake);
  s3.begin();
  TEST_ASSERT_EQUAL_FLOAT(6, s3.config().get(cfg::SLOTS));
}

void test_errors_unknown_busy_not_homed() {
  fake->out.clear();
  send("1 FOO");
  TEST_ASSERT_EQUAL_STRING("1 ERR E12 UNKNOWN_CMD\n", fake->out.c_str());
  fake->out.clear();
  send("2 EJECT");
  TEST_ASSERT_EQUAL_STRING("2 ERR E01 NOT_HOMED\n", fake->out.c_str());
  fake->out.clear();
  send("3 HOME");
  TEST_ASSERT_EQUAL_STRING("3 ACCEPTED\n", fake->out.c_str());
  run(100);
  fake->out.clear();
  send("4 LOAD");
  TEST_ASSERT_EQUAL_STRING("4 ERR E10 BUSY\n", fake->out.c_str());
}

void test_manual_move_limits_without_home() {
  fake->out.clear();
  send("1 MOVE 30");
  TEST_ASSERT_EQUAL_STRING("1 ERR E13 LIMIT\n", fake->out.c_str());
  send("2 MOVE -10 20");
  TEST_ASSERT_TRUE(runUntil("2 DONE MOVE", 5000));
  TEST_ASSERT_FLOAT_WITHIN(0.1, 90, fake->carriageMm());
  send("3 GOTO 50");
  TEST_ASSERT_TRUE(fake->out.find("3 ERR E01 NOT_HOMED") != std::string::npos);
}

void test_home_sequence() {
  homeOk();
  TEST_ASSERT_TRUE(st->homed());
  TEST_ASSERT_FLOAT_WITHIN(0.2, 285, st->carriageMm());  // aparcado en s_park
  TEST_ASSERT_FLOAT_WITHIN(0.05, 5, st->liftMm());       // nivel 0 = lift_zero_mm
  TEST_ASSERT_FALSE(fake->enabled);                      // idle_disable
  send("9 STATUS");
  TEST_ASSERT_TRUE(fake->out.find("9 OK state=IDLE homed=1 pos=285") != std::string::npos);
}

void test_full_swap_cycle() {
  homeOk();
  send("10 EJECT");
  TEST_ASSERT_TRUE_MESSAGE(runUntil("10 DONE EJECT", 120000), fake->out.c_str());
  TEST_ASSERT_EQUAL_INT(1, fake->dropped);
  TEST_ASSERT_FALSE(fake->plate);
  send("11 LOAD");
  TEST_ASSERT_TRUE_MESSAGE(runUntil("11 DONE LOAD", 120000), fake->out.c_str());
  TEST_ASSERT_TRUE(fake->plate);
  TEST_ASSERT_FLOAT_WITHIN(0.6, 530, fake->shoe);
  TEST_ASSERT_EQUAL_INT(0, fake->magazine[0]);
  TEST_ASSERT_EQUAL_INT(1, fake->magazine[1]);
  TEST_ASSERT_EQUAL_INT(1, st->level());
  TEST_ASSERT_FLOAT_WITHIN(0.05, 5 + 14, st->liftMm());  // siguiente nivel ya preparado
  TEST_ASSERT_FALSE(st->hookUp());
  // segundo ciclo con la placa del nivel 1
  send("12 EJECT");
  TEST_ASSERT_TRUE(runUntil("12 DONE EJECT", 120000));
  send("13 LOAD");
  TEST_ASSERT_TRUE(runUntil("13 DONE LOAD", 120000));
  TEST_ASSERT_EQUAL_INT(0, fake->magazine[1]);
  TEST_ASSERT_EQUAL_INT(2, fake->dropped);
}

void test_load_with_empty_slot_reports_magazine_empty() {
  homeOk();
  fake->magazine[0] = 0;
  send("1 EJECT");
  TEST_ASSERT_TRUE(runUntil("1 DONE EJECT", 120000));
  send("2 LOAD");
  TEST_ASSERT_TRUE(runUntil("2 ERR E06 MAGAZINE_EMPTY", 120000));
  TEST_ASSERT_TRUE(st->inFault());
  fake->out.clear();
  send("3 LOAD");
  TEST_ASSERT_EQUAL_STRING("3 ERR E19 IN_FAULT\n", fake->out.c_str());
}

void test_eject_hook_miss() {
  homeOk();
  fake->failEngage = true;
  send("1 EJECT");
  TEST_ASSERT_TRUE(runUntil("1 ERR E16 HOOK_MISS", 120000));
  TEST_ASSERT_TRUE(fake->out.find("* FAULT E16 HOOK_MISS action=EJECT") != std::string::npos);
}

void test_eject_drop_jam() {
  homeOk();
  fake->failDrop = true;
  send("1 EJECT");
  TEST_ASSERT_TRUE(runUntil("1 ERR E08 DROP_JAM", 120000));
  TEST_ASSERT_FALSE(st->flapOpen());
}

void test_load_seat_fail() {
  homeOk();
  send("1 EJECT");
  TEST_ASSERT_TRUE(runUntil("1 DONE EJECT", 120000));
  fake->failSeat = true;
  send("2 LOAD");
  TEST_ASSERT_TRUE(runUntil("2 ERR E09 SEAT_FAIL", 120000));
}

void test_load_refused_when_bed_occupied() {
  homeOk();
  send("1 LOAD");
  TEST_ASSERT_TRUE(fake->out.find("1 ERR E05 BED_OCCUPIED") != std::string::npos);
}

void test_stop_button_and_reset() {
  homeOk();
  send("1 EJECT");
  run(500);
  fake->stopPressed = true;
  run(50);
  TEST_ASSERT_TRUE(fake->out.find("1 ERR E02 STOP_ACTIVE") != std::string::npos);
  TEST_ASSERT_FALSE(fake->enabled);
  fake->out.clear();
  send("2 RESET");
  TEST_ASSERT_EQUAL_STRING("2 ERR E02 STOP_ACTIVE\n", fake->out.c_str());
  fake->stopPressed = false;
  run(50);
  fake->out.clear();
  send("3 RESET");
  TEST_ASSERT_EQUAL_STRING("3 OK\n", fake->out.c_str());
  TEST_ASSERT_FALSE(st->homed());
  TEST_ASSERT_FALSE(st->inFault());
}

void test_stop_command() {
  homeOk();
  send("1 EJECT");
  run(300);
  send("2 STOP");
  TEST_ASSERT_TRUE(fake->out.find("1 ERR E18 HALTED") != std::string::npos);
  TEST_ASSERT_TRUE(fake->out.find("2 OK") != std::string::npos);
  TEST_ASSERT_TRUE(st->inFault());
}

void test_host_watchdog() {
  send("0 PING");  // a partir de aqui el ordenador debe mandar PING durante las acciones
  send("1 HOME");
  TEST_ASSERT_TRUE(runUntil("1 ERR E14 HOST_TIMEOUT", 8000));
}

void test_host_watchdog_fed_by_ping() {
  send("0 PING");
  send("1 HOME");
  for (int i = 0; i < 60 && fake->out.find("1 DONE HOME") == std::string::npos; i++) {
    run(2000);
    send("0 PING");
  }
  TEST_ASSERT_TRUE(fake->out.find("1 DONE HOME") != std::string::npos);
  TEST_ASSERT_TRUE(fake->out.find("E14") == std::string::npos);
}

void test_lift_level_commands() {
  send("1 LIFT LEVEL 2");
  TEST_ASSERT_TRUE(fake->out.find("1 ERR E01 NOT_HOMED") != std::string::npos);
  homeOk();
  send("2 LIFT LEVEL 3");
  TEST_ASSERT_TRUE(runUntil("2 DONE LIFT", 60000));
  TEST_ASSERT_EQUAL_INT(3, st->level());
  TEST_ASSERT_FLOAT_WITHIN(0.05, 5 + 3 * 14, st->liftMm());
  send("3 LIFT NEXT");
  TEST_ASSERT_TRUE(runUntil("3 DONE LIFT", 60000));
  TEST_ASSERT_EQUAL_INT(4, st->level());
  fake->out.clear();
  send("4 LIFT LEVEL 6");  // slots = 6 -> niveles 0..5
  TEST_ASSERT_EQUAL_STRING("4 ERR E13 LIMIT\n", fake->out.c_str());
}

void test_heartbeat_when_idle() {
  fake->out.clear();
  run(2100);
  TEST_ASSERT_TRUE(fake->out.find("* STATUS state=UNHOMED") != std::string::npos);
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_boot_and_hello);
  RUN_TEST(test_line_formatting);
  RUN_TEST(test_status_fields);
  RUN_TEST(test_cfg_commands);
  RUN_TEST(test_config_from_eeprom_and_corrupt);
  RUN_TEST(test_errors_unknown_busy_not_homed);
  RUN_TEST(test_manual_move_limits_without_home);
  RUN_TEST(test_home_sequence);
  RUN_TEST(test_full_swap_cycle);
  RUN_TEST(test_load_with_empty_slot_reports_magazine_empty);
  RUN_TEST(test_eject_hook_miss);
  RUN_TEST(test_eject_drop_jam);
  RUN_TEST(test_load_seat_fail);
  RUN_TEST(test_load_refused_when_bed_occupied);
  RUN_TEST(test_stop_button_and_reset);
  RUN_TEST(test_stop_command);
  RUN_TEST(test_host_watchdog);
  RUN_TEST(test_host_watchdog_fed_by_ping);
  RUN_TEST(test_lift_level_commands);
  RUN_TEST(test_heartbeat_when_idle);
  return UNITY_END();
}

/**
 * AutoSwapEnder3Pro - Firmware de la Estacion de Cambio Frontal (ECF)
 * Arduino UNO R3 + CNC Shield V3. Licencia MIT.
 *
 * Mapa de pines (rotulos de la CNC Shield V3):
 *   Motor del carro (eje lineal)  -> zocalo X : STEP D2, DIR D5
 *   Motor del ascensor (cargador) -> zocalo Y : STEP D3, DIR D6
 *   Habilitacion de drivers       -> EN  D8 (comun a todos los zocalos)
 *   HOME del carro                -> X-  D9
 *   HOME del ascensor             -> Y-  D10
 *   PLACA_EN_CAMA (inductivo M8)  -> Z-  D11  (con diodo 1N4148 en serie)
 *   PLACA_EN_DESCARGA (inductivo) -> Abort  A0  (con diodo 1N4148 en serie)
 *   GANCHO_ENGANCHADO (rodillo)   -> Hold   A1
 *   Boton STOP (contacto NC)      -> Resume A2
 *   Servo del gancho (MG90S)      -> SpnEn  D12
 *   Servo del volteador (MG996R)  -> CoolEn A3
 *   Libre                         -> SpnDir D13 (LED de la placa)
 *
 * Toda la logica esta en lib/core (Station); aqui solo se implementa el acceso
 * al hardware (clase ArduinoHal) y el bucle principal.
 */

#include <Arduino.h>
#include <AccelStepper.h>
#include <EEPROM.h>
#include <Servo.h>
#include <avr/wdt.h>

#include "station.h"

namespace pin {
const uint8_t X_STEP = 2, X_DIR = 5;
const uint8_t Y_STEP = 3, Y_DIR = 6;
const uint8_t ENABLE = 8;  // activo en bajo
const uint8_t SENSORS[hw::SENSOR_COUNT] = {9, 10, 11, A0, A1, A2};
const uint8_t SERVOS[hw::SERVO_COUNT] = {12, A3};
}  // namespace pin

namespace {

const uint16_t EEPROM_MAGIC = 0xA55A;
const uint8_t DEBOUNCE_MS = 20;

class ArduinoHal : public Hal {
 public:
  ArduinoHal()
      : steppers_{AccelStepper(AccelStepper::DRIVER, pin::X_STEP, pin::X_DIR),
                  AccelStepper(AccelStepper::DRIVER, pin::Y_STEP, pin::Y_DIR)} {}

  void begin() {
    pinMode(pin::ENABLE, OUTPUT);
    digitalWrite(pin::ENABLE, HIGH);  // drivers desactivados al arrancar
    for (uint8_t i = 0; i < hw::SENSOR_COUNT; i++) {
      pinMode(pin::SENSORS[i], INPUT_PULLUP);
      stable_[i] = digitalRead(pin::SENSORS[i]) == LOW;
      changedAt_[i] = 0;
    }
    for (uint8_t a = 0; a < hw::AXIS_COUNT; a++) {
      steppers_[a].setMinPulseWidth(3);  // TMC2209 y A4988 aceptan >= 1-2 us
    }
  }

  // Llamar a menudo: genera los pasos y filtra los sensores.
  void service() {
    steppers_[0].run();
    steppers_[1].run();
    const uint32_t t = millis();
    for (uint8_t i = 0; i < hw::SENSOR_COUNT; i++) {
      const bool raw = digitalRead(pin::SENSORS[i]) == LOW;
      if (raw == stable_[i]) {
        changedAt_[i] = t;
      } else if (t - changedAt_[i] >= DEBOUNCE_MS) {
        stable_[i] = raw;
        changedAt_[i] = t;
      }
    }
  }

  uint32_t now() override { return millis(); }
  bool rawActive(uint8_t sensor) override { return stable_[sensor]; }

  void moveTo(uint8_t axis, int32_t target, float speed, float accel) override {
    AccelStepper& s = steppers_[axis];
    s.setMaxSpeed(speed);
    if (accel != lastAccel_[axis]) {  // setAcceleration hace una raiz cuadrada: evitarla si no cambia
      s.setAcceleration(accel);
      lastAccel_[axis] = accel;
    }
    s.moveTo(target);
  }
  bool moving(uint8_t axis) override { return steppers_[axis].distanceToGo() != 0; }
  int32_t position(uint8_t axis) override { return steppers_[axis].currentPosition(); }
  void setPosition(uint8_t axis, int32_t steps) override { steppers_[axis].setCurrentPosition(steps); }
  void enableDrivers(bool on) override { digitalWrite(pin::ENABLE, on ? LOW : HIGH); }
  void setDirInvert(uint8_t axis, bool invert) override { steppers_[axis].setPinsInverted(invert, false, false); }

  void servoWrite(uint8_t servo, uint8_t degrees) override {
    if (!servos_[servo].attached()) servos_[servo].attach(pin::SERVOS[servo], 500, 2400);
    servos_[servo].write(degrees);
  }
  void servoRelease(uint8_t servo) override {
    if (servos_[servo].attached()) servos_[servo].detach();
  }

  void write(const char* text) override { Serial.print(text); }

  // Formato: magic(2) version(1) n(1) valores(4*n) crc(2)
  bool loadConfig(Config& config) override {
    uint16_t magic;
    EEPROM.get(0, magic);
    if (magic != EEPROM_MAGIC || EEPROM.read(2) != cfg::FORMAT_VERSION || EEPROM.read(3) != cfg::COUNT) return false;
    EEPROM.get(4, config.v);
    uint16_t crc;
    EEPROM.get(4 + sizeof(config.v), crc);
    return crc == config.crc();
  }
  bool saveConfig(const Config& config) override {
    wdt_reset();
    EEPROM.put(0, EEPROM_MAGIC);
    EEPROM.update(2, cfg::FORMAT_VERSION);
    EEPROM.update(3, cfg::COUNT);
    for (uint8_t k = 0; k < cfg::COUNT; k++) {  // EEPROM.put de todo el bloque tarda > 0,5 s
      EEPROM.put(4 + k * sizeof(float), config.v[k]);
      wdt_reset();
      service();
    }
    EEPROM.put(4 + sizeof(config.v), config.crc());
    Config check;
    return loadConfig(check) && check.crc() == config.crc();
  }

 private:
  AccelStepper steppers_[hw::AXIS_COUNT];
  float lastAccel_[hw::AXIS_COUNT] = {-1, -1};
  Servo servos_[hw::SERVO_COUNT];
  bool stable_[hw::SENSOR_COUNT];
  uint32_t changedAt_[hw::SENSOR_COUNT];
};

ArduinoHal hal;
Station station(hal);
char lineBuf[96];
uint8_t lineLen = 0;
bool lineOverflow = false;

void readSerial() {
  // Como mucho unos pocos caracteres por vuelta para no retrasar los pasos del motor.
  for (uint8_t budget = 0; budget < 16 && Serial.available(); budget++) {
    const char ch = (char)Serial.read();
    if (ch == '\n' || ch == '\r') {
      if (lineOverflow) {
        Serial.println(F("0 ERR E11 BAD_ARG"));
      } else if (lineLen) {
        lineBuf[lineLen] = '\0';
        station.onLine(lineBuf);
      }
      lineLen = 0;
      lineOverflow = false;
    } else if (lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = ch;
    } else {
      lineOverflow = true;
    }
  }
}

}  // namespace

void setup() {
  MCUSR = 0;
  wdt_disable();
  Serial.begin(115200);
  hal.begin();
  station.begin();
  wdt_enable(WDTO_2S);  // watchdog de hardware: si el programa se cuelga, el UNO se reinicia
}

void loop() {
  wdt_reset();
  hal.service();
  readSerial();
  hal.service();
  station.tick();
}

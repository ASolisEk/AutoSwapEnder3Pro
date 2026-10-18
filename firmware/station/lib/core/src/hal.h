// Interfaz con el hardware. main.cpp la implementa para el Arduino UNO y las
// pruebas "native" la implementan con una estacion simulada.
#pragma once

#include "config.h"

namespace hw {

// Sensores (finales de carrera). El orden coincide con los bits de inv_mask y sensor_mask.
enum Sensor : uint8_t {
  HOME = 0,          // carro en el extremo lejano (HOME)          -> CNC Shield X-  (D9)
  LIFT_HOME = 1,     // ascensor del cargador en su tope superior   -> CNC Shield Y-  (D10)
  PLATE_BED = 2,     // zapata de una placa asentada en la cama      -> CNC Shield Z-  (D11)
  PLATE_DROP = 3,    // placa usada sobre la zona de descarga        -> Abort          (A0)
  HOOK_ENGAGED = 4,  // la zapata empuja la palanca del carro        -> Hold           (A1)
  STOP = 5,          // boton de paro (contacto NC)                  -> Resume         (A2)
  SENSOR_COUNT = 6
};

enum Axis : uint8_t { CARRIAGE = 0, LIFT = 1, AXIS_COUNT = 2 };

enum ServoId : uint8_t { SERVO_HOOK = 0, SERVO_FLAP = 1, SERVO_COUNT = 2 };

}  // namespace hw

class Hal {
 public:
  virtual ~Hal() {}

  virtual uint32_t now() = 0;  // milisegundos desde el arranque

  // Lectura electrica ya filtrada (antirrebote): true = el pin esta a GND.
  // La inversion logica (inv_mask) la aplica Station.
  virtual bool rawActive(uint8_t sensor) = 0;

  // Movimiento en pasos. speed en pasos/s, accel en pasos/s^2.
  virtual void moveTo(uint8_t axis, int32_t target, float speed, float accel) = 0;
  virtual bool moving(uint8_t axis) = 0;
  virtual int32_t position(uint8_t axis) = 0;
  virtual void setPosition(uint8_t axis, int32_t steps) = 0;  // tambien detiene el eje en seco
  virtual void enableDrivers(bool on) = 0;
  virtual void setDirInvert(uint8_t axis, bool invert) = 0;

  virtual void servoWrite(uint8_t servo, uint8_t degrees) = 0;
  virtual void servoRelease(uint8_t servo) = 0;

  // Escribe texto hacia el ordenador (sin salto de linea implicito).
  virtual void write(const char* text) = 0;

  virtual bool loadConfig(Config& config) = 0;
  virtual bool saveConfig(const Config& config) = 0;
};

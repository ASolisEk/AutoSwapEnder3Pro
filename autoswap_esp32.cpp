/**
 * AutoSwapEnder3Pro - Firmware para Microcontrolador ESP32-DevKitC V4
 * Licencia MIT - Copyright (c) 2026 Angel Solis Ek
 *
 * Conexiones en Placa de Bornes con Tornillo (Sin Soldadura):
 * - GPIO 18 : Cable de Senal (Naranja/Amarillo) del Servomotor MG996R
 * - GPIO 19 : Pin NO del Microswitch 1 (Deteccion de cama en Y=0 atras)
 * - GPIO 21 : Pin NO del Microswitch 2 (Deteccion de placas PEI en el cargador)
 * - GND     : Negativo (-) de Fuente 5V 3A, cable Marron del Servo y pines C de Microswitches
 */

#include <Arduino.h>
#include <ESP32Servo.h>

const int PIN_SERVO_SWAP     = 18;
const int PIN_ENDSTOP_Y_BACK = 19;
const int PIN_ENDSTOP_PLATES = 21;

const int ANGLE_IDLE         = 15;  // Angulo en reposo (hilo destensado)
const int ANGLE_EJECT_ENGAGE = 125; // Angulo de traccion (libera placa y activa cunas)

Servo swapServo;

bool hasPlatesAvailable() {
  return digitalRead(PIN_ENDSTOP_PLATES) == LOW;
}

bool isBedAtBack() {
  return digitalRead(PIN_ENDSTOP_Y_BACK) == LOW;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_ENDSTOP_Y_BACK, INPUT_PULLUP);
  pinMode(PIN_ENDSTOP_PLATES, INPUT_PULLUP);

  swapServo.setPeriodHertz(50);
  swapServo.attach(PIN_SERVO_SWAP, 500, 2400);
  swapServo.write(ANGLE_IDLE);

  Serial.println("AUTOSWAP_ESP32_READY");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "STATUS") {
      Serial.print("STATUS:PLATES=");
      Serial.print(hasPlatesAvailable() ? "YES" : "EMPTY");
      Serial.print(",BED_BACK=");
      Serial.println(isBedAtBack() ? "YES" : "NO");
    } else if (cmd == "ENGAGE") {
      if (!hasPlatesAvailable()) {
        Serial.println("ERROR:NO_PLATES_IN_MAGAZINE");
      } else {
        swapServo.write(ANGLE_EJECT_ENGAGE);
        delay(1200);
        Serial.println("OK:LATCH_ENGAGED");
      }
    } else if (cmd == "RELEASE") {
      swapServo.write(ANGLE_IDLE);
      delay(800);
      Serial.println("OK:LATCH_RELEASED");
    } else if (cmd == "TEST_CYCLE") {
      swapServo.write(ANGLE_EJECT_ENGAGE);
      delay(1500);
      swapServo.write(ANGLE_IDLE);
      delay(1000);
      Serial.println("OK:TEST_COMPLETE");
    }
  }
}
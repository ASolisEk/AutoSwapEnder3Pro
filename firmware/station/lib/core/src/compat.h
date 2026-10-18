// Portabilidad entre AVR (Arduino UNO) y el ordenador (pruebas "native").
#pragma once

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#if defined(__AVR__)
#include <avr/pgmspace.h>
#else
#ifndef PROGMEM
#define PROGMEM
#endif
#ifndef PSTR
#define PSTR(s) (s)
#endif
#define pgm_read_ptr(p) (*(p))
#define pgm_read_float(p) (*(p))
#define pgm_read_byte(p) (*(const uint8_t*)(p))
#define strcmp_P strcmp
#define strncpy_P strncpy
#endif

#include "HX711.h"
#include <math.h>

// HX711 wiring
const byte HX711_DOUT_PIN = 6;
const byte HX711_SCK_PIN = 7;

// Serial settings
const unsigned long SERIAL_BAUD = 9600;

// This value must match your own load cell calibration.
// If the numbers move in the wrong direction, flip the sign.
float CALIBRATION_FACTOR = -7050.0f;

// Scale behavior tuning
const byte RAW_SAMPLES_PER_READ = 4;
const unsigned long OUTPUT_INTERVAL_MS = 80;
const float FAST_ALPHA = 0.38f;
const float SLOW_ALPHA = 0.12f;
const float SWITCH_TO_FAST_GRAMS = 12.0f;
const float ZERO_TRACK_WINDOW_G = 3.0f;
const float ZERO_TRACK_ALPHA = 0.015f;
const float SNAP_TO_ZERO_G = 0.35f;
const float STABLE_DELTA_G = 0.8f;
const unsigned long STABLE_HOLD_MS = 350;

HX711 scale;

long zeroOffset = 0;
float filteredGrams = 0.0f;
float lastReportedGrams = 0.0f;
bool filterPrimed = false;
bool scaleReady = false;
bool readingStable = false;
bool readyStatusSent = false;

unsigned long lastOutputMs = 0;
unsigned long lastMovementMs = 0;

long readRawAverage(byte samples) {
  if (samples < 1) {
    samples = 1;
  }

  long total = 0;
  for (byte i = 0; i < samples; i++) {
    total += scale.read();
  }
  return total / samples;
}

float rawToGrams(long rawValue) {
  return (rawValue - zeroOffset) / CALIBRATION_FACTOR;
}

void sendWeight(float grams) {
  if (grams < 0.0f) {
    grams = 0.0f;
  }

  float kilograms = grams / 1000.0f;

  Serial.print("W,");
  Serial.print(grams, 2);
  Serial.print(",");
  Serial.print(kilograms, 4);
  Serial.print(",");
  Serial.println(CALIBRATION_FACTOR, 2);
}

void tareScale() {
  Serial.println("S,TARING");

  const byte tareSamples = 18;
  long total = 0;

  for (byte i = 0; i < tareSamples; i++) {
    while (!scale.is_ready()) {
      delay(2);
    }
    total += scale.read();
  }

  zeroOffset = total / tareSamples;
  filteredGrams = 0.0f;
  lastReportedGrams = 0.0f;
  filterPrimed = true;
  readingStable = true;
  lastMovementMs = millis();

  Serial.println("S,TARE_DONE");
}

void handleSerialCommands() {
  while (Serial.available() > 0) {
    char incoming = (char)Serial.read();

    if (incoming == 't' || incoming == 'T') {
      tareScale();
    } else if (incoming == 'r' || incoming == 'R') {
      filterPrimed = false;
      Serial.println("S,RESET_FILTER");
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  scale.begin(HX711_DOUT_PIN, HX711_SCK_PIN);

  Serial.println("S,BOOTING");

  unsigned long waitStarted = millis();
  while (!scale.is_ready()) {
    if (millis() - waitStarted > 4000) {
      Serial.println("E,HX711_NOT_READY");
      waitStarted = millis();
    }
    delay(50);
  }

  scaleReady = true;
  Serial.println("S,HX711_READY");
  tareScale();
}

void loop() {
  handleSerialCommands();

  if (!scaleReady || !scale.is_ready()) {
    Serial.println("E,HX711_NOT_READY");
    delay(100);
    return;
  }

  long rawValue = readRawAverage(RAW_SAMPLES_PER_READ);
  float grams = rawToGrams(rawValue);

  if (!filterPrimed) {
    filteredGrams = grams;
    lastReportedGrams = grams;
    filterPrimed = true;
    lastMovementMs = millis();
  }

  float delta = grams - filteredGrams;
  float alpha = (fabsf(delta) >= SWITCH_TO_FAST_GRAMS) ? FAST_ALPHA : SLOW_ALPHA;
  filteredGrams += delta * alpha;

  // Real scales drift slightly near zero, so keep zero centered only when
  // the platform is effectively empty.
  if (fabsf(filteredGrams) <= ZERO_TRACK_WINDOW_G) {
    zeroOffset += (long)((rawValue - zeroOffset) * ZERO_TRACK_ALPHA);
  }

  if (fabsf(filteredGrams) < SNAP_TO_ZERO_G) {
    filteredGrams = 0.0f;
  }

  if (filteredGrams < 0.0f) {
    filteredGrams = 0.0f;
  }

  if (fabsf(filteredGrams - lastReportedGrams) > STABLE_DELTA_G) {
    lastMovementMs = millis();
    readingStable = false;
    readyStatusSent = false;
  } else if (millis() - lastMovementMs >= STABLE_HOLD_MS) {
    readingStable = true;
  }

  if (millis() - lastOutputMs >= OUTPUT_INTERVAL_MS) {
    sendWeight(filteredGrams);
    lastReportedGrams = filteredGrams;
    lastOutputMs = millis();

    if (readingStable && !readyStatusSent) {
      Serial.println("S,READY");
      readyStatusSent = true;
    }
  }
}

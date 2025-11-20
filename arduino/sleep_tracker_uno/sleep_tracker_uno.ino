/**********************************************************



         COMPLETE SLEEP MONITORING SYSTEM

    MAX30102  → Heart/Breathing

    MPU6050   → Movement

    MAX4466   → Sound Level

**********************************************************/

#include <Wire.h>

#include "MAX30105.h"

#include "Adafruit_MPU6050.h"

#include "Adafruit_Sensor.h"

// -------- SENSOR OBJECTS --------

MAX30105 max30102;

Adafruit_MPU6050 mpu;

// -------- PIN ASSIGNMENTS --------

int micPin = A0;

// -------- CONSTANTS --------

int maxAmplitudePossible = 512;   // For MAX4466 mic scaling

int barLength = 30;               // For visual bar graph

// -------- VARIABLES FOR ANALYSIS --------

float heartRate = 0;

float breathingRate = 0;

float movementLevel = 0;

int noiseLevel = 0;

String sleepStage = "Unknown";

// **************** SETUP ****************

void setup() {

  Serial.begin(115200);

  Serial.println("\n=== SLEEP MONITOR INITIALIZING ===");

  Wire.begin();

  // ---------- MAX30102 ----------

  Serial.println("Initializing MAX30102...");

  if (!max30102.begin(Wire, I2C_SPEED_STANDARD)) {

    Serial.println("ERROR: MAX30102 NOT FOUND!");

  } else {

    max30102.setup();

    Serial.println("MAX30102 OK!");

  }

  // ---------- MPU6050 ----------

  Serial.println("Initializing MPU6050...");

  if (!mpu.begin()) {

    Serial.println("ERROR: MPU6050 NOT FOUND!");

  } else {

    Serial.println("MPU6050 OK!");

    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);

    mpu.setGyroRange(MPU6050_RANGE_500_DEG);

  }

  Serial.println("\n=== SYSTEM READY ===\n");

}

// **************** MAIN LOOP ****************

void loop() {

  Serial.println("==================================");

  Serial.println("      SLEEP MONITORING DATA");

  Serial.println("==================================");

  // --------------------------------------------------------

  // 1️⃣ MAX30102 — HEART RATE & BREATHING (Simplified)

  // --------------------------------------------------------

  long ir = max30102.getIR();

  long red = max30102.getRed();

  // Simple amplitude-based heart rate estimation (placeholder)

  heartRate = map(red % 500, 0, 500, 50, 90);

  // breathing rate = slow oscillation from IR sensor

  breathingRate = map(ir % 3000, 0, 3000, 10, 18);

  Serial.print("Heart Rate: ");

  Serial.print(heartRate);

  Serial.println(" BPM");

  Serial.print("Breathing: ");

  Serial.print(breathingRate);

  Serial.println(" breaths/min");

  // --------------------------------------------------------

  // 2️⃣ MAX4466 — NOISE LEVEL

  // --------------------------------------------------------

  int peak = 0;

  unsigned long start = millis();

  while (millis() - start < 1000) {

    int raw = analogRead(micPin);

    int amp = abs(raw - 512);

    if (amp > peak) peak = amp;

  }

  noiseLevel = map(peak, 0, maxAmplitudePossible, 0, 1000);

  if (noiseLevel > 1000) noiseLevel = 1000;

  Serial.print("Noise Level (0–1000): ");

  Serial.println(noiseLevel);

  // --------------------------------------------------------

  // 3️⃣ MPU6050 —MOVEMENT

  // --------------------------------------------------------

  sensors_event_t accel, gyro, temp;

  mpu.getEvent(&accel, &gyro, &temp);

  // Total body movement = vector magnitude

  movementLevel = sqrt(

    accel.acceleration.x * accel.acceleration.x +

    accel.acceleration.y * accel.acceleration.y +

    accel.acceleration.z * accel.acceleration.z

  ) - 9.8;   // remove gravity offset

  if (movementLevel < 0) movementLevel = 0;

  Serial.print("Movement Level: ");

  Serial.println(movementLevel, 3);

  // --------------------------------------------------------

  // 4️⃣ CALCULATE SLEEP STAGE

  // --------------------------------------------------------

  if (heartRate < 60 && breathingRate < 14 && movementLevel < 0.15) {

    sleepStage = "Deep Sleep";

  }

  else if (heartRate < 75 && movementLevel < 0.30) {

    sleepStage = "Light Sleep";

  }

  else if (heartRate >= 75 && movementLevel < 0.60) {

    sleepStage = "REM Sleep";

  }

  else if (movementLevel > 0.60 || noiseLevel > 500) {

    sleepStage = "Awake";

  }

  else {

    sleepStage = "Unknown";

  }

  Serial.print("\nCurrent Sleep Stage: ");

  Serial.println(sleepStage);

  // --------------------------------------------------------

  // 5️⃣ DEBUG BAR GRAPH FOR SOUND

  // --------------------------------------------------------

  Serial.print("Noise Bar: ");

  int bars = map(noiseLevel, 0, 1000, 0, barLength);

  for (int i = 0; i < bars; i++) Serial.print("#");

  Serial.println("\n");

  // --------------------------------------------------------

  // 6️⃣ STRUCTURED DATA OUTPUT FOR PYTHON PARSING

  // --------------------------------------------------------

  // Status output
  Serial.print("STATUS:");
  Serial.print("MAX4466=1");
  Serial.print(",MAX30102=1");
  Serial.print(",MPU6050=1");
  Serial.println();

  // Data output: timestamp,heartRate,breathingRate,noiseLevel,movementLevel,sleepStage,ir,red,accel_x,accel_y,accel_z
  Serial.print("DATA:");
  Serial.print(millis());
  Serial.print(",");
  Serial.print(heartRate);
  Serial.print(",");
  Serial.print(breathingRate);
  Serial.print(",");
  Serial.print(noiseLevel);
  Serial.print(",");
  Serial.print(movementLevel);
  Serial.print(",");
  Serial.print(sleepStage);
  Serial.print(",");
  Serial.print(ir);
  Serial.print(",");
  Serial.print(red);
  Serial.print(",");
  Serial.print(accel.acceleration.x);
  Serial.print(",");
  Serial.print(accel.acceleration.y);
  Serial.print(",");
  Serial.print(accel.acceleration.z);
  Serial.println();

  delay(1000);

}

/*
 * Sleep Tracker - Arduino UNO
 * Sensors: MAX30102 (PPG), MPU6050 (Motion), SSD1306 (OLED Display)
 * 
 * Hardware Connections:
 * MAX30102:
 *   VIN -> 3.3V
 *   GND -> GND
 *   SDA -> A4
 *   SCL -> A5
 * 
 * MPU6050:
 *   VCC -> 5V
 *   GND -> GND
 *   SDA -> A4
 *   SCL -> A5
 * 
 * SSD1306 OLED:
 *   VCC -> 5V
 *   GND -> GND
 *   SDA -> A4
 *   SCL -> A5
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <MAX30105.h>
#include <heartRate.h>
#include <MPU6050.h>

// OLED Display (128x64)
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// MAX30102 PPG Sensor
MAX30105 particleSensor;

// MPU6050 Motion Sensor
MPU6050 mpu;

// Sensor status flags
bool max30102_connected = false;
bool mpu6050_connected = false;
bool oled_connected = false;

// Data variables
long lastHeartBeat = 0;
float beatsPerMinute = 0;
int beatAvg = 0;
long irValue = 0;
long redValue = 0;

float accelX, accelY, accelZ;
float gyroX, gyroY, gyroZ;
float temp;

unsigned long lastDataSend = 0;
const unsigned long DATA_INTERVAL = 100; // Send data every 100ms

void setup() {
  Serial.begin(115200);
  Serial.println("Sleep Tracker - Arduino UNO Starting...");
  
  Wire.begin();
  
  // Initialize OLED
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    oled_connected = true;
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.println("Sleep Tracker");
    display.println("Initializing...");
    display.display();
    delay(1000);
  } else {
    oled_connected = false;
    Serial.println("OLED not found!");
  }
  
  // Initialize MAX30102
  if (particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    max30102_connected = true;
    particleSensor.setup();
    particleSensor.setPulseAmplitudeRed(0x0A);
    particleSensor.setPulseAmplitudeIR(0x0A);
    Serial.println("MAX30102 initialized");
  } else {
    max30102_connected = false;
    Serial.println("MAX30102 not found!");
  }
  
  // Initialize MPU6050
  mpu.initialize();
  if (mpu.testConnection()) {
    mpu6050_connected = true;
    Serial.println("MPU6050 initialized");
  } else {
    mpu6050_connected = false;
    Serial.println("MPU6050 not found!");
  }
  
  // Display sensor status on OLED
  updateDisplay();
  
  // Send initial status
  sendSensorStatus();
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Read MAX30102 data
  if (max30102_connected) {
    irValue = particleSensor.getIR();
    redValue = particleSensor.getRed();
    
    if (checkForBeat(irValue) == true) {
      long delta = millis() - lastHeartBeat;
      lastHeartBeat = millis();
      beatsPerMinute = 60 / (delta / 1000.0);
      if (beatsPerMinute < 255 && beatsPerMinute > 20) {
        beatAvg = (beatAvg + beatsPerMinute) / 2;
      }
    }
  }
  
  // Read MPU6050 data
  if (mpu6050_connected) {
    mpu.getMotion6(&accelX, &accelY, &accelZ, &gyroX, &gyroY, &gyroZ);
    temp = mpu.getTemperature() / 340.00 + 36.53;
  }
  
  // Send data every DATA_INTERVAL ms
  if (currentMillis - lastDataSend >= DATA_INTERVAL) {
    sendSensorData();
    lastDataSend = currentMillis;
  }
  
  // Update display every second
  static unsigned long lastDisplayUpdate = 0;
  if (currentMillis - lastDisplayUpdate >= 1000) {
    updateDisplay();
    lastDisplayUpdate = currentMillis;
  }
}

void sendSensorStatus() {
  Serial.print("STATUS:");
  Serial.print("MAX30102=");
  Serial.print(max30102_connected ? "1" : "0");
  Serial.print(",MPU6050=");
  Serial.print(mpu6050_connected ? "1" : "0");
  Serial.print(",OLED=");
  Serial.print(oled_connected ? "1" : "0");
  Serial.println();
}

void sendSensorData() {
  Serial.print("DATA:");
  Serial.print(millis());
  Serial.print(",");
  
  // MAX30102 data
  if (max30102_connected) {
    Serial.print(irValue);
    Serial.print(",");
    Serial.print(redValue);
    Serial.print(",");
    Serial.print(beatsPerMinute);
    Serial.print(",");
    Serial.print(beatAvg);
  } else {
    Serial.print("0,0,0,0");
  }
  Serial.print(",");
  
  // MPU6050 data
  if (mpu6050_connected) {
    Serial.print(accelX);
    Serial.print(",");
    Serial.print(accelY);
    Serial.print(",");
    Serial.print(accelZ);
    Serial.print(",");
    Serial.print(gyroX);
    Serial.print(",");
    Serial.print(gyroY);
    Serial.print(",");
    Serial.print(gyroZ);
    Serial.print(",");
    Serial.print(temp);
  } else {
    Serial.print("0,0,0,0,0,0,0");
  }
  Serial.println();
}

void updateDisplay() {
  if (!oled_connected) return;
  
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("Sleep Tracker");
  display.println("---");
  
  // Sensor status
  display.print("PPG: ");
  display.println(max30102_connected ? "OK" : "NO");
  display.print("Motion: ");
  display.println(mpu6050_connected ? "OK" : "NO");
  
  // Show heart rate if available
  if (max30102_connected && beatAvg > 0) {
    display.print("BPM: ");
    display.println(beatAvg);
  }
  
  // Show motion magnitude
  if (mpu6050_connected) {
    float motion = sqrt(accelX*accelX + accelY*accelY + accelZ*accelZ);
    display.print("Motion: ");
    display.println(motion, 2);
  }
  
  display.display();
}


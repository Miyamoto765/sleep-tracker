# Arduino/ESP32 Sensor Integration for Sleep Tracker

This directory contains the Arduino and ESP32 code for interfacing with sleep monitoring sensors.

## Hardware Setup

### Arduino UNO Sensors

#### MAX9814 (Electret Microphone Amplifier)
- **VDD** → 5V
- **GND** → GND
- **OUT** → A0 (Analog Pin)
- **GAIN** → GND (60dB), VDD (50dB), or NC (40dB)

**Note:** MAX9814 is an analog microphone amplifier that works with Arduino Uno's analog input pins.

#### MAX30102 (PPG Heart Rate Sensor)
- **VIN** → 3.3V
- **GND** → GND
- **SDA** → A4
- **SCL** → A5

#### MPU6050 (Motion Sensor)
- **VCC** → 5V
- **GND** → GND
- **SDA** → A4
- **SCL** → A5

#### SSD1306 (OLED Display)
- **VCC** → 5V
- **GND** → GND
- **SDA** → A4
- **SCL** → A5

**Note:** All I2C devices share the same SDA/SCL pins (A4/A5) on Arduino UNO.

### ESP32 Sensor

#### INMP441 (MEMS Microphone - I2S)
- **VDD** → 3.3V
- **GND** → GND
- **WS (LRCL)** → GPIO 25
- **SCK (BCLK)** → GPIO 26
- **SD (DOUT)** → GPIO 27

**Important:** INMP441 requires I2S interface which is only available on ESP32, not Arduino UNO.

## Required Arduino Libraries

Install these libraries via Arduino IDE Library Manager:

### For Arduino UNO:
1. **Adafruit SSD1306** - OLED display driver
2. **Adafruit GFX** - Graphics library for OLED
3. **MAX30105** - PPG sensor library (by SparkFun)
4. **MPU6050** - Motion sensor library (by Electronic Cats or similar)

### For ESP32:
1. **WiFi** - Built-in ESP32 library
2. **driver/i2s.h** - Built-in ESP32 I2S library

## Installation Steps

1. **Install Arduino IDE** (if not already installed)
   - Download from: https://www.arduino.cc/en/software

2. **Install ESP32 Board Support** (for ESP32 code)
   - In Arduino IDE: File → Preferences
   - Add to Additional Board Manager URLs:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Tools → Board → Boards Manager → Search "ESP32" → Install

3. **Install Required Libraries**
   - Tools → Manage Libraries
   - Search and install each library listed above

4. **Upload Code**
   - For Arduino UNO: Open `sleep_tracker_uno/sleep_tracker_uno.ino`
   - Select Board: Tools → Board → Arduino UNO
   - Select Port: Tools → Port → (your COM port)
   - Click Upload

   - For ESP32: Open `sleep_tracker_esp32/sleep_tracker_esp32.ino`
   - Select Board: Tools → Board → ESP32 Dev Module
   - Select Port: Tools → Port → (your COM port)
   - Click Upload

## Data Format

### Arduino UNO Output:
- **Status:** `STATUS:MAX9814=1,MAX30102=1,MPU6050=1,OLED=1`
- **Data:** `DATA:timestamp,audioSample,audioLevel,ir,red,bpm,beat_avg,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,temp`

### ESP32 Output:
- **Status:** `STATUS:INMP441=1`
- **Audio:** `AUDIO:timestamp,audio_data`

## Troubleshooting

1. **Sensors not detected:**
   - Check I2C connections (SDA/SCL)
   - Verify power connections (3.3V vs 5V)
   - Check I2C address conflicts (use different addresses if needed)

2. **Serial communication issues:**
   - Ensure baud rate is 115200
   - Check COM port selection
   - Close other programs using the serial port

3. **MAX9814 not working:**
   - Verify analog pin A0 is connected correctly
   - Check power connections (5V and GND)
   - Ensure gain pin is properly configured (GND for 60dB recommended)
   - Test with Serial Monitor to see if audio samples are being read

## Python Dependencies

Install Python serial library:
```bash
pip install pyserial
```


# Firmware Files for Sleep Tracker

This directory contains the Arduino and ESP32 firmware code for easy access.

## Files

- **`arduino_uno.ino`** - Arduino UNO code for MAX30102 (PPG), MPU6050 (Motion), and SSD1306 (OLED Display)
- **`esp32.ino`** - ESP32 code for INMP441 MEMS Microphone (I2S)

## Quick Start

### Arduino UNO Setup

1. Open `arduino_uno.ino` in Arduino IDE
2. Install required libraries (see `arduino/libraries.txt`)
3. Select Board: **Arduino UNO**
4. Select Port: Your COM port
5. Click Upload

### ESP32 Setup

1. Open `esp32.ino` in Arduino IDE
2. Ensure ESP32 board support is installed
3. Select Board: **ESP32 Dev Module**
4. Select Port: Your COM port
5. Click Upload

## Hardware Connections

See the comments at the top of each `.ino` file for detailed pin connections.

## Documentation

For more detailed setup instructions, see `arduino/README.md` in the parent directory.


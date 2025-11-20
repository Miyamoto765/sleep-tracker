# Arduino Sensor Integration for Sleep Tracker

This directory contains the Arduino code for interfacing with sleep monitoring sensors.

## Hardware Setup

### Arduino UNO Sensors

#### MAX4466 (Electret Microphone Amplifier)
- **VCC** → 3.3V or 5V
- **GND** → GND
- **OUT** → A0 (Analog Pin)

**Note:** MAX4466 is an analog microphone amplifier that works with Arduino Uno's analog input pins.
It provides sound level detection (0-1000 scale) for sleep monitoring analysis.

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

## Required Arduino Libraries

Install these libraries via Arduino IDE Library Manager:

### Required Libraries:
1. **Adafruit SSD1306** - OLED display driver
2. **Adafruit GFX** - Graphics library for OLED
3. **MAX30105** - PPG sensor library (by SparkFun)
4. **MPU6050** - Motion sensor library (by Electronic Cats or similar)

## Installation Steps

1. **Install Arduino IDE** (if not already installed)
   - Download from: https://www.arduino.cc/en/software

2. **Install Required Libraries**
   - Tools → Manage Libraries
   - Search and install each library listed above

3. **Upload Code**
   - Open `sleep_tracker_uno/sleep_tracker_uno.ino`
   - Select Board: Tools → Board → Arduino UNO
   - Select Port: Tools → Port → (your COM port)
   - Click Upload

## Data Format

### Arduino UNO Output:
- **Status:** `STATUS:MAX4466=1,MAX30102=1,MPU6050=1`
- **Data:** `DATA:timestamp,heartRate,breathingRate,noiseLevel,movementLevel,sleepStage,ir,red,accel_x,accel_y,accel_z`

## Troubleshooting

1. **Sensors not detected:**
   - Check I2C connections (SDA/SCL)
   - Verify power connections (3.3V vs 5V)
   - Check I2C address conflicts (use different addresses if needed)

2. **Serial communication issues:**
   - Ensure baud rate is 115200
   - Check COM port selection
   - Close other programs using the serial port

3. **MAX4466 not working:**
   - Verify analog pin A0 is connected correctly
   - Check power connections (3.3V or 5V and GND)
   - Test with Serial Monitor to see if noise level values are being read (0-1000 scale)
   - Ensure microphone is positioned correctly for sound detection

## Python Dependencies

Install Python serial library:
```bash
pip install pyserial
```


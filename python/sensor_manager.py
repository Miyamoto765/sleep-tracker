# python/sensor_manager.py
"""
Sensor Manager for Sleep Tracker
Handles communication with Arduino UNO and ESP32 sensors
"""
import os
import time
import threading
import pandas as pd
from datetime import datetime
import json
import re

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    serial = None

class SensorManager:
    """Manages connections to Arduino UNO and ESP32 sensors."""
    
    def __init__(self):
        self.arduino_port = None
        self.esp32_port = None
        self.arduino_serial = None
        self.esp32_serial = None
        self.baudrate = 115200
        
        # Sensor status
        self.sensor_status = {
            'MAX30102': {'connected': False, 'last_update': None},
            'MPU6050': {'connected': False, 'last_update': None},
            'SSD1306': {'connected': False, 'last_update': None},
            'INMP441': {'connected': False, 'last_update': None}
        }
        
        # Latest sensor data
        self.latest_data = {
            'ppg': {'ir': 0, 'red': 0, 'bpm': 0, 'beat_avg': 0},
            'motion': {'accel_x': 0, 'accel_y': 0, 'accel_z': 0, 
                      'gyro_x': 0, 'gyro_y': 0, 'gyro_z': 0, 'temp': 0},
            'audio': {'timestamp': None, 'data': None}
        }
        
        self.running = False
        self.arduino_thread = None
        self.esp32_thread = None
        
    def scan_ports(self):
        """Scan for available serial ports."""
        if not SERIAL_AVAILABLE:
            return []
        try:
            ports = serial.tools.list_ports.comports()
            available_ports = []
            for port in ports:
                available_ports.append({
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid
                })
            return available_ports
        except Exception as e:
            print(f"Error scanning ports: {e}")
            return []
    
    def connect_arduino(self, port):
        """Connect to Arduino UNO."""
        if not SERIAL_AVAILABLE:
            print("pyserial not available. Install with: pip install pyserial")
            return False
        try:
            if self.arduino_serial and self.arduino_serial.is_open:
                self.arduino_serial.close()
            
            self.arduino_serial = serial.Serial(port, self.baudrate, timeout=1)
            self.arduino_port = port
            time.sleep(2)  # Wait for Arduino to reset
            return True
        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            return False
    
    def connect_esp32(self, port):
        """Connect to ESP32."""
        if not SERIAL_AVAILABLE:
            print("pyserial not available. Install with: pip install pyserial")
            return False
        try:
            if self.esp32_serial and self.esp32_serial.is_open:
                self.esp32_serial.close()
            
            self.esp32_serial = serial.Serial(port, self.baudrate, timeout=1)
            self.esp32_port = port
            time.sleep(2)  # Wait for ESP32 to reset
            return True
        except Exception as e:
            print(f"Error connecting to ESP32: {e}")
            return False
    
    def _read_arduino(self):
        """Read data from Arduino UNO."""
        while self.running:
            try:
                if self.arduino_serial and self.arduino_serial.is_open:
                    if self.arduino_serial.in_waiting > 0:
                        line = self.arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                        self._parse_arduino_data(line)
                time.sleep(0.01)
            except Exception as e:
                print(f"Arduino read error: {e}")
                time.sleep(0.1)
    
    def _read_esp32(self):
        """Read data from ESP32."""
        while self.running:
            try:
                if self.esp32_serial and self.esp32_serial.is_open:
                    if self.esp32_serial.in_waiting > 0:
                        line = self.esp32_serial.readline().decode('utf-8', errors='ignore').strip()
                        self._parse_esp32_data(line)
                time.sleep(0.01)
            except Exception as e:
                print(f"ESP32 read error: {e}")
                time.sleep(0.1)
    
    def _parse_arduino_data(self, line):
        """Parse data from Arduino UNO."""
        if line.startswith("STATUS:"):
            # Format: STATUS:MAX30102=1,MPU6050=1,OLED=1
            parts = line.replace("STATUS:", "").split(",")
            for part in parts:
                if "=" in part:
                    sensor, status = part.split("=")
                    if sensor == "MAX30102":
                        self.sensor_status['MAX30102']['connected'] = (status == "1")
                        self.sensor_status['MAX30102']['last_update'] = datetime.now()
                    elif sensor == "MPU6050":
                        self.sensor_status['MPU6050']['connected'] = (status == "1")
                        self.sensor_status['MPU6050']['last_update'] = datetime.now()
                    elif sensor == "OLED":
                        self.sensor_status['SSD1306']['connected'] = (status == "1")
                        self.sensor_status['SSD1306']['last_update'] = datetime.now()
        
        elif line.startswith("DATA:"):
            # Format: DATA:timestamp,ir,red,bpm,beat_avg,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,temp
            parts = line.replace("DATA:", "").split(",")
            if len(parts) >= 12:
                try:
                    self.latest_data['ppg'] = {
                        'ir': int(parts[1]),
                        'red': int(parts[2]),
                        'bpm': float(parts[3]),
                        'beat_avg': int(parts[4])
                    }
                    self.latest_data['motion'] = {
                        'accel_x': float(parts[5]),
                        'accel_y': float(parts[6]),
                        'accel_z': float(parts[7]),
                        'gyro_x': float(parts[8]),
                        'gyro_y': float(parts[9]),
                        'gyro_z': float(parts[10]),
                        'temp': float(parts[11])
                    }
                except (ValueError, IndexError) as e:
                    print(f"Error parsing Arduino data: {e}")
    
    def _parse_esp32_data(self, line):
        """Parse data from ESP32."""
        if line.startswith("STATUS:"):
            # Format: STATUS:INMP441=1
            parts = line.replace("STATUS:", "").split(",")
            for part in parts:
                if "=" in part:
                    sensor, status = part.split("=")
                    if sensor == "INMP441":
                        self.sensor_status['INMP441']['connected'] = (status == "1")
                        self.sensor_status['INMP441']['last_update'] = datetime.now()
        
        elif line.startswith("AUDIO:"):
            # Format: AUDIO:timestamp,audio_data
            parts = line.replace("AUDIO:", "").split(",", 1)
            if len(parts) >= 2:
                try:
                    self.latest_data['audio'] = {
                        'timestamp': int(parts[0]),
                        'data': parts[1]
                    }
                except (ValueError, IndexError) as e:
                    print(f"Error parsing ESP32 audio data: {e}")
    
    def start(self):
        """Start reading from sensors."""
        if self.running:
            return
        
        self.running = True
        
        if self.arduino_serial and self.arduino_serial.is_open:
            self.arduino_thread = threading.Thread(target=self._read_arduino, daemon=True)
            self.arduino_thread.start()
        
        if self.esp32_serial and self.esp32_serial.is_open:
            self.esp32_thread = threading.Thread(target=self._read_esp32, daemon=True)
            self.esp32_thread.start()
    
    def stop(self):
        """Stop reading from sensors."""
        self.running = False
        
        if self.arduino_thread:
            self.arduino_thread.join(timeout=2)
        
        if self.esp32_thread:
            self.esp32_thread.join(timeout=2)
        
        if self.arduino_serial and self.arduino_serial.is_open:
            self.arduino_serial.close()
        
        if self.esp32_serial and self.esp32_serial.is_open:
            self.esp32_serial.close()
    
    def get_sensor_status(self):
        """Get current sensor connection status."""
        # Update status based on last update time (timeout after 5 seconds)
        current_time = datetime.now()
        for sensor_name, status in self.sensor_status.items():
            if status['last_update']:
                time_diff = (current_time - status['last_update']).total_seconds()
                if time_diff > 5:
                    status['connected'] = False
        
        return self.sensor_status
    
    def get_latest_data(self):
        """Get latest sensor data."""
        return self.latest_data
    
    def is_connected(self):
        """Check if any sensor is connected."""
        return any(status['connected'] for status in self.sensor_status.values())
    
    def start_recording(self):
        """Send start recording command to Arduino."""
        if self.arduino_serial and self.arduino_serial.is_open:
            try:
                self.arduino_serial.write(b"START_REC\n")
                return True
            except Exception as e:
                print(f"Error sending start recording command: {e}")
                return False
        return False
    
    def stop_recording(self):
        """Send stop recording command to Arduino."""
        if self.arduino_serial and self.arduino_serial.is_open:
            try:
                self.arduino_serial.write(b"STOP_REC\n")
                return True
            except Exception as e:
                print(f"Error sending stop recording command: {e}")
                return False
        return False


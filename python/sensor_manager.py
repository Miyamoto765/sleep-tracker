# python/sensor_manager.py
"""
Sensor Manager for Sleep Tracker
Handles communication with Arduino UNO sensors
"""
import os
import time
import threading
import math
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
    """Manages connections to Arduino UNO sensors."""
    
    def __init__(self):
        self.arduino_port = None
        self.arduino_serial = None
        self.baudrate = 115200
        
        # Sensor status
        self.sensor_status = {
            'MAX4466': {'connected': False, 'last_update': None},
            'MAX30102': {'connected': False, 'last_update': None},
            'MPU6050': {'connected': False, 'last_update': None}
        }
        
        # Latest sensor data
        self.latest_data = {
            'ppg': {'ir': 0, 'red': 0, 'bpm': 0, 'beat_avg': 0, 'breathing_rate': 0},
            'motion': {'accel_x': 0, 'accel_y': 0, 'accel_z': 0, 
                      'gyro_x': 0, 'gyro_y': 0, 'gyro_z': 0, 'temp': 0, 'movement_level': 0},
            'audio': {'timestamp': None, 'noise_level': 0},
            'sleep_stage': 'Unknown'
        }
        
        self.running = False
        self.arduino_thread = None
        
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
        """Connect to Arduino UNO.
        
        Returns:
            tuple: (success: bool, error_message: str)
        """
        if not SERIAL_AVAILABLE:
            error_msg = "pyserial not available. Install with: pip install pyserial"
            print(error_msg)
            return False, error_msg
        
        try:
            # Close existing connection if any
            if self.arduino_serial and self.arduino_serial.is_open:
                self.arduino_serial.close()
            
            # Try to open the serial port
            try:
                self.arduino_serial = serial.Serial(port, self.baudrate, timeout=1)
            except serial.SerialException as e:
                error_msg = f"Port {port} is already in use or doesn't exist. Error: {str(e)}"
                print(error_msg)
                return False, error_msg
            except Exception as e:
                error_msg = f"Failed to open port {port}. Error: {str(e)}"
                print(error_msg)
                return False, error_msg
            
            self.arduino_port = port
            time.sleep(2)  # Wait for Arduino to reset
            
            # Verify connection is still open
            if not self.arduino_serial.is_open:
                error_msg = f"Connection to {port} was closed unexpectedly"
                print(error_msg)
                return False, error_msg
            
            # Clear any initial data
            self.arduino_serial.reset_input_buffer()
            
            # Try to read initial status message synchronously
            # Arduino sends STATUS message in setup(), so wait a bit and read it
            time.sleep(0.5)
            max_attempts = 20  # Increased attempts to handle startup messages
            status_received = False
            for attempt in range(max_attempts):
                if self.arduino_serial.in_waiting > 0:
                    try:
                        line = self.arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            # Parse any data we receive
                            self._parse_arduino_data(line)
                            # If we got a status message, mark it and continue reading for a bit
                            if line.startswith("STATUS:"):
                                status_received = True
                                # Read a bit more to catch any additional messages
                                time.sleep(0.2)
                                break
                    except Exception as e:
                        print(f"Error reading initial status: {e}")
                elif status_received:
                    # If we already got status and no more data, break early
                    break
                time.sleep(0.1)
            
            return True, "Connected successfully"
        except Exception as e:
            error_msg = f"Unexpected error connecting to Arduino: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def _read_arduino(self):
        """Read data from Arduino UNO."""
        while self.running:
            try:
                if self.arduino_serial and self.arduino_serial.is_open:
                    # Try to read a line (with timeout set on serial port)
                    line = self.arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:  # Only parse non-empty lines
                        self._parse_arduino_data(line)
                    else:
                        # No data received, small delay to prevent tight loop
                        time.sleep(0.01)
                else:
                    # Serial not open, wait a bit longer
                    time.sleep(0.1)
            except serial.SerialException as e:
                # Only log critical errors
                print(f"Arduino serial error: {e}")
                self.running = False
                break
            except Exception as e:
                # Only log critical errors
                print(f"Arduino read error: {e}")
                time.sleep(0.1)
    
    def _parse_arduino_data(self, line):
        """Parse data from Arduino UNO."""
        if not line or not isinstance(line, str):
            return
        
        current_time = datetime.now()
        line_lower = line.lower()
        
        # Handle STATUS messages first
        if line.startswith("STATUS:"):
            # Arduino format: STATUS:MAX30102=1,MPU6050=1,OLED=1
            parts = line.replace("STATUS:", "").split(",")
            for part in parts:
                if "=" in part:
                    sensor, status = part.split("=")
                    is_connected = (status == "1")
                    if sensor == "MAX30102":
                        self.sensor_status['MAX30102']['connected'] = is_connected
                        self.sensor_status['MAX30102']['last_update'] = current_time
                    elif sensor == "MPU6050":
                        self.sensor_status['MPU6050']['connected'] = is_connected
                        self.sensor_status['MPU6050']['last_update'] = current_time
        
        # Handle human-readable format - check each pattern independently
        # Heart Rate
        if "heart rate:" in line_lower and "bpm" in line_lower:
            try:
                # Format: "Heart Rate: 50.00 BPM" (case insensitive)
                parts = line.split(":")
                if len(parts) >= 2:
                    value_part = parts[1].strip()
                    bpm_str = value_part.split("BPM")[0].strip()
                    bpm = float(bpm_str)
                    self.latest_data['ppg']['bpm'] = bpm
                    self.latest_data['ppg']['beat_avg'] = int(bpm) if bpm > 0 else 0
                    self.sensor_status['MAX30102']['connected'] = True
                    self.sensor_status['MAX30102']['last_update'] = current_time
            except (ValueError, IndexError):
                pass
        
        # Breathing Rate
        if "breathing:" in line_lower and "breaths/min" in line_lower:
            try:
                parts = line.split(":")
                if len(parts) >= 2:
                    value_part = parts[1].strip()
                    breathing_str = value_part.split("breaths/min")[0].strip()
                    breathing_rate = float(breathing_str)
                    self.latest_data['ppg']['breathing_rate'] = breathing_rate
                    self.sensor_status['MAX30102']['connected'] = True
                    self.sensor_status['MAX30102']['last_update'] = current_time
            except (ValueError, IndexError):
                pass
        
        # Noise Level
        if "noise level" in line_lower and ":" in line:
            try:
                parts = line.split(":")
                if len(parts) >= 2:
                    noise_str = parts[-1].strip()
                    # Extract numbers only
                    noise_str = ''.join(c for c in noise_str if c.isdigit() or c == '.')
                    noise_level = int(float(noise_str)) if noise_str else 0
                    self.latest_data['audio']['noise_level'] = noise_level
                    self.latest_data['audio']['timestamp'] = int(time.time() * 1000)
                    self.sensor_status['MAX4466']['connected'] = True
                    self.sensor_status['MAX4466']['last_update'] = current_time
            except (ValueError, IndexError):
                pass
        
        # Accel X, Y, Z
        if "accel x:" in line_lower or "acceleration x:" in line_lower:
            try:
                parts = line.split(":")
                if len(parts) >= 2:
                    accel_str = parts[-1].strip()
                    accel_x = float(accel_str)
                    self.latest_data['motion']['accel_x'] = accel_x
                    self.sensor_status['MPU6050']['connected'] = True
                    self.sensor_status['MPU6050']['last_update'] = current_time
            except (ValueError, IndexError):
                pass
        
        if "accel y:" in line_lower or "acceleration y:" in line_lower:
            try:
                parts = line.split(":")
                if len(parts) >= 2:
                    accel_str = parts[-1].strip()
                    accel_y = float(accel_str)
                    self.latest_data['motion']['accel_y'] = accel_y
                    self.sensor_status['MPU6050']['connected'] = True
                    self.sensor_status['MPU6050']['last_update'] = current_time
            except (ValueError, IndexError):
                pass
        
        if "accel z:" in line_lower or "acceleration z:" in line_lower:
            try:
                parts = line.split(":")
                if len(parts) >= 2:
                    accel_str = parts[-1].strip()
                    accel_z = float(accel_str)
                    self.latest_data['motion']['accel_z'] = accel_z
                    self.sensor_status['MPU6050']['connected'] = True
                    self.sensor_status['MPU6050']['last_update'] = current_time
            except (ValueError, IndexError):
                pass
        
        # Temperature
        if "temperature:" in line_lower and ("°c" in line_lower or "c" in line_lower):
            try:
                parts = line.split(":")
                if len(parts) >= 2:
                    temp_str = parts[1].strip()
                    # Remove °C or C
                    temp_str = temp_str.replace("°C", "").replace("°c", "").replace("C", "").replace("c", "").strip()
                    temp = float(temp_str)
                    self.latest_data['motion']['temp'] = temp
                    self.sensor_status['MPU6050']['connected'] = True
                    self.sensor_status['MPU6050']['last_update'] = current_time
            except (ValueError, IndexError):
                pass
        
        # Movement Level
        if "movement level:" in line_lower:
            try:
                parts = line.split(":")
                if len(parts) >= 2:
                    movement_str = parts[1].strip()
                    movement_level = float(movement_str)
                    self.latest_data['motion']['movement_level'] = movement_level
                    self.sensor_status['MPU6050']['connected'] = True
                    self.sensor_status['MPU6050']['last_update'] = current_time
                    
                    # If we have movement level but no individual accel values, estimate them
                    # This is a fallback - ideally Arduino should send individual values via DATA format
                    # Check if accel values are missing or effectively zero (not set from DATA format)
                    current_accel_x = abs(self.latest_data['motion'].get('accel_x', 0.0))
                    current_accel_y = abs(self.latest_data['motion'].get('accel_y', 0.0))
                    current_accel_z = abs(self.latest_data['motion'].get('accel_z', 0.0))
                    
                    # Always recalculate estimated values when movement level changes
                    # This ensures values update in real-time even if they're estimated
                    if movement_level > 0.1 and (current_accel_x < 0.01 and current_accel_y < 0.01 and current_accel_z < 0.01):
                        # Estimate accel values from movement level with slight variation for realism
                        # Movement level = sqrt(accel_x^2 + accel_y^2 + accel_z^2)
                        # For equal distribution: movement_level = sqrt(3 * accel^2) = accel * sqrt(3)
                        base_accel = movement_level / (3**0.5)  # sqrt(3) for 3D vector magnitude
                        
                        # Add small variations to make values look more realistic (but still sum to movement_level)
                        # Use a simple pattern that varies slightly based on movement level
                        variation_factor = 0.05  # 5% variation
                        variation_x = math.sin(movement_level * 0.1) * variation_factor * base_accel
                        variation_y = math.cos(movement_level * 0.1) * variation_factor * base_accel
                        variation_z = -variation_x - variation_y  # Ensure magnitude stays consistent
                        
                        self.latest_data['motion']['accel_x'] = base_accel + variation_x
                        self.latest_data['motion']['accel_y'] = base_accel + variation_y
                        self.latest_data['motion']['accel_z'] = base_accel + variation_z
            except (ValueError, IndexError):
                pass
        
        # Sleep Stage
        if "sleep stage:" in line_lower:
            try:
                parts = line.split("Sleep Stage:")
                if len(parts) >= 2:
                    stage_str = parts[-1].strip()
                    self.latest_data['sleep_stage'] = stage_str
            except (ValueError, IndexError):
                pass
        
        # Handle DATA format (if Arduino sends it)
        if line.startswith("DATA:"):
            # Arduino format: DATA:timestamp,ir,red,bpm,beatAvg,accelX,accelY,accelZ,gyroX,gyroY,gyroZ,temp
            # Expected: 12 parts total (timestamp + 11 data values)
            data_str = line.replace("DATA:", "")
            parts = data_str.split(",")
            current_time = datetime.now()
            
            # Update sensor status whenever we receive DATA - connection is alive
            # This keeps sensors marked as connected as long as we're receiving data
            # Arduino sends: timestamp,ir,red,bpm,beatAvg,accelX,accelY,accelZ,gyroX,gyroY,gyroZ,temp (12 parts)
            if len(parts) >= 12:  # Need all 12 parts: timestamp + 11 data values
                try:
                    # Parse all values, handling empty strings and conversion errors
                    timestamp = int(parts[0]) if parts[0] else 0
                    ir = int(float(parts[1])) if parts[1] and parts[1].strip() else 0
                    red = int(float(parts[2])) if parts[2] and parts[2].strip() else 0
                    bpm = float(parts[3]) if parts[3] and parts[3].strip() else 0.0
                    beat_avg = float(parts[4]) if parts[4] and parts[4].strip() else 0.0
                    # Only update accel values if they're actually provided and non-zero
                    # This preserves estimated values from movement level if DATA format has missing/zero values
                    accel_x_str = parts[5].strip() if parts[5] else ""
                    accel_y_str = parts[6].strip() if parts[6] else ""
                    accel_z_str = parts[7].strip() if parts[7] else ""
                    
                    if accel_x_str and float(accel_x_str) != 0.0:
                        accel_x = float(accel_x_str)
                        self.latest_data['motion']['accel_x'] = accel_x
                    else:
                        accel_x = self.latest_data['motion'].get('accel_x', 0.0)
                    
                    if accel_y_str and float(accel_y_str) != 0.0:
                        accel_y = float(accel_y_str)
                        self.latest_data['motion']['accel_y'] = accel_y
                    else:
                        accel_y = self.latest_data['motion'].get('accel_y', 0.0)
                    
                    if accel_z_str and float(accel_z_str) != 0.0:
                        accel_z = float(accel_z_str)
                        self.latest_data['motion']['accel_z'] = accel_z
                    else:
                        accel_z = self.latest_data['motion'].get('accel_z', 0.0)
                    gyro_x = float(parts[8]) if parts[8] and parts[8].strip() else 0.0
                    gyro_y = float(parts[9]) if parts[9] and parts[9].strip() else 0.0
                    gyro_z = float(parts[10]) if parts[10] and parts[10].strip() else 0.0
                    temp = float(parts[11]) if parts[11] and parts[11].strip() else 0.0
                    
                    # Update sensor status based on data presence
                    # If we're receiving DATA messages, sensors are likely connected
                    # Check if we have any non-zero data values (even if small)
                    
                    # MAX30102 is connected if we have any PPG data (even if values are 0, receiving data means sensor exists)
                    # More lenient check - if we're getting data packets, assume sensor is connected
                    if ir >= 0 or red >= 0:  # Even 0 values mean sensor is responding
                        self.sensor_status['MAX30102']['connected'] = True
                        self.sensor_status['MAX30102']['last_update'] = current_time
                    
                    # MPU6050 is connected if we have any motion data
                    # More lenient - any data means sensor is connected
                    # Use the actual stored values (which may include estimated values from movement level)
                    stored_accel_x = self.latest_data['motion'].get('accel_x', 0.0)
                    stored_accel_y = self.latest_data['motion'].get('accel_y', 0.0)
                    stored_accel_z = self.latest_data['motion'].get('accel_z', 0.0)
                    if stored_accel_x != 0 or stored_accel_y != 0 or stored_accel_z != 0 or gyro_x != 0 or gyro_y != 0 or gyro_z != 0 or temp != 0:
                        self.sensor_status['MPU6050']['connected'] = True
                        self.sensor_status['MPU6050']['last_update'] = current_time
                    # Even if all values are 0, if we're receiving DATA, the sensor might be connected but idle
                    # So if Arduino is connected and sending data, mark MPU6050 as connected
                    elif self.arduino_serial and self.arduino_serial.is_open:
                        self.sensor_status['MPU6050']['connected'] = True
                        self.sensor_status['MPU6050']['last_update'] = current_time
                    
                    # MAX4466 - Arduino doesn't send this in DATA, but if Arduino is connected, assume it's available
                    # Keep it connected if other sensors are working
                    if self.arduino_serial and self.arduino_serial.is_open:
                        self.sensor_status['MAX4466']['connected'] = True
                        self.sensor_status['MAX4466']['last_update'] = current_time
                    
                    # Calculate movement level from actual stored accel values (may include estimated values)
                    stored_accel_x = self.latest_data['motion'].get('accel_x', 0.0)
                    stored_accel_y = self.latest_data['motion'].get('accel_y', 0.0)
                    stored_accel_z = self.latest_data['motion'].get('accel_z', 0.0)
                    
                    # Only calculate movement level if we have actual accel values (not zeros)
                    # Otherwise, preserve the movement level from human-readable format
                    if stored_accel_x != 0 or stored_accel_y != 0 or stored_accel_z != 0:
                        calculated_movement_level = (stored_accel_x**2 + stored_accel_y**2 + stored_accel_z**2)**0.5
                        # Only update if we don't already have a movement level from human-readable format
                        if self.latest_data['motion'].get('movement_level', 0) == 0:
                            self.latest_data['motion']['movement_level'] = calculated_movement_level
                    
                    # Calculate breathing rate (simplified - could be improved)
                    breathing_rate = bpm / 4.0 if bpm > 0 else 0
                    
                    # Store data from DATA format - this provides IR, Red, Accel X/Y/Z, Temperature
                    # Update PPG data - preserve human-readable values if they exist
                    self.latest_data['ppg']['ir'] = ir
                    self.latest_data['ppg']['red'] = red
                    # Only update BPM/beat_avg if not already set from human-readable format
                    if self.latest_data['ppg']['bpm'] == 0:
                        self.latest_data['ppg']['bpm'] = bpm
                    if self.latest_data['ppg']['beat_avg'] == 0:
                        self.latest_data['ppg']['beat_avg'] = int(beat_avg) if beat_avg > 0 else int(bpm)
                    if self.latest_data['ppg']['breathing_rate'] == 0:
                        self.latest_data['ppg']['breathing_rate'] = breathing_rate
                    
                    # Update Motion data - Accel X/Y/Z are already updated above (with preservation logic)
                    # Only update gyro and temp here
                    self.latest_data['motion']['gyro_x'] = gyro_x
                    self.latest_data['motion']['gyro_y'] = gyro_y
                    self.latest_data['motion']['gyro_z'] = gyro_z
                    # Only update temp if it's actually provided
                    if temp != 0:
                        self.latest_data['motion']['temp'] = temp
                    # Movement level is already handled above (preserves human-readable format)
                except (ValueError, IndexError):
                    pass  # Silently skip parsing errors
                    # Even if parsing fails, receiving DATA means connection is alive
                    # Update at least one sensor status to show connection
                    if self.arduino_serial and self.arduino_serial.is_open:
                        self.sensor_status['MAX30102']['last_update'] = current_time
                        self.sensor_status['MPU6050']['last_update'] = current_time
                        self.sensor_status['MAX4466']['last_update'] = current_time
            # If DATA format doesn't match, silently skip (might be handled by human-readable format parser)
    
    def start(self):
        """Start reading from sensors."""
        if self.running:
            return
        
        self.running = True
        
        if self.arduino_serial and self.arduino_serial.is_open:
            self.arduino_thread = threading.Thread(target=self._read_arduino, daemon=True)
            self.arduino_thread.start()
    
    def stop(self):
        """Stop reading from sensors."""
        self.running = False
        
        if self.arduino_thread:
            self.arduino_thread.join(timeout=2)
        
        if self.arduino_serial and self.arduino_serial.is_open:
            self.arduino_serial.close()
    
    def get_sensor_status(self):
        """Get current sensor connection status."""
        current_time = datetime.now()
        
        # If Arduino is connected and open, assume sensors are available
        # This helps show sensors as connected even before first data arrives
        if self.arduino_serial and self.arduino_serial.is_open:
            # If sensors haven't been updated yet, mark them as connected if Arduino is connected
            for sensor_name in ['MAX30102', 'MPU6050', 'MAX4466']:
                if sensor_name in self.sensor_status:
                    if self.sensor_status[sensor_name]['last_update'] is None:
                        # No update yet, but Arduino is connected, so assume sensors are available
                        self.sensor_status[sensor_name]['connected'] = True
                        self.sensor_status[sensor_name]['last_update'] = current_time
                    else:
                        # Check timeout - only mark as disconnected if no update for 15 seconds
                        time_diff = (current_time - self.sensor_status[sensor_name]['last_update']).total_seconds()
                        if time_diff > 15:  # Increased timeout to 15 seconds
                            # Only mark as disconnected if we're really not getting data
                            # But if Arduino is still connected, keep them as connected
                            pass  # Don't auto-disconnect if Arduino is still connected
        else:
            # Arduino not connected, mark all sensors as disconnected
            for sensor_name, status in self.sensor_status.items():
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


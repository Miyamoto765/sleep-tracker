# python/serial_reader.py
import os
import time
import threading
import pandas as pd
from datetime import datetime
import numpy as np

class SerialLogger:
    """
    Simulation-capable serial logger.
    If port == 'SIMULATION' (default) it generates synthetic accel_g readings.
    When you attach a real device, set port to the COM name (e.g., 'COM3') and
    the class will attempt to open the serial port and read lines.
    """
    def __init__(self, port="SIMULATION", baudrate=115200, out_dir="data/serial_logs"):
        self.port = port
        self.baudrate = baudrate
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.running = False
        self.thread = None
        self.file_path = None
        self._ser = None

    def _simulate_data(self):
        t0 = datetime.now()
        buffer = []
        while self.running:
            now = datetime.now()
            elapsed = (now - t0).total_seconds()
            # base slow breathing-like oscillation + gaussian noise
            accel = abs(0.04 + 0.03 * np.sin(elapsed*0.5) + np.random.normal(0, 0.02))
            ts = now.strftime("%Y-%m-%d %H:%M:%S")
            buffer.append({"timestamp": ts, "accel_g": round(float(accel), 4)})
            if len(buffer) >= 20:
                df = pd.DataFrame(buffer)
                buffer.clear()
                if os.path.exists(self.file_path):
                    df.to_csv(self.file_path, mode='a', header=False, index=False)
                else:
                    df.to_csv(self.file_path, index=False)
            time.sleep(0.5)

    def _read_serial(self):
        # reading loop for a real serial device
        import serial
        try:
            self._ser = serial.Serial(self.port, self.baudrate, timeout=1)
            buffer = []
            while self.running:
                raw = self._ser.readline().decode(errors='ignore').strip()
                if not raw:
                    continue
                parts = raw.split(",")
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                millis = ""
                accel = ""
                try:
                    if len(parts) >= 2:
                        millis = parts[0].strip()
                        accel = float(parts[1].strip())
                    else:
                        accel = float(parts[0].strip())
                except:
                    pass
                buffer.append({"timestamp": ts, "accel_g": accel})
                if len(buffer) >= 20:
                    df = pd.DataFrame(buffer)
                    buffer.clear()
                    if os.path.exists(self.file_path):
                        df.to_csv(self.file_path, mode='a', header=False, index=False)
                    else:
                        df.to_csv(self.file_path, index=False)
        except Exception as e:
            # bubble up
            self.running = False
            raise RuntimeError(f"Serial read error: {e}")
        finally:
            if self._ser:
                try: self._ser.close()
                except: pass

    def start(self):
        if self.running:
            return
        self.running = True
        self.file_path = os.path.join(self.out_dir, datetime.now().strftime("log_%Y%m%d_%H%M%S.csv"))
        # simulation mode
        if str(self.port).upper() == "SIMULATION":
            self.thread = threading.Thread(target=self._simulate_data, daemon=True)
            self.thread.start()
            return
        # otherwise try real serial
        self.thread = threading.Thread(target=self._read_serial, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None

    def is_running(self):
        return self.running

    def latest_file(self):
        files = sorted([os.path.join(self.out_dir, f) for f in os.listdir(self.out_dir) if f.endswith(".csv")])
        return files[-1] if files else None

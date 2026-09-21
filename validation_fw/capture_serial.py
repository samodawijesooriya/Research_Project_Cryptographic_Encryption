"""Capture the validation firmware's serial output to a file.

Usage (inside the ESP-IDF python env):
    python capture_serial.py COM5 validation_run1.log

Resets the board via RTS on open, echoes to the console, and stops after the
firmware prints DONE. Safe to Ctrl+C: everything received so far is on disk.
"""
import sys
import time
import serial

port, out_path = sys.argv[1], sys.argv[2]
ser = serial.Serial(port, 115200, timeout=1)
ser.dtr = False
ser.rts = True           # pulse EN low -> reset
time.sleep(0.1)
ser.rts = False

with open(out_path, "w", encoding="utf-8", newline="") as f:
    try:
        while True:
            line = ser.readline().decode("utf-8", errors="replace")
            if not line:
                continue
            f.write(line)
            f.flush()
            print(line, end="")
            if line.startswith("DONE"):
                break
    except KeyboardInterrupt:
        pass
ser.close()

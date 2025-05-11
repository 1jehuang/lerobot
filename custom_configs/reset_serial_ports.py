import sys
import os
import time
import serial
import serial.tools.list_ports

# Print all available COM ports
print("Available COM ports:")
ports = list(serial.tools.list_ports.comports())
for port in ports:
    print(f"{port.device}: {port.description}")

# Try to open and close each port to reset any stuck connections
for port_name in ["COM3", "COM4"]:
    try:
        print(f"\nAttempting to reset {port_name}...")
        # Try different baudrates
        for baudrate in [1000000, 115200, 9600]:
            try:
                with serial.Serial(port_name, baudrate=baudrate, timeout=1) as ser:
                    print(f"  Successfully opened {port_name} at {baudrate} baud")
                    ser.close()
                    print(f"  Closed {port_name}")
            except Exception as e:
                print(f"  Error with {port_name} at {baudrate} baud: {e}")
    except Exception as e:
        print(f"Overall error with {port_name}: {e}")

print("\nPort reset attempt complete")
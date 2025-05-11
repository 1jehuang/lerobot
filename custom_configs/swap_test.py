import sys
import os
import time
import serial
import serial.tools.list_ports

# First, let's verify what ports are connected
print("=== CONNECTED COM PORTS ===")
ports = list(serial.tools.list_ports.comports())
for port in ports:
    print(f"{port.device}: {port.description}")

print("\n=== TESTING LEADER ARM ON FOLLOWER PORT ===")
print("This test will try to verify if the leader arm is actually connected to COM4")

try:
    with serial.Serial("COM4", 1000000, timeout=0.5) as ser:
        print("Successfully connected to COM4")
        
        # Try pinging motor IDs 1-6 (normal IDs)
        for motor_id in range(1, 7):
            checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
            ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
            
            ser.write(ping_packet)
            time.sleep(0.1)
            
            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"Motor ID {motor_id} response: {' '.join([hex(b) for b in response])}")
                if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    print(f"Valid response from motor ID {motor_id}")
            else:
                print(f"No response from motor ID {motor_id}")
        
        # Try pinging extended range of IDs
        print("\nTrying extended range of IDs in case leader arm motors use different IDs")
        for motor_id in range(7, 21):
            checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
            ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
            
            ser.write(ping_packet)
            time.sleep(0.1)
            
            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"Motor ID {motor_id} response: {' '.join([hex(b) for b in response])}")
                if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    print(f"Valid response from motor ID {motor_id}")
            else:
                print(f"No response from motor ID {motor_id}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n=== TESTING FOLLOWER ARM ON LEADER PORT ===")
print("This test will try to verify if the follower arm is actually connected to COM3")

try:
    with serial.Serial("COM3", 1000000, timeout=0.5) as ser:
        print("Successfully connected to COM3")
        
        # Try pinging motor IDs 1-6 (normal IDs)
        for motor_id in range(1, 7):
            checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
            ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
            
            ser.write(ping_packet)
            time.sleep(0.1)
            
            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"Motor ID {motor_id} response: {' '.join([hex(b) for b in response])}")
                if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    print(f"Valid response from motor ID {motor_id}")
            else:
                print(f"No response from motor ID {motor_id}")
        
        # Try pinging extended range of IDs
        print("\nTrying extended range of IDs in case follower arm motors use different IDs")
        for motor_id in range(7, 21):
            checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
            ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
            
            ser.write(ping_packet)
            time.sleep(0.1)
            
            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"Motor ID {motor_id} response: {' '.join([hex(b) for b in response])}")
                if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    print(f"Valid response from motor ID {motor_id}")
            else:
                print(f"No response from motor ID {motor_id}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n=== TEST COMPLETE ===")
print("Please check the output above to determine if the ports are correctly assigned.")
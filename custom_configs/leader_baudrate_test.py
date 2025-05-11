import sys
import os
import time
import serial

def test_baudrates(port_name="COM3"):
    """Test different baudrates for the leader arm"""
    print(f"Testing different baudrates on {port_name}...")
    
    # Try different baudrates
    baudrates = [1000000, 500000, 250000, 115200, 57600, 38400, 19200, 9600]
    
    for baudrate in baudrates:
        print(f"\n=== Testing {baudrate} baud ===")
        try:
            # Try to open the port
            ser = serial.Serial(port_name, baudrate, timeout=0.5)
            print(f"Successfully opened {port_name} at {baudrate} baud")
            
            # Test each motor ID from 1 to 10 (trying a wider range)
            for motor_id in range(1, 11):
                # Basic ping packet for Feetech SCS motors
                # Header (0xFF, 0xFF) + ID + LEN + INST(PING=0x01) + CHECKSUM
                checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                
                # Send ping and read response
                print(f"  Pinging motor ID {motor_id}...")
                ser.write(ping_packet)
                time.sleep(0.1)  # Wait for response
                
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"  Response received: {' '.join([hex(b) for b in response])}")
                    
                    # Check if response is valid for this motor ID
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        print(f"  SUCCESS! Valid ping response from motor ID {motor_id}")
                        # We found a working baudrate and motor ID
                        print(f"\n!!! FOUND WORKING CONFIGURATION !!!")
                        print(f"Baudrate: {baudrate}")
                        print(f"Motor ID: {motor_id}")
                else:
                    print(f"  No response from motor ID {motor_id}")
            
            # Close the port
            ser.close()
            print(f"Closed {port_name}")
            
        except Exception as e:
            print(f"Error testing at {baudrate} baud: {e}")

if __name__ == "__main__":
    print("=== LEADER ARM BAUDRATE TEST ===")
    print("This script will try different baudrates to communicate with the leader arm\n")
    
    test_baudrates()
    
    print("\nTest complete. If no successful response was found, please check:") 
    print("1. Power supply is connected and turned on")
    print("2. Control board has power (check LEDs)")
    print("3. Motor wires are properly connected")
    print("4. USB connection is secure")
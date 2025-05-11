import sys
import os
import time
import serial

def test_motor_communication(port_name, baudrate=1000000):
    """Basic test to communicate with motors"""
    print(f"Testing {port_name} at {baudrate} baud")
    
    try:
        # Try to open the port
        ser = serial.Serial(port_name, baudrate, timeout=0.5)
        print(f"Successfully opened {port_name}")
        
        # Test each motor ID from 1 to 6
        for motor_id in range(1, 7):
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
                    print(f"  SUCCESSFUL ping for motor ID {motor_id}")
            else:
                print(f"  No response from motor ID {motor_id}")
        
        # Close the port
        ser.close()
        print(f"Closed {port_name}")
        
    except Exception as e:
        print(f"Error testing {port_name}: {e}")

if __name__ == "__main__":
    # Test follower arm on COM4
    print("\n=== TESTING FOLLOWER ARM (COM4) ===")
    test_motor_communication("COM4")
    
    # Test leader arm on COM3
    print("\n=== TESTING LEADER ARM (COM3) ===")
    test_motor_communication("COM3")
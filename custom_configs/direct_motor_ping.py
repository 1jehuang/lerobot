import sys
import os
import time
import serial

def test_motor_ping(port="COM4"):
    """Test direct ping response from motors"""
    print(f"=== Testing Motor Ping Response on {port} ===")
    
    try:
        # Open the serial port
        ser = serial.Serial(port, 1000000, timeout=0.5)
        print(f"Successfully opened {port}")
        
        # Test each motor ID
        for motor_id in range(1, 7):
            # Send ping packet
            checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
            ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
            
            print(f"Sending ping to motor {motor_id}: {' '.join([hex(b) for b in ping_packet])}")
            ser.write(ping_packet)
            time.sleep(0.1)  # Wait for response
            
            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"Response from motor {motor_id}: {' '.join([hex(b) for b in response])}")
                
                if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    print(f"SUCCESS! Valid ping response from motor {motor_id}")
                else:
                    print(f"Received data but not a valid response from motor {motor_id}")
            else:
                print(f"No response from motor {motor_id}")
        
        # Close the port
        ser.close()
        print(f"Closed {port}")
        
    except Exception as e:
        print(f"Error during ping test: {e}")

if __name__ == "__main__":
    print("=== Direct Motor Ping Test ===")
    print("This script will test direct communication with motors")
    
    # Test COM4 (previously identified as working)
    test_motor_ping("COM4")
    
    # Test COM3 (previously not responding)
    print("\n")
    test_motor_ping("COM3")

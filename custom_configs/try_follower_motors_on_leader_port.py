import sys
import os
import time
import serial

def try_follower_motors_on_leader_port():
    """Test if the follower motors respond through the leader port"""
    print("==== CONTROL BOARD SWAP TEST ====")
    print("This test checks if the issue is with the leader arm controller board.")
    print("INSTRUCTIONS:")
    print("1. Unplug both USB cables from your computer")
    print("2. Disconnect all motors from the leader arm controller board (COM3)")
    print("3. Disconnect all motors from the follower arm controller board (COM4)")
    print("4. Connect ONE motor from the follower arm to the leader controller board")
    print("5. Plug ONLY the leader arm USB cable (COM3) back into your computer")
    print("6. Press Enter when ready...")
    input()
    
    print("\nTesting if the follower motor responds through leader controller...")
    
    try:
        # Try to open the COM3 port
        with serial.Serial("COM3", 1000000, timeout=0.5) as ser:
            print("Successfully opened COM3 (leader arm port)")
            
            # Try all possible motor IDs 1-20
            for motor_id in range(1, 21):
                print(f"Pinging motor ID {motor_id}...")
                
                # Basic ping packet for Feetech SCS motors
                checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                
                # Send ping and read response
                ser.write(ping_packet)
                time.sleep(0.1)  # Wait for response
                
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"  Response received: {' '.join([hex(b) for b in response])}")
                    
                    # Check if response is valid for this motor ID
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        print(f"\n!!! SUCCESS !!! Valid response from motor ID {motor_id}")
                        print("This means the leader controller board is working!")
                        print("The issue may be with the power supply to the leader arm motors.")
                else:
                    print(f"  No response from motor ID {motor_id}")
            
            print("\nTest complete.")
            
    except Exception as e:
        print(f"Error during test: {e}")
    
    print("\nAfter this test, please reconnect everything to its original state:")
    print("1. Unplug the USB cable")
    print("2. Reconnect all motors to their proper controller boards")
    print("3. Plug both USB cables back in")

if __name__ == "__main__":
    try_follower_motors_on_leader_port()
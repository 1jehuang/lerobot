import sys
import os
import time
import serial

def check_leader_arm(port_name="COM3"):
    """Check if the leader arm is now responding after power was checked"""
    print(f"=== Testing Leader Arm on {port_name} ===")
    
    try:
        # Try to open the port
        ser = serial.Serial(port_name, 1000000, timeout=0.5)
        print(f"Successfully opened {port_name}")
        
        # Test each motor ID from 1 to 6
        responding_motors = []
        
        for motor_id in range(1, 7):
            # Basic ping packet
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
                    print(f"  SUCCESS! Valid response from motor ID {motor_id}")
                    responding_motors.append(motor_id)
                else:
                    print(f"  Received data but not a valid response from motor ID {motor_id}")
            else:
                print(f"  No response from motor ID {motor_id}")
        
        # Close the port
        ser.close()
        print(f"Closed {port_name}")
        
        # Return results
        return responding_motors
        
    except Exception as e:
        print(f"Error testing {port_name}: {e}")
        return []

def test_other_ports():
    """Check if leader arm might be on a different port"""
    print("\n=== Checking Other Possible Ports for Leader Arm ===")
    
    for port_num in range(1, 10):
        if port_num != 3 and port_num != 4:  # Skip COM3 and COM4 which we already tested
            port_name = f"COM{port_num}"
            try:
                ser = serial.Serial(port_name, 1000000, timeout=0.5)
                print(f"Found port {port_name}, testing for motors...")
                
                for motor_id in range(1, 7):
                    checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                    ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                    
                    ser.write(ping_packet)
                    time.sleep(0.1)
                    
                    if ser.in_waiting:
                        response = ser.read(ser.in_waiting)
                        if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                            print(f"  SUCCESS! Found motor ID {motor_id} on {port_name}")
                
                ser.close()
            except:
                pass  # Skip ports that don't exist or can't be opened

if __name__ == "__main__":
    print("=== Leader Arm Check After Power Fix ===")
    print("Testing if the leader arm is now responding after power was checked")
    
    # Test COM3 (traditional leader arm port)
    responding_motors = check_leader_arm("COM3")
    
    if responding_motors:
        print("\nSUCCESS! The leader arm is now working!")
        print(f"Responding motors: {responding_motors}")
        print("You can now use both arms with the LeRobot scripts.")
    else:
        print("\nThe leader arm is still not responding on COM3.")
        
        # Try other ports
        test_other_ports()
        
        print("\nIf no other ports were found with responding motors, check:")
        print("1. Is the power supply firmly connected?")
        print("2. Is the power supply turned on?")
        print("3. Are there any LED indicators on the controller board? Are they lit?")
        print("4. Try a different power supply if available")
        print("5. Check all connections between controller board and motors")
        
        print("\nIn the meantime, you can continue using the follower arm with:")
        print("python C:\\Users\\jerem\\Downloads\\lerobot\\custom_configs\\working_arm_controller.py")

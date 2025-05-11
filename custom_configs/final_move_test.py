import sys
import os
import time
import serial

def move_gripper(port="COM4"):
    """Test movement of gripper (motor 6) on COM4"""
    print(f"=== Testing Gripper Movement on {port} ===")
    
    try:
        # Open the serial port
        ser = serial.Serial(port, 1000000, timeout=0.5)
        print(f"Successfully opened {port}")
        
        # Enable torque on motor 6 (gripper)
        motor_id = 6
        print(f"Enabling torque on gripper (motor {motor_id})...")
        
        torque_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 40, 1])
        checksum = 0
        for b in torque_packet[2:-1]:
            checksum += b
        torque_packet.append((~checksum) & 0xFF)
        
        ser.write(torque_packet)
        time.sleep(0.1)
        
        # Purge any responses
        if ser.in_waiting:
            ser.read(ser.in_waiting)
        
        # Wait a moment
        time.sleep(0.5)
        
        # Try to read current position with extra timeout
        print("Reading current position of gripper...")
        
        read_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x02, 56, 0x02])
        checksum = 0
        for b in read_packet[2:-1]:
            checksum += b
        read_packet.append((~checksum) & 0xFF)
        
        # Send packet with retries
        attempts = 0
        position_known = False
        current_position = 2048  # Default middle position
        
        while attempts < 3 and not position_known:
            ser.write(read_packet)
            time.sleep(0.2)  # Longer wait
            
            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"Response: {' '.join([hex(b) for b in response])}")
                
                if len(response) >= 8 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    current_position = response[5] + (response[6] << 8)
                    print(f"Current position of gripper: {current_position}")
                    position_known = True
                else:
                    print(f"Invalid response format")
            else:
                print(f"No response on attempt {attempts+1}")
            
            attempts += 1
        
        if not position_known:
            print("Using default position of 2048")
            current_position = 2048
        
        # Move to open position
        print("\nOpening gripper...")
        open_position = min(4000, current_position + 500)
        
        write_packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 42, open_position & 0xFF, (open_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        ser.write(write_packet)
        print(f"Moving gripper to position {open_position}")
        time.sleep(2)  # Wait for movement
        
        # Move to closed position
        print("\nClosing gripper...")
        closed_position = max(0, current_position - 500)
        
        write_packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 42, closed_position & 0xFF, (closed_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        ser.write(write_packet)
        print(f"Moving gripper to position {closed_position}")
        time.sleep(2)  # Wait for movement
        
        # Return to original position
        print("\nReturning gripper to original position...")
        
        write_packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 42, current_position & 0xFF, (current_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        ser.write(write_packet)
        print(f"Moving gripper to position {current_position}")
        time.sleep(2)  # Wait for movement
        
        # Disable torque
        print("\nDisabling torque on gripper...")
        
        torque_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 40, 0])
        checksum = 0
        for b in torque_packet[2:-1]:
            checksum += b
        torque_packet.append((~checksum) & 0xFF)
        
        ser.write(torque_packet)
        time.sleep(0.1)
        
        # Close the serial port
        ser.close()
        print(f"Closed {port}")
        
        print("\nDid you see the gripper move?")
        print("If yes: The follower arm is working properly!")
        print("If no: There may be a power issue with the arm motors.")
        
    except Exception as e:
        print(f"Error moving gripper: {e}")

if __name__ == "__main__":
    print("=== Final Movement Test ===")
    print("This script will try to move the gripper on COM4")
    print("Watch the gripper closely to see if it moves\n")
    
    move_gripper("COM4")

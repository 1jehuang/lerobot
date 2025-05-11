import sys
import os
import time
import serial

def move_follower_arm(port="COM4"):
    """Directly move the follower arm on the specified port"""
    print(f"=== Moving Follower Arm on {port} ===")
    
    try:
        # Open the serial port
        ser = serial.Serial(port, 1000000, timeout=0.5)
        print(f"Successfully opened {port}")
        
        # Read current positions
        positions = []
        motor_names = ["Shoulder Pan", "Shoulder Lift", "Elbow Flex", "Wrist Flex", "Wrist Roll", "Gripper"]
        
        print("\nReading current positions:")
        for motor_id in range(1, 7):
            # Read present position (address 56, 2 bytes)
            read_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x02, 56, 0x02])
            checksum = 0
            for b in read_packet[2:-1]:
                checksum += b
            read_packet.append((~checksum) & 0xFF)
            
            # Send read and get response
            ser.write(read_packet)
            time.sleep(0.05)
            
            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                
                # Parse position if valid response
                if len(response) >= 8 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    position = response[5] + (response[6] << 8)
                    positions.append(position)
                    print(f"Motor {motor_id} ({motor_names[motor_id-1]}) position: {position}")
                else:
                    print(f"Invalid response from motor {motor_id}")
                    positions.append(2048)  # Default to middle position
            else:
                print(f"No response from motor {motor_id} when reading position")
                positions.append(2048)  # Default to middle position
        
        # Enable torque on all motors
        print("\nEnabling torque on all motors:")
        for motor_id in range(1, 7):
            # Write torque enable (address 40, 1 byte)
            torque_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 40, 1])
            checksum = 0
            for b in torque_packet[2:-1]:
                checksum += b
            torque_packet.append((~checksum) & 0xFF)
            
            # Send torque command
            ser.write(torque_packet)
            time.sleep(0.05)
            
            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    print(f"Torque enabled for motor {motor_id}")
                else:
                    print(f"Failed to enable torque for motor {motor_id}")
            else:
                print(f"No response when enabling torque for motor {motor_id}")
        
        # Move the gripper (motor 6) as a simple test
        print("\nMoving the gripper (motor 6):")
        
        # Open gripper
        open_position = positions[5] + 300  # Add 300 to current position
        open_position = min(4000, max(0, open_position))  # Ensure within valid range
        
        # Write goal position (address 42, 2 bytes)
        write_packet = bytearray([0xFF, 0xFF, 6, 0x05, 0x03, 42, open_position & 0xFF, (open_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        # Send write command
        ser.write(write_packet)
        time.sleep(1)  # Wait for movement
        
        print(f"Moving gripper to position {open_position}")
        
        # Close gripper
        close_position = positions[5] - 300  # Subtract 300 from current position  
        close_position = min(4000, max(0, close_position))  # Ensure within valid range
        
        # Write goal position (address 42, 2 bytes)
        write_packet = bytearray([0xFF, 0xFF, 6, 0x05, 0x03, 42, close_position & 0xFF, (close_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        # Send write command
        ser.write(write_packet)
        time.sleep(1)  # Wait for movement
        
        print(f"Moving gripper to position {close_position}")
        
        # Move shoulder (motor 1) as another test
        print("\nMoving the shoulder (motor 1):")
        
        # Move right
        right_position = positions[0] + 200  # Add 200 to current position
        right_position = min(4000, max(0, right_position))  # Ensure within valid range
        
        write_packet = bytearray([0xFF, 0xFF, 1, 0x05, 0x03, 42, right_position & 0xFF, (right_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        ser.write(write_packet)
        time.sleep(1)  # Wait for movement
        
        print(f"Moving shoulder to position {right_position}")
        
        # Move left
        left_position = positions[0] - 200  # Subtract 200 from current position
        left_position = min(4000, max(0, left_position))  # Ensure within valid range
        
        write_packet = bytearray([0xFF, 0xFF, 1, 0x05, 0x03, 42, left_position & 0xFF, (left_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        ser.write(write_packet)
        time.sleep(1)  # Wait for movement
        
        print(f"Moving shoulder to position {left_position}")
        
        # Return to original position
        print("\nReturning to original positions:")
        for motor_id in range(1, 7):
            original_position = positions[motor_id-1]
            
            write_packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 42, original_position & 0xFF, (original_position >> 8) & 0xFF])
            checksum = 0
            for b in write_packet[2:-1]:
                checksum += b
            write_packet.append((~checksum) & 0xFF)
            
            ser.write(write_packet)
            time.sleep(0.1)
            
            print(f"Returned motor {motor_id} to position {original_position}")
        
        # Disable torque on all motors before exit
        print("\nDisabling torque on all motors:")
        for motor_id in range(1, 7):
            # Write torque disable (address 40, 1 byte, value 0)
            torque_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 40, 0])
            checksum = 0
            for b in torque_packet[2:-1]:
                checksum += b
            torque_packet.append((~checksum) & 0xFF)
            
            # Send torque command
            ser.write(torque_packet)
            time.sleep(0.05)
            
            print(f"Torque disabled for motor {motor_id}")
        
        # Close the port
        ser.close()
        print(f"\nClosed {port}")
        
        print("\nMovement test complete!")
        print("Did you see the follower arm move the gripper and shoulder?")
        print("If yes, the follower arm is working correctly on COM4.")
        print("If no, there may be issues with the power or motor connections.")
        
        return True
        
    except Exception as e:
        print(f"Error moving follower arm: {e}")
        return False

if __name__ == "__main__":
    print("=== Follower Arm Movement Test ===")
    print("This script will try to move the follower arm on COM4")
    print("Watch the arm to see if it responds to movement commands")
    
    move_follower_arm("COM4")

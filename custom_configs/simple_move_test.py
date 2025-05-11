import sys
import os
import time
import serial

def test_move_motor(port="COM4", motor_id=6):
    """Simple test to move one motor on the specified port"""
    print(f"Testing movement of motor {motor_id} on {port}")
    
    try:
        # Open the serial port
        ser = serial.Serial(port, 1000000, timeout=0.5)
        print(f"Successfully opened {port}")
        
        # Enable torque on the motor
        print(f"Enabling torque on motor {motor_id}")
        torque_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 40, 1])
        checksum = 0
        for b in torque_packet[2:-1]:
            checksum += b
        torque_packet.append((~checksum) & 0xFF)
        
        ser.write(torque_packet)
        time.sleep(0.1)
        
        # Read current position
        print(f"Reading current position of motor {motor_id}")
        read_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x02, 56, 0x02])
        checksum = 0
        for b in read_packet[2:-1]:
            checksum += b
        read_packet.append((~checksum) & 0xFF)
        
        ser.write(read_packet)
        time.sleep(0.1)
        
        current_position = 2048  # Default middle position
        if ser.in_waiting:
            response = ser.read(ser.in_waiting)
            if len(response) >= 8 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                current_position = response[5] + (response[6] << 8)
                print(f"Current position of motor {motor_id}: {current_position}")
            else:
                print(f"Invalid response when reading position: {' '.join([hex(b) for b in response])}")
        else:
            print("No response when reading position")
        
        # Move forward
        forward_position = min(4000, current_position + 300)
        print(f"Moving motor {motor_id} forward to position {forward_position}")
        
        write_packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 42, forward_position & 0xFF, (forward_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        ser.write(write_packet)
        time.sleep(1.0)  # Wait for movement
        
        # Move backward
        backward_position = max(0, current_position - 300)
        print(f"Moving motor {motor_id} backward to position {backward_position}")
        
        write_packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 42, backward_position & 0xFF, (backward_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        ser.write(write_packet)
        time.sleep(1.0)  # Wait for movement
        
        # Return to original position
        print(f"Returning motor {motor_id} to original position {current_position}")
        
        write_packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 42, current_position & 0xFF, (current_position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        ser.write(write_packet)
        time.sleep(1.0)  # Wait for movement
        
        # Disable torque
        print(f"Disabling torque on motor {motor_id}")
        torque_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 40, 0])
        checksum = 0
        for b in torque_packet[2:-1]:
            checksum += b
        torque_packet.append((~checksum) & 0xFF)
        
        ser.write(torque_packet)
        time.sleep(0.1)
        
        # Close the port
        ser.close()
        print(f"Closed {port}")
        
        print("\nMovement test complete!")
        print("Did you see the arm move?")
        print("If yes, the arm is working correctly.")
        print("If no, there may be issues with the power or motor connections.")
        
        return True
        
    except Exception as e:
        print(f"Error during movement test: {e}")
        return False

def test_all_motors():
    """Test movement of all motors"""
    print("=== Testing Movement of All Motors on COM4 ===")
    
    for motor_id in range(1, 7):
        print(f"\n--- Testing Motor {motor_id} ---")
        success = test_move_motor("COM4", motor_id)
        
        if not success:
            print(f"Failed to test motor {motor_id}")
            break
        
        # Wait between motor tests
        time.sleep(0.5)

if __name__ == "__main__":
    print("=== Simple Movement Test ===")
    print("This script will try to move motors on the arm connected to COM4")
    print("Watch the arm to see if it responds to movement commands")
    
    # Test the gripper (motor 6) first
    test_move_motor("COM4", 6)
    
    # Uncomment to test all motors
    # test_all_motors()

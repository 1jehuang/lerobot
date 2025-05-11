
import time
import sys
import os

# Add the project root to the path so we can import the lerobot package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lerobot.common.robot_devices.motors.feetech import FeetechServoController

def test_motor_connection():
    # Try leader arm on COM3
    print("Testing connection to leader arm on COM3...")
    try:
        controller = FeetechServoController(port="COM3", baudrate=1000000)
        print("Connected to COM3 successfully!")
        
        # Try to read motor IDs
        print("Scanning for motors on COM3...")
        for motor_id in range(1, 7):
            try:
                position = controller.get_present_position(motor_id)
                print(f"  Found motor ID {motor_id} at position: {position}")
            except Exception as e:
                print(f"  Motor ID {motor_id} not found or error: {str(e)}")
        
        controller.close()
    except Exception as e:
        print(f"Failed to connect to COM3: {str(e)}")
    
    # Try follower arm on COM4
    print("\nTesting connection to follower arm on COM4...")
    try:
        controller = FeetechServoController(port="COM4", baudrate=1000000)
        print("Connected to COM4 successfully!")
        
        # Try to read motor IDs
        print("Scanning for motors on COM4...")
        for motor_id in range(1, 7):
            try:
                position = controller.get_present_position(motor_id)
                print(f"  Found motor ID {motor_id} at position: {position}")
            except Exception as e:
                print(f"  Motor ID {motor_id} not found or error: {str(e)}")
        
        controller.close()
    except Exception as e:
        print(f"Failed to connect to COM4: {str(e)}")

if __name__ == "__main__":
    test_motor_connection()

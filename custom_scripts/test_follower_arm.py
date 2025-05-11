import sys
import time
import os
import signal
from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("\nExiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("Connecting to follower arm...")
    
    # Define motor configuration for follower arm
    follower_port = "COM4"  # Port for follower arm
    motor_ids = [1, 2, 3, 4, 5, 6]  # Motor IDs from 1 to 6
    
    try:
        # Connect to the motors bus
        motors_bus = FeetechMotorsBus(
            port=follower_port,
            baudrate=1000000,  # Default baudrate for these motors
            protocol_version=1  # Try protocol version 1
        )
        
        print(f"Connected to motors bus on {follower_port}")
        
        # Check if we can read from each motor
        print("Testing motor communication...")
        for motor_id in motor_ids:
            try:
                position = motors_bus.read_position(motor_id)
                print(f"Motor {motor_id} position: {position}")
            except Exception as e:
                print(f"Error reading from motor {motor_id}: {e}")
        
        # Test moving the gripper (motor 6)
        print("\nTesting gripper movement (Motor 6)...")
        
        # First, disable torque to allow movement
        try:
            motors_bus.write_torque_enable(6, False)
            print("Torque disabled for gripper")
            time.sleep(1)
            
            # Read current position
            current_pos = motors_bus.read_position(6)
            print(f"Current gripper position: {current_pos}")
            
            # Enable torque and move to a slightly different position
            motors_bus.write_torque_enable(6, True)
            print("Torque enabled for gripper")
            time.sleep(1)
            
            # Move to open position
            target_pos = 600  # This is an example position, may need adjustment
            print(f"Moving gripper to position {target_pos}...")
            motors_bus.write_position(6, target_pos)
            time.sleep(2)
            
            # Move to closed position
            target_pos = 400  # This is an example position, may need adjustment
            print(f"Moving gripper to position {target_pos}...")
            motors_bus.write_position(6, target_pos)
            time.sleep(2)
            
            # Return to original position
            print(f"Returning to original position {current_pos}...")
            motors_bus.write_position(6, current_pos)
            time.sleep(2)
            
            # Disable torque when done
            motors_bus.write_torque_enable(6, False)
            print("Torque disabled for gripper")
            
        except Exception as e:
            print(f"Error controlling gripper: {e}")
            
    except Exception as e:
        print(f"Error connecting to motors bus: {e}")
        return
    
    print("Test complete!")

if __name__ == "__main__":
    main()

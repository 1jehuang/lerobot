import sys
import time
import os
import signal
from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("\nExiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("Connecting to follower arm...")
    
    # Define motor configuration for follower arm
    follower_port = "COM4"  # Port for follower arm
    
    # Create motor configuration
    motors_config = {
        "shoulder_pan": (1, "sts3215"),
        "shoulder_lift": (2, "sts3215"),
        "elbow_flex": (3, "sts3215"),
        "wrist_flex": (4, "sts3215"),
        "wrist_roll": (5, "sts3215"),
        "gripper": (6, "sts3215")
    }
    
    config = FeetechMotorsBusConfig(
        port=follower_port,
        motors=motors_config
    )
    
    try:
        # Connect to the motors bus
        motors_bus = FeetechMotorsBus(config)
        motors_bus.connect()
        
        print(f"Connected to motors bus on {follower_port}")
        
        # Check if we can read from each motor
        print("Testing motor communication...")
        for motor_name, (motor_id, _) in motors_config.items():
            try:
                position = motors_bus.read("Present_Position", motor_name)
                print(f"Motor {motor_name} (ID: {motor_id}) position: {position}")
            except Exception as e:
                print(f"Error reading from motor {motor_name} (ID: {motor_id}): {e}")
        
        # Test moving the gripper (motor 6)
        print("\nTesting gripper movement...")
        
        # First, disable torque to allow movement
        try:
            motors_bus.write("Torque_Enable", 0, "gripper")
            print("Torque disabled for gripper")
            time.sleep(1)
            
            # Read current position
            current_pos = motors_bus.read("Present_Position", "gripper")
            print(f"Current gripper position: {current_pos}")
            
            # Enable torque and move to a slightly different position
            motors_bus.write("Torque_Enable", 1, "gripper")
            print("Torque enabled for gripper")
            time.sleep(1)
            
            # Move to a slightly open position
            new_pos = current_pos + 10  # Move 10 degrees more open
            print(f"Moving gripper to position {new_pos}...")
            motors_bus.write("Goal_Position", new_pos, "gripper")
            time.sleep(2)
            
            # Read position again
            new_current_pos = motors_bus.read("Present_Position", "gripper")
            print(f"New gripper position: {new_current_pos}")
            
            # Return to original position
            print(f"Returning to original position {current_pos}...")
            motors_bus.write("Goal_Position", current_pos, "gripper")
            time.sleep(2)
            
            # Disable torque when done
            motors_bus.write("Torque_Enable", 0, "gripper")
            print("Torque disabled for gripper")
            
        except Exception as e:
            print(f"Error controlling gripper: {e}")
        
        # Disconnect when done
        motors_bus.disconnect()
        print("Disconnected from motors bus")
            
    except Exception as e:
        print(f"Error: {e}")
        return
    
    print("Test complete!")

if __name__ == "__main__":
    main()

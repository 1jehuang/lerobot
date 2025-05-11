import sys
import time
from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig

def main():
    print("Starting gripper movement test...")
    
    # Define motor configuration for follower arm
    follower_port = "COM4"  # Port for follower arm
    
    # Create motor configuration - only include the gripper
    motors_config = {
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
        
        # Read initial gripper position
        try:
            initial_position = motors_bus.read("Present_Position", "gripper")[0]
            print(f"Initial gripper position: {initial_position}")
        except Exception as e:
            print(f"Error reading gripper position: {e}")
            initial_position = 2000  # Default value
        
        # Enable torque for gripper
        print("Enabling torque for gripper...")
        motors_bus.write("Torque_Enable", 1, "gripper")
        time.sleep(1)
        
        # Open gripper (increase position)
        print("Opening gripper...")
        open_position = initial_position + 200
        motors_bus.write("Goal_Position", open_position, "gripper")
        time.sleep(2)
        
        # Read current position
        current_position = motors_bus.read("Present_Position", "gripper")[0]
        print(f"Gripper position after opening: {current_position}")
        
        # Close gripper (decrease position)
        print("Closing gripper...")
        close_position = initial_position - 200
        motors_bus.write("Goal_Position", close_position, "gripper")
        time.sleep(2)
        
        # Read current position
        current_position = motors_bus.read("Present_Position", "gripper")[0]
        print(f"Gripper position after closing: {current_position}")
        
        # Return to initial position
        print("Returning to initial position...")
        motors_bus.write("Goal_Position", initial_position, "gripper")
        time.sleep(2)
        
        # Read final position
        final_position = motors_bus.read("Present_Position", "gripper")[0]
        print(f"Final gripper position: {final_position}")
        
        # Disable torque
        print("Disabling torque for gripper...")
        motors_bus.write("Torque_Enable", 0, "gripper")
        
        # Disconnect
        motors_bus.disconnect()
        print("Disconnected from motors bus")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("Gripper test complete!")

if __name__ == "__main__":
    main()

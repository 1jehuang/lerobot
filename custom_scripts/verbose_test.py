import sys
import time
from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig

def main():
    print("===== STARTING VERBOSE GRIPPER TEST =====")
    sys.stdout.flush()  # Force output to display
    
    try:
        print("Step 1: Creating motor configuration...")
        sys.stdout.flush()
        
        # Define motor configuration for follower arm - only include the gripper
        follower_port = "COM4"  # Port for follower arm
        motors_config = {
            "gripper": (6, "sts3215")
        }
        
        config = FeetechMotorsBusConfig(
            port=follower_port,
            motors=motors_config
        )
        
        print("Step 2: Connecting to motors bus...")
        sys.stdout.flush()
        
        # Connect to the motors bus
        motors_bus = FeetechMotorsBus(config)
        motors_bus.connect()
        
        print(f"Connected to motors bus on {follower_port}")
        sys.stdout.flush()
        
        print("Step 3: Reading initial gripper position...")
        sys.stdout.flush()
        
        # Read initial gripper position
        initial_position = motors_bus.read("Present_Position", "gripper")[0]
        print(f"Initial gripper position: {initial_position}")
        sys.stdout.flush()
        
        print("Step 4: Enabling torque for gripper...")
        sys.stdout.flush()
        
        # Enable torque for gripper
        motors_bus.write("Torque_Enable", 1, "gripper")
        print("Torque enabled")
        sys.stdout.flush()
        
        print("Waiting 3 seconds...")
        sys.stdout.flush()
        time.sleep(3)
        
        print("Step 5: Opening gripper...")
        sys.stdout.flush()
        
        # Open gripper (increase position)
        open_position = initial_position + 100
        motors_bus.write("Goal_Position", open_position, "gripper")
        print(f"Command sent to move to position {open_position}")
        sys.stdout.flush()
        
        print("Waiting 3 seconds...")
        sys.stdout.flush()
        time.sleep(3)
        
        print("Step 6: Reading current position...")
        sys.stdout.flush()
        
        # Read current position
        current_position = motors_bus.read("Present_Position", "gripper")[0]
        print(f"Gripper position after opening: {current_position}")
        sys.stdout.flush()
        
        print("Step 7: Closing gripper...")
        sys.stdout.flush()
        
        # Close gripper (decrease position)
        close_position = initial_position - 100
        motors_bus.write("Goal_Position", close_position, "gripper")
        print(f"Command sent to move to position {close_position}")
        sys.stdout.flush()
        
        print("Waiting 3 seconds...")
        sys.stdout.flush()
        time.sleep(3)
        
        print("Step 8: Reading current position...")
        sys.stdout.flush()
        
        # Read current position
        current_position = motors_bus.read("Present_Position", "gripper")[0]
        print(f"Gripper position after closing: {current_position}")
        sys.stdout.flush()
        
        print("Step 9: Returning to initial position...")
        sys.stdout.flush()
        
        # Return to initial position
        motors_bus.write("Goal_Position", initial_position, "gripper")
        print(f"Command sent to move to position {initial_position}")
        sys.stdout.flush()
        
        print("Waiting 3 seconds...")
        sys.stdout.flush()
        time.sleep(3)
        
        print("Step 10: Reading final position...")
        sys.stdout.flush()
        
        # Read final position
        final_position = motors_bus.read("Present_Position", "gripper")[0]
        print(f"Final gripper position: {final_position}")
        sys.stdout.flush()
        
        print("Step 11: Disabling torque...")
        sys.stdout.flush()
        
        # Disable torque
        motors_bus.write("Torque_Enable", 0, "gripper")
        print("Torque disabled")
        sys.stdout.flush()
        
        print("Step 12: Disconnecting...")
        sys.stdout.flush()
        
        # Disconnect
        motors_bus.disconnect()
        print("Disconnected from motors bus")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.stdout.flush()
    
    print("===== GRIPPER TEST COMPLETE =====")
    sys.stdout.flush()

if __name__ == "__main__":
    main()

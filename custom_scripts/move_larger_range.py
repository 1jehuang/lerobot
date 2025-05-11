import sys
import time
from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig

def main():
    print("===== TESTING LARGER JOINT MOVEMENTS (10% of range) =====")
    sys.stdout.flush()
    
    try:
        print("Step 1: Creating motor configuration...")
        sys.stdout.flush()
        
        # Define motor configuration for follower arm
        follower_port = "COM4"  # Port for follower arm
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
        
        print("Step 2: Connecting to motors bus...")
        sys.stdout.flush()
        
        # Connect to the motors bus
        motors_bus = FeetechMotorsBus(config)
        motors_bus.connect()
        
        print(f"Connected to motors bus on {follower_port}")
        sys.stdout.flush()
        
        print("Step 3: Reading initial positions for all motors...")
        sys.stdout.flush()
        
        # Read initial positions for all motors
        initial_positions = {}
        for motor_name in motors_config.keys():
            try:
                position = motors_bus.read("Present_Position", motor_name)[0]
                initial_positions[motor_name] = position
                print(f"Initial {motor_name} position: {position}")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error reading {motor_name} position: {e}")
                sys.stdout.flush()
                initial_positions[motor_name] = 0
        
        print("Step 4: Enabling torque for all motors...")
        sys.stdout.flush()
        
        # Enable torque for all motors
        for motor_name in motors_config.keys():
            try:
                motors_bus.write("Torque_Enable", 1, motor_name)
                print(f"Torque enabled for {motor_name}")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error enabling torque for {motor_name}: {e}")
                sys.stdout.flush()
        
        # Define the range for each joint
        # 10% of full range of motion (full range would be ~4000 steps for these motors)
        # Using approximately 400 steps which is about 10% of full range
        MOVE_AMOUNT = 400
        WAIT_TIME = 3  # More time to see the movement clearly
        
        # Test each motor one by one with larger movements
        for motor_name in motors_config.keys():
            print(f"\n===== TESTING {motor_name.upper()} =====")
            sys.stdout.flush()
            
            try:
                # Get initial position
                initial_pos = initial_positions[motor_name]
                
                # Move in positive direction (10% of range)
                print(f"Moving {motor_name} in positive direction...")
                sys.stdout.flush()
                motors_bus.write("Goal_Position", initial_pos + MOVE_AMOUNT, motor_name)
                print(f"Command sent to move to position {initial_pos + MOVE_AMOUNT}")
                sys.stdout.flush()
                
                print(f"Waiting {WAIT_TIME} seconds...")
                sys.stdout.flush()
                time.sleep(WAIT_TIME)
                
                # Read current position
                current_pos = motors_bus.read("Present_Position", motor_name)[0]
                print(f"{motor_name} position after positive move: {current_pos}")
                print(f"Moved {current_pos - initial_pos} steps from initial position")
                sys.stdout.flush()
                
                # Return to initial position
                print(f"Returning {motor_name} to initial position...")
                sys.stdout.flush()
                motors_bus.write("Goal_Position", initial_pos, motor_name)
                print(f"Command sent to move to position {initial_pos}")
                sys.stdout.flush()
                
                print(f"Waiting {WAIT_TIME} seconds...")
                sys.stdout.flush()
                time.sleep(WAIT_TIME)
                
                # Move in negative direction (10% of range)
                print(f"Moving {motor_name} in negative direction...")
                sys.stdout.flush()
                motors_bus.write("Goal_Position", initial_pos - MOVE_AMOUNT, motor_name)
                print(f"Command sent to move to position {initial_pos - MOVE_AMOUNT}")
                sys.stdout.flush()
                
                print(f"Waiting {WAIT_TIME} seconds...")
                sys.stdout.flush()
                time.sleep(WAIT_TIME)
                
                # Read current position
                current_pos = motors_bus.read("Present_Position", motor_name)[0]
                print(f"{motor_name} position after negative move: {current_pos}")
                print(f"Moved {initial_pos - current_pos} steps from initial position")
                sys.stdout.flush()
                
                # Return to initial position
                print(f"Returning {motor_name} to initial position...")
                sys.stdout.flush()
                motors_bus.write("Goal_Position", initial_pos, motor_name)
                print(f"Command sent to move to position {initial_pos}")
                sys.stdout.flush()
                
                print(f"Waiting {WAIT_TIME} seconds...")
                sys.stdout.flush()
                time.sleep(WAIT_TIME)
                
                # Read final position
                final_pos = motors_bus.read("Present_Position", motor_name)[0]
                print(f"Final {motor_name} position: {final_pos}")
                sys.stdout.flush()
                
            except Exception as e:
                print(f"Error testing {motor_name}: {e}")
                sys.stdout.flush()
        
        print("\nStep 5: Disabling torque for all motors...")
        sys.stdout.flush()
        
        # Disable torque for all motors
        for motor_name in motors_config.keys():
            try:
                motors_bus.write("Torque_Enable", 0, motor_name)
                print(f"Torque disabled for {motor_name}")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error disabling torque for {motor_name}: {e}")
                sys.stdout.flush()
        
        print("Step 6: Disconnecting...")
        sys.stdout.flush()
        
        # Disconnect
        motors_bus.disconnect()
        print("Disconnected from motors bus")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.stdout.flush()
    
    print("===== LARGER JOINT MOVEMENTS TEST COMPLETE =====")
    sys.stdout.flush()

if __name__ == "__main__":
    main()

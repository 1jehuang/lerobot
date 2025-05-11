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
    print("Starting automated movement of follower arm...")
    
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
        
        # Read and store initial positions
        initial_positions = {}
        for motor_name in motors_config.keys():
            try:
                position = motors_bus.read("Present_Position", motor_name)[0]
                initial_positions[motor_name] = position
                print(f"Initial {motor_name} position: {position}")
            except Exception as e:
                print(f"Error reading from {motor_name}: {e}")
                initial_positions[motor_name] = 0
        
        # Enable torque for all motors
        print("\nEnabling torque for all motors...")
        for motor_name in motors_config.keys():
            motors_bus.write("Torque_Enable", 1, motor_name)
        time.sleep(1)
        
        # Move each motor one by one
        try:
            # 1. First, let's move the gripper
            print("\nMoving gripper...")
            # Open gripper
            motors_bus.write("Goal_Position", initial_positions["gripper"] + 100, "gripper")
            time.sleep(2)
            # Close gripper
            motors_bus.write("Goal_Position", initial_positions["gripper"] - 100, "gripper")
            time.sleep(2)
            # Return to initial position
            motors_bus.write("Goal_Position", initial_positions["gripper"], "gripper")
            time.sleep(2)
            
            # 2. Move wrist roll
            print("\nMoving wrist roll...")
            motors_bus.write("Goal_Position", initial_positions["wrist_roll"] + 200, "wrist_roll")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["wrist_roll"] - 200, "wrist_roll")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["wrist_roll"], "wrist_roll")
            time.sleep(2)
            
            # 3. Move wrist flex
            print("\nMoving wrist flex...")
            motors_bus.write("Goal_Position", initial_positions["wrist_flex"] + 200, "wrist_flex")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["wrist_flex"] - 200, "wrist_flex")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["wrist_flex"], "wrist_flex")
            time.sleep(2)
            
            # 4. Move elbow flex
            print("\nMoving elbow flex...")
            motors_bus.write("Goal_Position", initial_positions["elbow_flex"] + 200, "elbow_flex")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["elbow_flex"] - 200, "elbow_flex")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["elbow_flex"], "elbow_flex")
            time.sleep(2)
            
            # 5. Move shoulder lift
            print("\nMoving shoulder lift...")
            motors_bus.write("Goal_Position", initial_positions["shoulder_lift"] + 200, "shoulder_lift")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["shoulder_lift"] - 200, "shoulder_lift")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["shoulder_lift"], "shoulder_lift")
            time.sleep(2)
            
            # 6. Move shoulder pan
            print("\nMoving shoulder pan...")
            motors_bus.write("Goal_Position", initial_positions["shoulder_pan"] + 200, "shoulder_pan")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["shoulder_pan"] - 200, "shoulder_pan")
            time.sleep(2)
            motors_bus.write("Goal_Position", initial_positions["shoulder_pan"], "shoulder_pan")
            time.sleep(2)
            
            # Now move multiple motors simultaneously to create a waving motion
            print("\nPerforming wave motion...")
            # Wave position 1
            motors_bus.write("Goal_Position", initial_positions["shoulder_lift"] - 100, "shoulder_lift")
            motors_bus.write("Goal_Position", initial_positions["elbow_flex"] + 200, "elbow_flex")
            motors_bus.write("Goal_Position", initial_positions["wrist_flex"] - 150, "wrist_flex")
            time.sleep(2)
            
            # Wave position 2
            motors_bus.write("Goal_Position", initial_positions["shoulder_lift"] - 150, "shoulder_lift")
            motors_bus.write("Goal_Position", initial_positions["elbow_flex"] + 250, "elbow_flex")
            motors_bus.write("Goal_Position", initial_positions["wrist_flex"] - 200, "wrist_flex")
            time.sleep(2)
            
            # Wave position 1 again
            motors_bus.write("Goal_Position", initial_positions["shoulder_lift"] - 100, "shoulder_lift")
            motors_bus.write("Goal_Position", initial_positions["elbow_flex"] + 200, "elbow_flex")
            motors_bus.write("Goal_Position", initial_positions["wrist_flex"] - 150, "wrist_flex")
            time.sleep(2)
            
            # Return to initial positions
            print("\nReturning to initial positions...")
            for motor_name, position in initial_positions.items():
                motors_bus.write("Goal_Position", position, motor_name)
            time.sleep(3)
            
        except Exception as e:
            print(f"Error during movement sequence: {e}")
        
        # Disable torque for all motors when done
        print("\nDisabling torque for all motors...")
        for motor_name in motors_config.keys():
            motors_bus.write("Torque_Enable", 0, motor_name)
        
        # Disconnect when done
        motors_bus.disconnect()
        print("Disconnected from motors bus")
            
    except Exception as e:
        print(f"Error: {e}")
        return
    
    print("Movement sequence complete!")

if __name__ == "__main__":
    main()

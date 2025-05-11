import sys
import time
import os
import signal
import keyboard
import threading
from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig

# Flag to control the main loop
running = True

# Step size for movement
STEP_SIZE = 20  # Degrees

# Motor names and keys for controlling
MOTOR_KEYS = {
    "shoulder_pan": {"inc": "q", "dec": "a"},
    "shoulder_lift": {"inc": "w", "dec": "s"},
    "elbow_flex": {"inc": "e", "dec": "d"},
    "wrist_flex": {"inc": "r", "dec": "f"},
    "wrist_roll": {"inc": "t", "dec": "g"},
    "gripper": {"inc": "y", "dec": "h"}
}

def signal_handler(sig, frame):
    global running
    print("\nExiting...")
    running = False

def print_controls():
    """Print the control scheme for the user."""
    print("\n==== KEYBOARD CONTROLS ====")
    print("ESC: Exit program")
    print("SPACE: Toggle torque for all motors (ON/OFF)")
    print("HOME: Return all motors to home position")
    
    for motor_name, keys in MOTOR_KEYS.items():
        print(f"{motor_name.upper()}: {keys['inc']} (increase), {keys['dec']} (decrease)")
    
    print("==========================\n")

def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    
    # Set up motor configuration
    follower_port = "COM4"  # Port for follower arm
    motors_config = {
        "shoulder_pan": (1, "sts3215"),
        "shoulder_lift": (2, "sts3215"),
        "elbow_flex": (3, "sts3215"),
        "wrist_flex": (4, "sts3215"),
        "wrist_roll": (5, "sts3215"),
        "gripper": (6, "sts3215")
    }
    
    # Track the current positions
    current_positions = {}
    torque_enabled = False
    
    try:
        # Create config and connect
        config = FeetechMotorsBusConfig(
            port=follower_port,
            motors=motors_config
        )
        
        motors_bus = FeetechMotorsBus(config)
        motors_bus.connect()
        
        print(f"Connected to follower arm on {follower_port}")
        
        # Read initial positions
        for motor_name in motors_config.keys():
            try:
                position = motors_bus.read("Present_Position", motor_name)[0]
                current_positions[motor_name] = position
                print(f"{motor_name}: {position}")
            except Exception as e:
                print(f"Error reading from {motor_name}: {e}")
                current_positions[motor_name] = 0
        
        # Print controls
        print_controls()
        
        # Main control loop
        while running:
            # Check for keyboard input
            if keyboard.is_pressed('esc'):
                print("ESC pressed. Exiting...")
                running = False
                break
                
            # Toggle torque
            if keyboard.is_pressed('space'):
                torque_enabled = not torque_enabled
                print(f"Torque {'enabled' if torque_enabled else 'disabled'} for all motors")
                
                for motor_name in motors_config.keys():
                    motors_bus.write("Torque_Enable", int(torque_enabled), motor_name)
                
                # Wait to avoid multiple toggles
                time.sleep(0.3)
                
            # Home position
            if keyboard.is_pressed('home'):
                if torque_enabled:
                    print("Returning to home positions...")
                    for motor_name, initial_pos in current_positions.items():
                        motors_bus.write("Goal_Position", initial_pos, motor_name)
                else:
                    print("Enable torque first to return home")
                
                # Wait to avoid multiple triggers
                time.sleep(0.3)
            
            # Check for motor controls
            for motor_name, keys in MOTOR_KEYS.items():
                if keyboard.is_pressed(keys['inc']):
                    if torque_enabled:
                        # Read current position and increment it
                        try:
                            position = motors_bus.read("Present_Position", motor_name)[0]
                            new_position = position + STEP_SIZE
                            motors_bus.write("Goal_Position", new_position, motor_name)
                            print(f"Moving {motor_name} to {new_position}")
                        except Exception as e:
                            print(f"Error moving {motor_name}: {e}")
                    else:
                        print("Enable torque first to move motors")
                    
                    # Small delay to avoid multiple keypresses
                    time.sleep(0.1)
                    
                elif keyboard.is_pressed(keys['dec']):
                    if torque_enabled:
                        # Read current position and decrement it
                        try:
                            position = motors_bus.read("Present_Position", motor_name)[0]
                            new_position = position - STEP_SIZE
                            motors_bus.write("Goal_Position", new_position, motor_name)
                            print(f"Moving {motor_name} to {new_position}")
                        except Exception as e:
                            print(f"Error moving {motor_name}: {e}")
                    else:
                        print("Enable torque first to move motors")
                    
                    # Small delay to avoid multiple keypresses
                    time.sleep(0.1)
            
            # Small delay to reduce CPU usage
            time.sleep(0.05)
                
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Make sure to disable torque and disconnect when exiting
        if 'motors_bus' in locals():
            try:
                for motor_name in motors_config.keys():
                    motors_bus.write("Torque_Enable", 0, motor_name)
                print("Disabled torque for all motors")
                
                motors_bus.disconnect()
                print("Disconnected from follower arm")
            except Exception as e:
                print(f"Error during shutdown: {e}")

if __name__ == "__main__":
    main()

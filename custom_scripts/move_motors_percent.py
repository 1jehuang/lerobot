import sys
import time
import numpy as np
from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus, JointOutOfRangeError
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig

def main():
    print("===== MOVING ALL MOTORS BY 2% RANGE OF MOTION WITH SAFETY CONTROLS =====")
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
          # Set slower acceleration and speed for safety
        print("Setting acceleration and speed limits for safety...")
        sys.stdout.flush()
        
        for motor_name in motors_config.keys():
            try:
                # Set acceleration to a lower value (normal is 254)
                motors_bus.write("Acceleration", 100, motor_name)
                # Lock parameter needs to be 0 to allow writing certain values
                motors_bus.write("Lock", 0, motor_name)
                print(f"Safety limits set for {motor_name}")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error setting safety parameters for {motor_name}: {e}")
                sys.stdout.flush()
                
        # Motor range is approximately ±180 degrees = 360 degrees total
        # 2% of range is 7.2 degrees or about 82 steps (with 4096 steps for 360 degrees)
        MOVE_AMOUNT = 82  # 2% of range (approximately 7.2 degrees)
        WAIT_TIME = 4  # Longer wait time for slower movements
        
        # Function to check for joint limits
        def check_joint_limits(motor_name, target_position):
            # Read current position to have a reference point
            try:
                current_pos = motors_bus.read("Present_Position", motor_name)[0]
                # Calculate absolute change
                change = abs(current_pos - target_position)
                
                # If movement is too large (more than 25% of range = ~1024 steps), it might be dangerous
                if change > 1024:
                    print(f"WARNING: Movement for {motor_name} exceeds safe limits! Requested change: {change} steps")
                    return False
                
                # Check if the position is within the motor's expected range
                # STS3215 has a range of 0-4095 (absolute physical limits)
                if target_position < 0 or target_position > 4095:
                    print(f"WARNING: Target position {target_position} for {motor_name} is outside motor range (0-4095)")
                    return False
                    
                # Additional check for load or current if approaching limits
                # We can read Present_Load as an indicator of strain on the motor
                try:
                    current_load = motors_bus.read("Present_Load", motor_name)[0]
                    if current_load > 200:  # High load indicates resistance
                        print(f"WARNING: {motor_name} is under high load ({current_load}). Movement may be unsafe.")
                        return False
                except Exception:
                    pass  # If read fails, continue with other checks
                    
                return True
            except Exception as e:
                print(f"Error checking limits for {motor_name}: {e}")
                return False
                
        print("\n===== MOVING ALL MOTORS FORWARD BY 2% =====")
        sys.stdout.flush()
          # First, move all motors forward by 2%
        for motor_name in motors_config.keys():
            initial_pos = initial_positions[motor_name]
            new_pos = initial_pos + MOVE_AMOUNT
            
            # Safety check before moving
            if check_joint_limits(motor_name, new_pos):
                print(f"Moving {motor_name} forward to position {new_pos} (from {initial_pos})...")
                sys.stdout.flush()
                try:
                    motors_bus.write("Goal_Position", new_pos, motor_name)
                except JointOutOfRangeError as e:
                    print(f"SAFETY ALERT: {e}")
                    print(f"Skipping movement for {motor_name}")
                    sys.stdout.flush()
            else:
                print(f"Skipping movement for {motor_name} due to safety limits")
                sys.stdout.flush()
              # Wait for all motors to reach their positions with monitoring
        print(f"Waiting {WAIT_TIME} seconds for all motors to reach forward positions...")
        sys.stdout.flush()
        
        # Monitor movement with periodic checks
        start_time = time.time()
        while time.time() - start_time < WAIT_TIME:
            # Check every half second
            time.sleep(0.5)
            
            # Check if all motors have completed their movements
            all_stopped = True
            for motor_name in motors_config.keys():
                try:
                    # Check if motor is still moving
                    moving = motors_bus.read("Moving", motor_name)[0]
                    current_pos = motors_bus.read("Present_Position", motor_name)[0]
                    
                    # Also check current load as a safety measure
                    try:
                        current_load = motors_bus.read("Present_Load", motor_name)[0]
                        if current_load > 250:  # Extremely high load
                            print(f"WARNING: {motor_name} experiencing high load ({current_load})! Emergency stop.")
                            motors_bus.write("Goal_Position", current_pos, motor_name)  # Stop at current position
                        elif current_load > 150:  # Moderately high load
                            print(f"Caution: {motor_name} under elevated load: {current_load}")
                    except Exception:
                        pass
                        
                    if moving != 0:
                        all_stopped = False
                        
                except Exception as e:
                    print(f"Error checking motor {motor_name} status: {e}")
                    all_stopped = False
            
            # If all motors have stopped moving, we can break early
            if all_stopped:
                print("All motors have completed their movements")
                break
                
        # Ensure we've waited the minimum time regardless
        remaining = WAIT_TIME - (time.time() - start_time)
        if remaining > 0:
            time.sleep(remaining)
        
        # Read and display current positions
        for motor_name in motors_config.keys():
            try:
                current_pos = motors_bus.read("Present_Position", motor_name)[0]
                print(f"{motor_name} current position: {current_pos}")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error reading {motor_name} position: {e}")
                sys.stdout.flush()
                  print("\n===== MOVING ALL MOTORS BACKWARD BY 4% =====")
        sys.stdout.flush()
        
        # Now move all motors backward by 4% (from +2% to -2%)
        for motor_name in motors_config.keys():
            initial_pos = initial_positions[motor_name]
            new_pos = initial_pos - MOVE_AMOUNT
            
            # Safety check before moving
            if check_joint_limits(motor_name, new_pos):
                print(f"Moving {motor_name} backward to position {new_pos} (from {motors_bus.read('Present_Position', motor_name)[0]})...")
                sys.stdout.flush()
                try:
                    motors_bus.write("Goal_Position", new_pos, motor_name)
                except JointOutOfRangeError as e:
                    print(f"SAFETY ALERT: {e}")
                    print(f"Skipping movement for {motor_name}")
                    sys.stdout.flush()
            else:
                print(f"Skipping movement for {motor_name} due to safety limits")
                sys.stdout.flush()
            
        # Wait for all motors to reach their positions
        print(f"Waiting {WAIT_TIME} seconds for all motors to reach backward positions...")
        sys.stdout.flush()
        time.sleep(WAIT_TIME)
        
        # Read and display current positions
        for motor_name in motors_config.keys():
            try:
                current_pos = motors_bus.read("Present_Position", motor_name)[0]
                print(f"{motor_name} current position: {current_pos}")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error reading {motor_name} position: {e}")
                sys.stdout.flush()
          print("\n===== RETURNING ALL MOTORS TO INITIAL POSITIONS =====")
        sys.stdout.flush()
        
        # Finally, return all motors to their initial positions
        for motor_name in motors_config.keys():
            initial_pos = initial_positions[motor_name]
            
            # Safety check before moving back to initial position
            if check_joint_limits(motor_name, initial_pos):
                print(f"Returning {motor_name} to initial position {initial_pos}...")
                sys.stdout.flush()
                try:
                    motors_bus.write("Goal_Position", initial_pos, motor_name)
                except JointOutOfRangeError as e:
                    print(f"SAFETY ALERT: {e}")
                    print(f"Failed to return {motor_name} to initial position")
                    sys.stdout.flush()
            else:
                print(f"WARNING: Cannot safely return {motor_name} to initial position")
                sys.stdout.flush()
            
        # Wait for all motors to reach their initial positions
        print(f"Waiting {WAIT_TIME} seconds for all motors to return to initial positions...")
        sys.stdout.flush()
        time.sleep(WAIT_TIME)
        
        # Read and display final positions
        for motor_name in motors_config.keys():
            try:
                current_pos = motors_bus.read("Present_Position", motor_name)[0]
                print(f"{motor_name} final position: {current_pos}")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error reading {motor_name} position: {e}")
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
        
        # Disconnect from the motors bus
        motors_bus.disconnect()
        print("\nDisconnected from motors bus")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    main()

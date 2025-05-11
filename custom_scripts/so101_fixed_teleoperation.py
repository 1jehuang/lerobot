"""
SO-101 Fixed Teleoperation Script

This script ensures the follower arm moves properly by:
1. Calibrating position offsets between arms
2. Configuring advanced servo motor settings
3. Providing reliable reset to rest position

Usage:
    python so101_fixed_teleoperation.py

Keyboard controls:
    ESC: Exit program
    SPACE: Toggle teleoperation on/off
    R: Reset to rest/home position
    D: Toggle debug mode
    T: Toggle torque on all motors
    S: Show status of all motors
    C: Calibrate offset between leader and follower
    A: Configure advanced motor settings
    F: Test follower movement
    V: Fix specific registers for SO-101 servos
    1-6: Toggle individual motor torque
"""

import sys
import os
import time
import keyboard  # pip install keyboard
import signal
import threading
import numpy as np

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import scservo_sdk as scs
    print("Successfully imported scservo_sdk")
except ImportError:
    print("Failed to import scservo_sdk. Make sure it's installed.")
    sys.exit(1)

# Port settings
LEADER_PORT = "COM3"
FOLLOWER_PORT = "COM4"
BAUDRATE = 1000000
PROTOCOL = 0  # Protocol 0 for SCServo SCS

# Initialize port handlers
leader_port_handler = scs.PortHandler(LEADER_PORT)
leader_packet_handler = scs.PacketHandler(PROTOCOL)

follower_port_handler = scs.PortHandler(FOLLOWER_PORT)
follower_packet_handler = scs.PacketHandler(PROTOCOL)

# Control parameters
UPDATE_FREQUENCY = 0.05  # seconds (50ms update rate)
MOTOR_IDS = list(range(1, 7))  # Motors 1-6
DEBUG_MODE = False
teleoperation_active = True
position_offsets = [0, 0, 0, 0, 0, 0]  # Calibration offsets between leader and follower
calibration_done = False  # Flag to indicate if calibration was performed

# Safe positions for initialization - Center position at 2048
SAFE_POSITIONS = [2048, 2048, 2048, 2048, 2048, 2048]  

# Rest position - More natural arm position
REST_POSITIONS = [2048, 2700, 1500, 1800, 2048, 2048]  # Adjusted for a comfortable resting pose

# Communication retries
MAX_RETRIES = 3
RETRY_DELAY = 0.1  # seconds

# Motor names for better readability
MOTOR_NAMES = {
    1: "Shoulder Pan",
    2: "Shoulder Lift",
    3: "Elbow Flex",
    4: "Wrist Flex",
    5: "Wrist Roll",
    6: "Gripper"
}

# Lock for thread safety
lock = threading.Lock()

def signal_handler(sig, frame):
    """Clean up on exit"""
    print("\nExiting program...")
    disable_all_motors(follower_port_handler, follower_packet_handler)
    leader_port_handler.closePort()
    follower_port_handler.closePort()
    sys.exit(0)

def open_ports():
    """Open communication ports for both arms"""
    # Open leader port
    try:
        if leader_port_handler.openPort():
            print(f"✓ Successfully opened leader port {LEADER_PORT}")
        else:
            print(f"✗ Failed to open leader port {LEADER_PORT}")
            return False

        if leader_port_handler.setBaudRate(BAUDRATE):
            print(f"✓ Changed leader baudrate to {BAUDRATE}")
        else:
            print(f"✗ Failed to change leader baudrate")
            leader_port_handler.closePort()
            return False
    except Exception as e:
        print(f"✗ Error with leader port: {e}")
        return False

    # Open follower port
    try:
        if follower_port_handler.openPort():
            print(f"✓ Successfully opened follower port {FOLLOWER_PORT}")
        else:
            print(f"✗ Failed to open follower port {FOLLOWER_PORT}")
            leader_port_handler.closePort()
            return False

        if follower_port_handler.setBaudRate(BAUDRATE):
            print(f"✓ Changed follower baudrate to {BAUDRATE}")
        else:
            print(f"✗ Failed to change follower baudrate")
            leader_port_handler.closePort()
            follower_port_handler.closePort()
            return False
    except Exception as e:
        print(f"✗ Error with follower port: {e}")
        leader_port_handler.closePort()
        return False

    return True

def read_motor_positions(port_handler, packet_handler, motor_ids):
    """Read position of multiple motors"""
    positions = []
    error_count = 0

    for motor_id in motor_ids:
        try:
            position, result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)  # Read present position (address 56)
            if result == scs.COMM_SUCCESS:
                positions.append(position)
                if DEBUG_MODE:
                    print(f"Read motor {motor_id}: {position}")
            else:
                error_msg = packet_handler.getTxRxResult(result)
                error_count += 1
                if DEBUG_MODE:
                    print(f"Failed to read position from motor {motor_id}: {error_msg}")
                positions.append(2048)  # Use center position as fallback
        except Exception as e:
            if DEBUG_MODE:
                print(f"Exception reading motor {motor_id}: {e}")
            positions.append(2048)
            error_count += 1

    if error_count > 0 and DEBUG_MODE:
        print(f"Warning: {error_count}/{len(motor_ids)} motor reads failed")

    return positions

def move_motors(port_handler, packet_handler, motor_ids, positions):
    """Move multiple motors to specified positions"""
    success_count = 0
    for motor_id, position in zip(motor_ids, positions):
        if not is_motor_torque_enabled(port_handler, packet_handler, motor_id):
            if DEBUG_MODE:
                print(f"Motor {motor_id} skipped (torque disabled)")
            continue

        # Ensure position is within valid range
        safe_position = max(0, min(4095, int(position)))

        try:
            # Write goal position (address 60)
            result, error = packet_handler.write2ByteTxRx(port_handler, motor_id, 60, safe_position)
            if result == scs.COMM_SUCCESS:
                success_count += 1
                if DEBUG_MODE:
                    print(f"Motor {motor_id} commanded to position {safe_position}")
            else:
                error_msg = packet_handler.getTxRxResult(result)
                if DEBUG_MODE:
                    print(f"Failed to write position to motor {motor_id}: {error_msg}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"Exception moving motor {motor_id}: {e}")

    if DEBUG_MODE and success_count != len(motor_ids):
        print(f"Only {success_count}/{len(motor_ids)} motors were successfully moved")

    return success_count == len(motor_ids)

def verify_movement(port_handler, packet_handler, motor_id, target_position, tolerance=50):
    """Verify that a motor actually moved to target position"""
    time.sleep(0.2)  # Wait a bit for movement
    try:
        position, result, _ = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)
        if result == scs.COMM_SUCCESS:
            difference = abs(position - target_position)
            if difference <= tolerance:
                if DEBUG_MODE:
                    print(f"Motor {motor_id} successfully moved to {position} (target: {target_position})")
                return True
            else:
                print(f"Motor {motor_id} at {position}, off target by {difference} (target: {target_position})")
                return False
    except Exception as e:
        if DEBUG_MODE:
            print(f"Exception verifying movement of motor {motor_id}: {e}")
    return False

def is_motor_torque_enabled(port_handler, packet_handler, motor_id):
    """Check if torque is enabled for a specific motor"""
    try:
        torque, result, _ = packet_handler.read1ByteTxRx(port_handler, motor_id, 50)  # Address 50 = Torque Enable
        if result == scs.COMM_SUCCESS:
            return torque == 1
        else:
            if DEBUG_MODE:
                print(f"Failed to read torque status from motor {motor_id}")
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error checking motor {motor_id} torque: {e}")
    return False

def toggle_motor_torque(port_handler, packet_handler, motor_id):
    """Toggle torque for a specific motor"""
    is_enabled = is_motor_torque_enabled(port_handler, packet_handler, motor_id)
    new_state = 0 if is_enabled else 1
    try:
        result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 50, new_state)
        if result == scs.COMM_SUCCESS:
            status = "enabled" if new_state == 1 else "disabled"
            print(f"Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}) torque {status}")
            return True
        else:
            print(f"Failed to toggle torque on motor {motor_id}")
            return False
    except Exception as e:
        print(f"Error toggling motor {motor_id} torque: {e}")
        return False

def enable_all_motors(port_handler, packet_handler):
    """Enable torque for all motors"""
    print("Enabling torque for all follower motors...")
    success = True
    for motor_id in MOTOR_IDS:
        try:
            # Torque enable (address 50)
            result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 50, 1)
            if result != scs.COMM_SUCCESS:
                error_msg = packet_handler.getTxRxResult(result)
                print(f"Failed to enable torque on motor {motor_id}: {error_msg}")
                success = False
        except Exception as e:
            print(f"Exception enabling motor {motor_id}: {e}")
            success = False

    if success:
        print("All motors enabled successfully")
    else:
        print("WARNING: Some motors could not be enabled")

    return success

def disable_all_motors(port_handler, packet_handler):
    """Disable torque for all motors"""
    print("Disabling torque for all motors...")
    for motor_id in MOTOR_IDS:
        try:
            # Torque disable (address 50)
            packet_handler.write1ByteTxRx(port_handler, motor_id, 50, 0)
        except Exception:
            pass  # Ignore errors during shutdown

def toggle_all_motors_torque(port_handler, packet_handler):
    """Toggle torque for all motors"""
    # Check current state of first motor
    is_enabled = is_motor_torque_enabled(port_handler, packet_handler, MOTOR_IDS[0])
    new_state = 0 if is_enabled else 1

    status_word = "Disabling" if is_enabled else "Enabling"
    print(f"{status_word} torque for all follower motors...")

    for motor_id in MOTOR_IDS:
        try:
            result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 50, new_state)
            if result != scs.COMM_SUCCESS:
                print(f"Failed to set torque on motor {motor_id}")
        except Exception as e:
            print(f"Error setting motor {motor_id} torque: {e}")

    # Verify torque was actually set
    time.sleep(0.2)
    verify_torque_status(port_handler, packet_handler)

def verify_torque_status(port_handler, packet_handler):
    """Verify torque status of all motors"""
    print("\n--- Motor Torque Status ---")
    for motor_id in MOTOR_IDS:
        try:
            is_enabled = is_motor_torque_enabled(port_handler, packet_handler, motor_id)
            status = "ENABLED" if is_enabled else "DISABLED"
            print(f"Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}): Torque {status}")
        except Exception as e:
            print(f"Could not verify motor {motor_id} torque: {e}")

def show_motor_status():
    """Display detailed status of all motors"""
    print("\n=== FOLLOWER ARM MOTOR STATUS ===")
    for motor_id in MOTOR_IDS:
        try:
            # Read position
            position, pos_result, _ = follower_packet_handler.read2ByteTxRx(follower_port_handler, motor_id, 56)

            # Read torque status
            torque, torque_result, _ = follower_packet_handler.read1ByteTxRx(follower_port_handler, motor_id, 50)

            # Read voltage
            voltage, voltage_result, _ = follower_packet_handler.read1ByteTxRx(follower_port_handler, motor_id, 62)

            # Read temperature
            temp, temp_result, _ = follower_packet_handler.read1ByteTxRx(follower_port_handler, motor_id, 63)

            print(f"Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}):")

            if pos_result == scs.COMM_SUCCESS:
                print(f"  Position: {position}")
            else:
                print(f"  Position: ERROR")

            if torque_result == scs.COMM_SUCCESS:
                status = "ENABLED" if torque == 1 else "DISABLED"
                print(f"  Torque: {status}")
            else:
                print(f"  Torque: ERROR")

            if voltage_result == scs.COMM_SUCCESS:
                print(f"  Voltage: {voltage/10.0}V")
            else:
                print(f"  Voltage: ERROR")

            if temp_result == scs.COMM_SUCCESS:
                print(f"  Temperature: {temp}°C")
            else:
                print(f"  Temperature: ERROR")

        except Exception as e:
            print(f"Error reading status of motor {motor_id}: {e}")

    print("================================")

def calibrate_offset():
    """Calibrate offset between leader and follower positions"""
    print("\n=== Calibrating Position Offsets ===")
    global position_offsets, calibration_done
    
    print("Hold both arms in similar positions for accurate calibration...")
    print("Reading current positions from both arms...")

    # Read positions with retry to ensure good readings
    leader_positions = None
    follower_positions = None
    
    for attempt in range(MAX_RETRIES):
        try:
            leader_attempt = read_motor_positions(leader_port_handler, leader_packet_handler, MOTOR_IDS)
            follower_attempt = read_motor_positions(follower_port_handler, follower_packet_handler, MOTOR_IDS)
            
            # Verify readings are valid (not all center positions which would be default)
            if all(pos != 0 for pos in leader_attempt) and all(pos != 0 for pos in follower_attempt):
                leader_positions = leader_attempt
                follower_positions = follower_attempt
                break
        except Exception as e:
            print(f"Calibration read attempt {attempt+1} failed: {e}")
            time.sleep(RETRY_DELAY)
    
    if leader_positions is None or follower_positions is None:
        print("Failed to get reliable position readings for calibration.")
        return False

    # Calculate offsets (follower - leader)
    position_offsets = [f - l for f, l in zip(follower_positions, leader_positions)]
    calibration_done = True

    print("Calibrated offsets: ")
    for i, offset in enumerate(position_offsets):
        motor_id = i + 1
        print(f"Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}): {offset}")

    print("Calibration complete!")
    print("Now you can use teleoperation - move the leader arm and the follower will mimic it.")
    return True

def test_follower_movement():
    """Test if the follower arm can move at all"""
    print("\n=== Testing Follower Movement ===")

    # First verify torque is enabled
    print("Ensuring torque is enabled...")
    enable_all_motors(follower_port_handler, follower_packet_handler)

    # Try to move each motor slightly
    for motor_id in MOTOR_IDS:
        try:
            print(f"Testing motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")

            # Read current position
            current_pos, pos_result, _ = follower_packet_handler.read2ByteTxRx(follower_port_handler, motor_id, 56)

            if pos_result != scs.COMM_SUCCESS:
                print(f"  Could not read position of motor {motor_id}")
                continue

            # Move +100 steps
            target_pos = (current_pos + 100) % 4096
            print(f"  Moving from {current_pos} to {target_pos}...")

            move_result, _ = follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, 60, target_pos)

            if move_result != scs.COMM_SUCCESS:
                print(f"  Failed to send move command to motor {motor_id}")
                continue

            # Wait and verify
            time.sleep(0.5)
            new_pos, new_pos_result, _ = follower_packet_handler.read2ByteTxRx(follower_port_handler, motor_id, 56)

            if new_pos_result != scs.COMM_SUCCESS:
                print(f"  Failed to read new position of motor {motor_id}")
                continue

            diff = abs(new_pos - target_pos)
            if diff < 20:
                print(f"  SUCCESS: Motor moved to {new_pos} (target: {target_pos})")
            else:
                print(f"  FAILURE: Motor only moved to {new_pos} (target: {target_pos}, diff: {diff})")

            # Return to original position
            follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, 60, current_pos)
            time.sleep(0.5)

        except Exception as e:
            print(f"  Error testing motor {motor_id}: {e}")

    print("Test complete!")

def print_instructions():
    """Print the keyboard controls"""
    print("\n=== SO-101 Teleoperation Controls ===")
    print("ESC: Exit program")
    print("SPACE: Toggle teleoperation (ON/OFF)")
    print("R: Reset to rest position")
    print("A: Configure advanced motor settings")
    print("V: Fix SO-101 specific registers")
    print("D: Toggle debug information")
    print("T: Toggle torque on all follower motors")
    print("S: Show status of all follower motors")
    print("C: Calibrate position offsets")
    print("F: Test follower movement")
    print("1-6: Toggle individual follower motor torque")
    print("=====================================\n")

def print_status(leader_positions, follower_positions, is_active):
    """Print current status"""
    status = "ACTIVE" if is_active else "PAUSED"
    print(f"\rTeleoperation: {status} | ", end="")

    for i, (leader_pos, follower_pos) in enumerate(zip(leader_positions, follower_positions)):
        motor_id = i + 1
        diff = abs(leader_pos - follower_pos)
        print(f"{motor_id}:{leader_pos}->{follower_pos} ", end="")

    print("", end="\r")
    sys.stdout.flush()

def monitor_keyboard_input():
    """Monitor for keyboard input in a separate thread"""
    global teleoperation_active, DEBUG_MODE

    while True:
        if keyboard.is_pressed('esc'):
            print("\nESC pressed. Exiting...")
            signal_handler(None, None)

        elif keyboard.is_pressed('space'):
            with lock:
                teleoperation_active = not teleoperation_active
                status = "enabled" if teleoperation_active else "disabled"
                print(f"\nTeleoperation {status}")
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('r'):
            print("\nResetting to center position...")
            reset_to_rest_position()
            time.sleep(0.3)  # Debounce
            
        elif keyboard.is_pressed('a'):
            print("\nConfiguring advanced motor settings...")
            configure_advanced_settings()
            time.sleep(0.3)  # Debounce
            
        elif keyboard.is_pressed('v'):
            print("\nFixing SO-101 specific registers...")
            fix_so101_specific_registers()
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('d'):
            with lock:
                DEBUG_MODE = not DEBUG_MODE
                print(f"\nDebug mode {'enabled' if DEBUG_MODE else 'disabled'}")
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('t'):
            toggle_all_motors_torque(follower_port_handler, follower_packet_handler)
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('s'):
            show_motor_status()
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('c'):
            calibrate_offset()
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('f'):
            test_follower_movement()
            time.sleep(0.3)  # Debounce

        # Check for number keys 1-6
        for i in range(1, 7):
            if keyboard.is_pressed(str(i)):
                toggle_motor_torque(follower_port_handler, follower_packet_handler, i)
                time.sleep(0.3)  # Debounce

        time.sleep(0.1)

def reset_to_rest_position():
    """Reset the follower arm to a natural rest position"""
    print("\n=== Resetting to Rest Position ===")
    
    # Ensure torque is enabled on all motors
    enable_all_motors(follower_port_handler, follower_packet_handler)
    
    # Move to rest position with increased power settings
    for motor_id in MOTOR_IDS:
        try:
            # Set high torque temporarily for movement
            follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, 34, 1023)
            follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, 32, 512)
        except:
            pass
    
    # Send to REST_POSITIONS with retry
    for attempt in range(3):
        success = move_motors(follower_port_handler, follower_packet_handler, MOTOR_IDS, REST_POSITIONS)
        if success:
            break
        time.sleep(0.3)
    
    print("Follower arm moved to rest position")
    return success

def fix_so101_specific_registers():
    """Apply specific fixes for SO-101 servo registers"""
    print("\n=== Applying SO-101 Specific Fixes ===")
    
    # First disable torque
    for motor_id in MOTOR_IDS:
        follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 50, 0)
    
    time.sleep(0.2)
    
    # For each motor
    for motor_id in MOTOR_IDS:
        try:
            print(f"Fixing motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")
            
            # Fix potential register issues:
            
            # 1. Set alarm shutdown to prevent overheating/protection (address 18)
            follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 18, 36)
            print(f"  Set alarm shutdown settings")
            
            # 2. Set proper deadband (address 24-25) - helps with stability
            follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, 24, 0)
            print(f"  Reset deadband")
            
            # 3. Completely reset compliance settings
            for addr in range(26, 30):
                follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, addr, 0)
            print(f"  Reset compliance parameters")
            
            # 4. Ensure max speed is set high
            follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, 32, 1023)
            print(f"  Set max speed to maximum")
        except Exception as e:
            print(f"  Error fixing motor {motor_id}: {e}")
    
    # Re-enable torque
    print("Re-enabling torque...")
    for motor_id in MOTOR_IDS:
        try:
            follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 50, 1)
        except:
            print(f"  Could not re-enable torque on motor {motor_id}")
    
    print("SO-101 specific fixes applied!")
    print("Now try calibrating with the 'C' key and then teleoperating.")
    return True

def configure_advanced_settings():
    """Configure advanced motor settings to ensure movement works"""
    print("\n=== Configuring Advanced Motor Settings ===")
    
    # For each motor in the follower arm
    for motor_id in MOTOR_IDS:
        print(f"Configuring motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")
        
        try:
            # Disable torque temporarily to modify settings
            follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 50, 0)
            time.sleep(0.1)
            
            # 1. Set maximum torque (addresses 34-35) to maximum value
            max_torque = 1023  # Maximum possible value (100%)
            result, error = follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, 34, max_torque)
            if result == scs.COMM_SUCCESS:
                print(f"  Set maximum torque to {max_torque} (100%)")
            
            # 2. Set speed limit (addresses 46-47) to a suitable value (50% of max)
            speed = 512  # Medium speed (50% of max)
            result, error = follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, 46, speed)
            if result == scs.COMM_SUCCESS:
                print(f"  Set speed limit to {speed}")
                
            # 3. Set compliance parameters (if applicable to this servo model)
            try:
                # Compliance margin - how much error is acceptable
                follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 26, 2)  # CW compliance margin
                follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 27, 2)  # CCW compliance margin
                print("  Set compliance margins to 2")
                
                # Compliance slope - how quickly to correct errors
                follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 28, 32)  # CW compliance slope
                follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 29, 32)  # CCW compliance slope
                print("  Set compliance slopes to 32")
            except:
                print("  Could not set compliance parameters (may not be supported)")
            
            # 4. Set higher movement speed (addresses 32-33)
            speed_value = 512  # Range 0-1023 (about 50%)
            follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, 32, speed_value)
            print(f"  Set movement speed to {speed_value} (50%)")
            
            # 5. Reset control mode to position control (address 11 in some servos)
            try:
                follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 11, 0)  # 0=position control
                print("  Set to position control mode")
            except:
                print("  Could not set control mode (may not be supported)")
            
        except Exception as e:
            print(f"  Error configuring motor {motor_id}: {e}")
    
    print("Advanced motor configuration complete!")
    print("Now try resetting to the rest position using the 'R' key.")
    return True

def main():
    global teleoperation_active

    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    # Open communication ports
    if not open_ports():
        print("Failed to initialize ports. Exiting...")
        return

    print_instructions()
    print("Initializing teleoperation...")
    print("\nIMPORTANT SETUP STEPS:")
    print("1. Press 'V' to fix SO-101 specific registers")
    print("2. Press 'A' to configure advanced motor settings")
    print("3. Press 'R' to move the follower arm to rest position")
    print("4. Press 'C' to calibrate position offsets between arms")
    print("5. Use SPACE to toggle teleoperation on/off\n")

    # Enable motors on follower arm
    enable_result = enable_all_motors(follower_port_handler, follower_packet_handler)
    if not enable_result:
        print("WARNING: Not all follower motors could be enabled. Check connections and power.")
        print("Press 'T' to retry enabling motors or 'S' to check motor status.")

    # Read initial positions
    leader_positions = read_motor_positions(leader_port_handler, leader_packet_handler, MOTOR_IDS)
    follower_positions = read_motor_positions(follower_port_handler, follower_packet_handler, MOTOR_IDS)
    print(f"Initial leader positions: {leader_positions}")
    print(f"Initial follower positions: {follower_positions}")

    # Start keyboard monitoring in a separate thread
    keyboard_thread = threading.Thread(target=monitor_keyboard_input, daemon=True)
    keyboard_thread.start()

    # Smooth the position changes to avoid jerky movements
    smoothed_positions = leader_positions.copy()

    # Main control loop
    try:
        print("\nStarting teleoperation. Move the leader arm to control the follower.")
        print("Press 'F' to test if follower can move at all.")
        iteration_count = 0

        while True:
            try:
                with lock:
                    current_teleoperation_active = teleoperation_active

                if current_teleoperation_active:
                    # Read current leader arm positions
                    current_leader_positions = read_motor_positions(leader_port_handler, leader_packet_handler, MOTOR_IDS)

                    # Apply smoothing to reduce jitter
                    alpha = 0.3  # Smoothing factor (0-1), higher = less smoothing
                    smoothed_positions = [alpha * current + (1 - alpha) * smoothed for current, smoothed in zip(current_leader_positions, smoothed_positions)]

                    # Apply position offsets if calibrated
                    adjusted_positions = [int(pos + offset) % 4096 for pos, offset in zip(smoothed_positions, position_offsets)]

                    # Send to follower arm
                    move_motors(follower_port_handler, follower_packet_handler, MOTOR_IDS, adjusted_positions)

                    # Periodically verify the follower is actually moving
                    if iteration_count % 20 == 0:
                        follower_positions = read_motor_positions(follower_port_handler, follower_packet_handler, MOTOR_IDS)

                    # Print status every few iterations
                    if iteration_count % 10 == 0 and not DEBUG_MODE:
                        print_status(current_leader_positions, follower_positions, current_teleoperation_active)

                    iteration_count += 1

            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)

            time.sleep(UPDATE_FREQUENCY)

    except KeyboardInterrupt:
        print("\nProgram interrupted. Cleaning up...")

    finally:
        # Clean up
        disable_all_motors(follower_port_handler, follower_packet_handler)
        leader_port_handler.closePort()
        follower_port_handler.closePort()
        print("Ports closed. Program terminated.")

if __name__ == "__main__":
    main()

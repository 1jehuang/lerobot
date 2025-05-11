"""
SO-101 Improved Teleoperation Script

This script reads positions from the leader arm and sends them to the follower arm.
It features improved smoothing, visual feedback, and better error handling.

Usage:
    python so101_improved_teleoperation.py

Keyboard controls:
    ESC: Exit program
    SPACE: Toggle teleoperation on/off
    R: Reset/return to home position
    D: Toggle debug information
    T: Toggle torque on all follower motors
    1-6: Toggle individual follower motor torque
"""

import sys
import os
import time
import keyboard  # pip install keyboard
import signal
import numpy as np
import threading

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

# Safe positions for initialization
# Center position would be 2048 for each motor
SAFE_POSITIONS = [2048, 2048, 2048, 2048, 2048, 2048]

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
    print("\nExiting program...")
    disable_all_motors(follower_port_handler, follower_packet_handler)
    leader_port_handler.closePort()
    follower_port_handler.closePort()
    sys.exit(0)

def open_ports():
    """Open communication ports for both arms with better error handling"""
    # Open leader port
    try:
        if leader_port_handler.openPort():
            print(f"✓ Successfully opened leader port {LEADER_PORT}")
        else:
            print(f"✗ Failed to open leader port {LEADER_PORT}")
            return False

        # Set leader baudrate
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

        # Set follower baudrate
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
    """Read position of multiple motors with improved error handling"""
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
    """Move multiple motors to specified positions with better error handling"""
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
                    print(f"Motor {motor_id} moved to {safe_position}")
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

def is_motor_torque_enabled(port_handler, packet_handler, motor_id):
    """Check if torque is enabled for a specific motor"""
    try:
        torque, result, _ = packet_handler.read1ByteTxRx(port_handler, motor_id, 50)  # Address 50 = Torque Enable
        if result == scs.COMM_SUCCESS:
            return torque == 1
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

    print(f"{'Enabling' if new_state == 1 else 'Disabling'} torque for all follower motors...")
    for motor_id in MOTOR_IDS:
        try:
            result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 50, new_state)
            if result != scs.COMM_SUCCESS:
                print(f"Failed to set torque on motor {motor_id}")
        except Exception as e:
            print(f"Error setting motor {motor_id} torque: {e}")

def print_instructions():
    """Print the keyboard controls"""
    print("\n=== SO-101 Teleoperation Controls ===")
    print("ESC: Exit program")
    print("SPACE: Toggle teleoperation (ON/OFF)")
    print("R: Reset to home position")
    print("D: Toggle debug information")
    print("T: Toggle torque on all follower motors")
    print("1-6: Toggle individual follower motor torque")
    print("=====================================\n")

def print_status(leader_positions, follower_positions, is_active):
    """Print current status"""
    status = "ACTIVE" if is_active else "PAUSED"
    print(f"\rTeleoperation: {status} | ", end="")

    for i, (leader_pos, follower_pos) in enumerate(zip(leader_positions, follower_positions)):
        motor_id = i + 1
        print(f"{MOTOR_NAMES.get(motor_id, f'Motor {motor_id}')}: L={leader_pos} F={follower_pos} | ", end="")

    print("", end="\r")
    sys.stdout.flush()

def reset_to_home():
    """Reset follower to safe home position"""
    print("\nResetting to home position...")
    move_motors(follower_port_handler, follower_packet_handler, MOTOR_IDS, SAFE_POSITIONS)

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
            reset_to_home()
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('d'):
            with lock:
                DEBUG_MODE = not DEBUG_MODE
                print(f"\nDebug mode {'enabled' if DEBUG_MODE else 'disabled'}")
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('t'):
            toggle_all_motors_torque(follower_port_handler, follower_packet_handler)
            time.sleep(0.3)  # Debounce

        # Check for number keys 1-6
        for i in range(1, 7):
            if keyboard.is_pressed(str(i)):
                toggle_motor_torque(follower_port_handler, follower_packet_handler, i)
                time.sleep(0.3)  # Debounce

        time.sleep(0.1)

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

    # Enable motors on follower arm
    enable_result = enable_all_motors(follower_port_handler, follower_packet_handler)
    if not enable_result:
        print("Warning: Not all follower motors could be enabled. Check connections and power.")

    # Read initial positions with retries
    max_attempts = 3
    leader_positions = None
    for attempt in range(max_attempts):
        try:
            leader_positions = read_motor_positions(leader_port_handler, leader_packet_handler, MOTOR_IDS)
            if all(pos != 2048 for pos in leader_positions):  # Ensure not all default values
                break
        except Exception:
            time.sleep(0.5)

    if not leader_positions:
        print("Failed to read leader positions after multiple attempts. Using defaults.")
        leader_positions = [2048] * len(MOTOR_IDS)

    print(f"Initial leader positions: {leader_positions}")

    # Start keyboard monitoring in a separate thread
    keyboard_thread = threading.Thread(target=monitor_keyboard_input, daemon=True)
    keyboard_thread.start()

    # Smooth the position changes to avoid jerky movements
    smoothed_positions = leader_positions.copy()
    follower_current = read_motor_positions(follower_port_handler, follower_packet_handler, MOTOR_IDS)

    try:
        iteration_count = 0
        while True:
            try:
                with lock:
                    current_teleoperation_active = teleoperation_active

                if current_teleoperation_active:
                    # Read current leader arm positions
                    current_leader_positions = read_motor_positions(leader_port_handler, leader_packet_handler, MOTOR_IDS)

                    # Apply dynamic smoothing to reduce jitter
                    alpha = 0.2  # Lower value = more smoothing (0.0 - 1.0)
                    smoothed_positions = [alpha * current + (1 - alpha) * smoothed for current, smoothed in zip(current_leader_positions, smoothed_positions)]

                    # Convert to integers for motor control
                    target_positions = [int(pos) for pos in smoothed_positions]

                    # Send smoothed positions to follower arm
                    move_motors(follower_port_handler, follower_packet_handler, MOTOR_IDS, target_positions)

                    # Update follower positions periodically (not every loop to reduce overhead)
                    if iteration_count % 10 == 0:  # Every 10 iterations
                        follower_current = read_motor_positions(follower_port_handler, follower_packet_handler, MOTOR_IDS)

                    # Print status (less frequently)
                    if iteration_count % 20 == 0 and not DEBUG_MODE:  # Every 20 iterations when not in debug mode
                        print_status(current_leader_positions, follower_current, current_teleoperation_active)

                    iteration_count += 1

            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)  # Wait a bit before retrying

            # Control the update rate
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

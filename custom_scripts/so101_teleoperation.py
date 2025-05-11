"""
SO-101 Teleoperation Script

This script reads positions from the leader arm and sends them to the follower arm.
It allows real-time teleoperation of the SO-101 robot.

Usage:
    python so101_teleoperation.py

Keyboard controls:
    ESC: Exit program
    SPACE: Toggle teleoperation on/off
    R: Reset/return to home position
"""

import sys
import os
import time
import keyboard  # pip install keyboard
import signal
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
teleoperation_active = True

# Safe positions for initialization
SAFE_POSITIONS = [2048, 2048, 2048, 2048, 2048, 2048]  # Center positions

def signal_handler(sig, frame):
    print("\nExiting program...")
    disable_all_motors(follower_port_handler, follower_packet_handler)
    leader_port_handler.closePort()
    follower_port_handler.closePort()
    sys.exit(0)

def open_ports():
    """Open communication ports for both arms"""
    # Open leader port
    if leader_port_handler.openPort():
        print(f"Successfully opened leader port {LEADER_PORT}")
    else:
        print(f"Failed to open leader port {LEADER_PORT}")
        return False

    # Set leader baudrate
    if leader_port_handler.setBaudRate(BAUDRATE):
        print(f"Changed leader baudrate to {BAUDRATE}")
    else:
        print(f"Failed to change leader baudrate")
        leader_port_handler.closePort()
        return False

    # Open follower port
    if follower_port_handler.openPort():
        print(f"Successfully opened follower port {FOLLOWER_PORT}")
    else:
        print(f"Failed to open follower port {FOLLOWER_PORT}")
        leader_port_handler.closePort()
        return False

    # Set follower baudrate
    if follower_port_handler.setBaudRate(BAUDRATE):
        print(f"Changed follower baudrate to {BAUDRATE}")
    else:
        print(f"Failed to change follower baudrate")
        leader_port_handler.closePort()
        follower_port_handler.closePort()
        return False

    return True

def read_motor_positions(port_handler, packet_handler, motor_ids):
    """Read position of multiple motors"""
    positions = []
    for motor_id in motor_ids:
        position, result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)  # Read present position (address 56)
        if result == scs.COMM_SUCCESS:
            positions.append(position)
        else:
            print(f"Failed to read position from motor {motor_id}: {packet_handler.getTxRxResult(result)}")
            # Use previous position or default
            positions.append(2048)
    return positions

def move_motors(port_handler, packet_handler, motor_ids, positions):
    """Move multiple motors to specified positions"""
    for motor_id, position in zip(motor_ids, positions):
        result, error = packet_handler.write2ByteTxRx(port_handler, motor_id, 60, position)  # Write goal position (address 60)
        if result != scs.COMM_SUCCESS:
            print(f"Failed to write position to motor {motor_id}: {packet_handler.getTxRxResult(result)}")

def enable_all_motors(port_handler, packet_handler):
    """Enable torque for all motors"""
    print("Enabling torque for all motors...")
    for motor_id in MOTOR_IDS:
        result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 50, 1)  # Torque enable (address 50)
        if result != scs.COMM_SUCCESS:
            print(f"Failed to enable torque on motor {motor_id}: {packet_handler.getTxRxResult(result)}")

def disable_all_motors(port_handler, packet_handler):
    """Disable torque for all motors"""
    print("Disabling torque for all motors...")
    for motor_id in MOTOR_IDS:
        result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 50, 0)  # Torque disable (address 50)
        if result != scs.COMM_SUCCESS:
            print(f"Failed to disable torque on motor {motor_id}: {packet_handler.getTxRxResult(result)}")

def print_instructions():
    """Print the keyboard controls"""
    print("\n=== SO-101 Teleoperation ===")
    print("ESC: Exit program")
    print("SPACE: Toggle teleoperation (ON/OFF)")
    print("R: Reset/home position")
    print("=========================\n")

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
    enable_all_motors(follower_port_handler, follower_packet_handler)

    # Read initial positions
    leader_positions = read_motor_positions(leader_port_handler, leader_packet_handler, MOTOR_IDS)
    print(f"Initial leader positions: {leader_positions}")

    # Smooth the position changes to avoid jerky movements
    smoothed_positions = leader_positions.copy()

    try:
        while True:
            # Check for keyboard input
            if keyboard.is_pressed('esc'):
                print("\nESC pressed. Exiting...")
                break

            if keyboard.is_pressed('space'):
                teleoperation_active = not teleoperation_active
                print(f"Teleoperation {'enabled' if teleoperation_active else 'disabled'}")
                time.sleep(0.3)  # Debounce

            if keyboard.is_pressed('r'):
                print("Resetting to home position...")
                move_motors(follower_port_handler, follower_packet_handler, MOTOR_IDS, SAFE_POSITIONS)
                time.sleep(0.3)  # Debounce

            if teleoperation_active:
                # Read current leader arm positions
                current_leader_positions = read_motor_positions(leader_port_handler, leader_packet_handler, MOTOR_IDS)

                # Apply exponential smoothing to reduce jitter
                alpha = 0.3  # Smoothing factor (0-1), higher = less smoothing
                smoothed_positions = [alpha * current + (1 - alpha) * smoothed for current, smoothed in zip(current_leader_positions, smoothed_positions)]

                # Send smoothed positions to follower arm
                move_motors(follower_port_handler, follower_packet_handler, MOTOR_IDS, [int(pos) for pos in smoothed_positions])

                # Status update (uncomment to see detailed position information)
                # print(f"Leader: {current_leader_positions} -> Follower: {[int(pos) for pos in smoothed_positions]}")

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

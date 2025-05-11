"""
SO-101 Power Cycling Tool

This script helps with power cycling the servos by turning the torque
on and off multiple times, which can sometimes help reset servo issues.

Usage:
    python power_cycle_motors.py
"""

import sys
import os
import time
import serial

# Motor names for better readability
MOTOR_NAMES = {
    1: "Shoulder Pan",
    2: "Shoulder Lift",
    3: "Elbow Flex",
    4: "Wrist Flex",
    5: "Wrist Roll",
    6: "Gripper"
}

# Port settings
FOLLOWER_PORT = "COM4"
BAUDRATE = 1000000

# Control parameters
MOTOR_IDS = list(range(1, 7))  # Motors 1-6
ADDR_TORQUE_ENABLE = 0x28  # Torque enable (40)

def print_header():
    """Print script header"""
    print("=" * 50)
    print("       SO-101 FOLLOWER ARM POWER CYCLING TOOL")
    print("=" * 50)
    print("\nThis tool will help reset servo motors by cycling power")
    print("Make sure the follower arm is connected and powered on")

def open_port():
    """Open the serial port for communication"""
    try:
        # Try to open the port
        ser = serial.Serial(FOLLOWER_PORT, BAUDRATE, timeout=0.5)
        print(f"Successfully opened {FOLLOWER_PORT}")
        return ser
    except Exception as e:
        print(f"Error opening {FOLLOWER_PORT}: {e}")
        return None

def close_port(ser):
    """Close the serial port"""
    if ser:
        ser.close()
        print(f"Closed {FOLLOWER_PORT}")

def ping_motor(ser, motor_id):
    """Ping a motor to check if it's responsive"""
    # Basic ping packet: 0xFF 0xFF ID 0x02 0x01 CHECKSUM
    checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
    packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])

    ser.write(packet)
    time.sleep(0.1)  # Wait for response

    if ser.in_waiting:
        response = ser.read(ser.in_waiting)
        if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
            return True
        else:
            return False
    else:
        return False

def set_torque(ser, motor_id, enable):
    """Enable or disable torque on a motor"""
    value = 1 if enable else 0
    state = "ON" if enable else "OFF"

    # Format: 0xFF 0xFF ID LENGTH INSTRUCTION PARAM1 PARAM2 CHECKSUM
    checksum = 0xFF - ((motor_id + 0x04 + 0x03 + ADDR_TORQUE_ENABLE + value) % 256)
    packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, ADDR_TORQUE_ENABLE, value, checksum])

    ser.write(packet)
    time.sleep(0.05)  # Wait for response

    if ser.in_waiting:
        response = ser.read(ser.in_waiting)
        if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
            return True
        else:
            return False
    return False

def power_cycle_motors():
    """Perform power cycling on motors"""
    print_header()

    # Open the port
    ser = open_port()
    if not ser:
        print("Failed to open port. Exiting...")
        return

    try:
        # Check which motors are responsive
        print("\nChecking for responsive motors...")
        responsive_motors = []
        for motor_id in MOTOR_IDS:
            if ping_motor(ser, motor_id):
                print(f"  ✓ Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}) is responsive")
                responsive_motors.append(motor_id)
            else:
                print(f"  ✗ Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}) not responding")

        if not responsive_motors:
            print("\nNo motors are responding. Check connections and power.")
            return

        print(f"\nFound {len(responsive_motors)} responsive motors.")
        print("\nStarting power cycling sequence...")

        # Perform 5 power cycles
        cycles = 5
        for cycle in range(1, cycles + 1):
            print(f"\nCycle {cycle}/{cycles}:")

            # Turn torque OFF
            print("  Turning torque OFF...")
            for motor_id in responsive_motors:
                success = set_torque(ser, motor_id, False)
                if success:
                    print(f"    ✓ Motor {motor_id} torque disabled")
                else:
                    print(f"    ✗ Failed to disable torque on motor {motor_id}")

            # Wait
            print("  Waiting 2 seconds...")
            time.sleep(2.0)

            # Turn torque ON
            print("  Turning torque ON...")
            for motor_id in responsive_motors:
                success = set_torque(ser, motor_id, True)
                if success:
                    print(f"    ✓ Motor {motor_id} torque enabled")
                else:
                    print(f"    ✗ Failed to enable torque on motor {motor_id}")

            # Wait
            print("  Waiting 2 seconds...")
            time.sleep(2.0)

        print("\nPower cycling complete!")
        print("\nVerifying motors are still responsive...")

        # Check which motors are still responsive
        final_responsive = []
        for motor_id in MOTOR_IDS:
            if ping_motor(ser, motor_id):
                print(f"  ✓ Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}) is responsive")
                final_responsive.append(motor_id)
            else:
                print(f"  ✗ Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}) not responding")

        print(f"\nFound {len(final_responsive)} responsive motors after power cycling.")
        print("\nNext steps:")
        print("1. Run the direct_reset_follower_motors.py script")
        print("2. Then test movement with follower_move_test.py")

    finally:
        # Close the port
        close_port(ser)

if __name__ == "__main__":
    power_cycle_motors()

"""
SO-101 Follower Motor Direct Reset

This script attempts to reset the follower arm motors using direct serial communication
rather than the SDK, which sometimes works better for basic communication.

1. Tries to reset each motor to factory defaults
2. Uses multiple approaches for motor recovery
3. Tests basic movement after reset

Usage:
    python direct_reset_follower_motors.py
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
CENTER_POSITION = 2048  # Center position (0 degree)

# Key register addresses for SCServo motors
ADDR_TORQUE_ENABLE = 0x28       # Torque enable (40)
ADDR_PRESENT_POSITION = 0x38    # Present position (56)
ADDR_GOAL_POSITION = 0x2A       # Goal position (42)
ADDR_OPERATING_MODE = 0x0B      # Operating mode (11)
ADDR_MAX_TORQUE = 0x22          # Max torque setting (34)
ADDR_GOAL_SPEED = 0x2E          # Movement speed (46)
ADDR_RETURN_DELAY = 0x05        # Return delay time (5)
ADDR_ALARM_SHUTDOWN = 0x12      # Alarm shutdown flags (18)
ADDR_LED = 0x29                 # LED control (41)

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

def write_byte(ser, motor_id, address, value):
    """Write a single byte to a motor register using direct serial"""
    # Format: 0xFF 0xFF ID LENGTH INSTRUCTION PARAM1 PARAM2 ... CHECKSUM
    # For write (INST=0x03): ADDRESS VALUE
    checksum = 0xFF - ((motor_id + 0x04 + 0x03 + address + value) % 256)
    packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, address, value, checksum])

    ser.write(packet)
    time.sleep(0.05)  # Wait for response

    if ser.in_waiting:
        response = ser.read(ser.in_waiting)
        if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
            return True, response
        else:
            return False, response
    return False, None

def write_word(ser, motor_id, address, value):
    """Write a two-byte word to a motor register using direct serial"""
    # Split value into low and high bytes
    value_l = value & 0xFF
    value_h = (value >> 8) & 0xFF

    # Format: 0xFF 0xFF ID LENGTH INSTRUCTION PARAM1 PARAM2 PARAM3 CHECKSUM
    # For write (INST=0x03): ADDRESS VALUE_L VALUE_H
    checksum = 0xFF - ((motor_id + 0x05 + 0x03 + address + value_l + value_h) % 256)
    packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, address, value_l, value_h, checksum])

    ser.write(packet)
    time.sleep(0.05)  # Wait for response

    if ser.in_waiting:
        response = ser.read(ser.in_waiting)
        if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
            return True, response
        else:
            return False, response
    return False, None

def read_word(ser, motor_id, address, length=2):
    """Read a two-byte word from a motor register using direct serial"""
    # Format: 0xFF 0xFF ID LENGTH INSTRUCTION PARAM1 PARAM2 CHECKSUM
    # For read (INST=0x02): ADDRESS LENGTH
    checksum = 0xFF - ((motor_id + 0x04 + 0x02 + address + length) % 256)
    packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x02, address, length, checksum])

    ser.write(packet)
    time.sleep(0.05)  # Wait for response

    if ser.in_waiting:
        response = ser.read(ser.in_waiting)
        if len(response) >= 8 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
            # Extract value
            value_l = response[5]
            value_h = response[6]
            value = (value_h << 8) + value_l
            return value, True, response
        else:
            return 0, False, response
    return 0, False, None

def ping_motor(ser, motor_id):
    """Ping a motor to check if it's responsive"""
    print(f"Pinging motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")

    # Basic ping packet: 0xFF 0xFF ID 0x02 0x01 CHECKSUM
    checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
    packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])

    ser.write(packet)
    time.sleep(0.1)  # Wait for response

    if ser.in_waiting:
        response = ser.read(ser.in_waiting)
        print(f"  Response: {' '.join([hex(b) for b in response])}")

        if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
            print(f"  ✓ Motor {motor_id} responded to ping!")
            return True
        else:
            print(f"  ✗ Invalid response format")
            return False
    else:
        print(f"  ✗ No response from motor {motor_id}")
        return False

def reset_motor(ser, motor_id):
    """Reset motor to factory defaults using a sequence of commands"""
    print(f"Resetting motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")

    # First disable torque to allow parameter changes
    success, _ = write_byte(ser, motor_id, ADDR_TORQUE_ENABLE, 0)
    if success:
        print(f"  ✓ Torque disabled")
    else:
        print(f"  ✗ Failed to disable torque")

    # Try various approaches to reset the motor

    # 1. Reset max torque to normal value
    success, _ = write_word(ser, motor_id, ADDR_MAX_TORQUE, 1000)  # ~100%
    if success:
        print(f"  ✓ Max torque reset")
    else:
        print(f"  ✗ Failed to reset max torque")

    # 2. Set position control mode
    success, _ = write_byte(ser, motor_id, ADDR_OPERATING_MODE, 0)
    if success:
        print(f"  ✓ Position control mode set")
    else:
        print(f"  ✗ Failed to set position control mode")

    # 3. Set speed to moderate value
    success, _ = write_word(ser, motor_id, ADDR_GOAL_SPEED, 500)
    if success:
        print(f"  ✓ Speed set to moderate value")
    else:
        print(f"  ✗ Failed to set speed")

    # 4. Set return delay to minimum
    success, _ = write_byte(ser, motor_id, ADDR_RETURN_DELAY, 0)
    if success:
        print(f"  ✓ Return delay set to minimum")
    else:
        print(f"  ✗ Failed to set return delay")

    # 5. Reset alarm shutdown
    success, _ = write_byte(ser, motor_id, ADDR_ALARM_SHUTDOWN, 3)
    if success:
        print(f"  ✓ Alarm shutdown reset")
    else:
        print(f"  ✗ Failed to reset alarm shutdown")

    # 6. Blink LED to show reset
    success, _ = write_byte(ser, motor_id, ADDR_LED, 1)
    if success:
        print(f"  ✓ LED turned on")
    else:
        print(f"  ✗ Failed to turn on LED")

    time.sleep(0.5)

    success, _ = write_byte(ser, motor_id, ADDR_LED, 0)
    if success:
        print(f"  ✓ LED turned off")

    # 7. Re-enable torque
    success, _ = write_byte(ser, motor_id, ADDR_TORQUE_ENABLE, 1)
    if success:
        print(f"  ✓ Torque enabled")
    else:
        print(f"  ✗ Failed to enable torque")

    return success

def test_motor_movement(ser, motor_id):
    """Test if the motor can move to a target position"""
    print(f"Testing movement of motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")

    # Enable torque
    success, _ = write_byte(ser, motor_id, ADDR_TORQUE_ENABLE, 1)
    if not success:
        print(f"  ✗ Failed to enable torque")
        return False

    # Read current position
    current_pos, success, _ = read_word(ser, motor_id, ADDR_PRESENT_POSITION)
    if not success:
        print(f"  ✗ Failed to read position")
        return False

    print(f"  Current position: {current_pos}")

    # Try to move 100 steps
    target_pos = (current_pos + 100) % 4096
    print(f"  Moving to position {target_pos}...")

    success, _ = write_word(ser, motor_id, ADDR_GOAL_POSITION, target_pos)
    if not success:
        print(f"  ✗ Failed to send move command")
        return False

    # Give time to move
    print("  Waiting for movement...")
    time.sleep(1.0)

    # Read new position
    new_pos, success, _ = read_word(ser, motor_id, ADDR_PRESENT_POSITION)
    if not success:
        print(f"  ✗ Failed to read new position")
        return False

    print(f"  New position: {new_pos}")

    # Check if it moved
    diff = abs(new_pos - target_pos)
    if diff < 20:
        print(f"  ✓ Motor moved successfully! (difference: {diff})")
        moved = True
    else:
        print(f"  ✗ Motor did not move to target (difference: {diff})")
        moved = False

    # Return to original position
    if moved:
        print(f"  Returning to original position {current_pos}...")
        success, _ = write_word(ser, motor_id, ADDR_GOAL_POSITION, current_pos)
        time.sleep(1.0)

    return moved

def center_motor(ser, motor_id):
    """Center a motor (move to position 2048)"""
    print(f"Centering motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")

    # Enable torque
    success, _ = write_byte(ser, motor_id, ADDR_TORQUE_ENABLE, 1)
    if not success:
        print(f"  ✗ Failed to enable torque")
        return False

    # Move to center position
    success, _ = write_word(ser, motor_id, ADDR_GOAL_POSITION, CENTER_POSITION)
    if not success:
        print(f"  ✗ Failed to send center command")
        return False

    print(f"  Move command sent to position {CENTER_POSITION}")
    return True

def perform_reset_sequence():
    """Run the full reset sequence on all motors"""
    print("=== SO-101 Follower Motor Direct Reset ===")

    # Open serial port
    ser = open_port()
    if not ser:
        print("Failed to open port. Please check connections.")
        return

    try:
        # Step 1: Ping all motors to check basic communication
        print("\n=== Testing Basic Communication ===")
        responsive_motors = []
        for motor_id in MOTOR_IDS:
            if ping_motor(ser, motor_id):
                responsive_motors.append(motor_id)

        if not responsive_motors:
            print("\nNo motors responding. Check physical connections and power.")
            return

        print(f"\nResponsive motors: {responsive_motors}")

        # Step 2: Reset parameters on all responsive motors
        print("\n=== Resetting Motor Parameters ===")
        reset_motors = []
        for motor_id in responsive_motors:
            if reset_motor(ser, motor_id):
                reset_motors.append(motor_id)

        print(f"\nSuccessfully reset motors: {reset_motors}")

        # Step 3: Test movement on all reset motors
        print("\n=== Testing Motor Movement ===")
        moving_motors = []
        for motor_id in reset_motors:
            if test_motor_movement(ser, motor_id):
                moving_motors.append(motor_id)

        print(f"\nMotors that can move: {moving_motors}")

        # Step 4: Center all movable motors
        if moving_motors:
            print("\n=== Centering Motors ===")
            for motor_id in moving_motors:
                center_motor(ser, motor_id)

            print("\nWaiting for centering to complete...")
            time.sleep(2.0)

        # Final report
        print("\n=== Reset Process Complete ===")
        print(f"Total motors: {len(MOTOR_IDS)}")
        print(f"Responsive motors: {len(responsive_motors)}/{len(MOTOR_IDS)}")
        print(f"Reset motors: {len(reset_motors)}/{len(responsive_motors)}")
        print(f"Movable motors: {len(moving_motors)}/{len(reset_motors)}")

        if len(moving_motors) == len(MOTOR_IDS):
            print("\nSUCCESS! All motors are now functional.")
        elif len(moving_motors) > 0:
            print(f"\nPARTIAL SUCCESS. {len(moving_motors)} motors are functional.")
        else:
            print("\nFAILED. No motors are moving despite reset attempts.")

    finally:
        # Close the port
        close_port(ser)

if __name__ == "__main__":
    perform_reset_sequence()

"""
SO-101 Follower Motor Reset

This script attempts to reset the follower arm's servo motors and adjust their settings
to ensure they respond to position commands correctly. It will:

1. Verify communication with all motors
2. Reset certain control parameters to factory defaults
3. Adjust settings critical for movement
4. Test movement on each motor

Usage:
    python reset_follower_motors.py
"""

import sys
import os
import time
import signal

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import scservo_sdk as scs
    print("Successfully imported scservo_sdk")
except ImportError:
    print("Failed to import scservo_sdk. Make sure it's installed.")
    sys.exit(1)

# Port settings
FOLLOWER_PORT = "COM4"
BAUDRATE = 1000000
PROTOCOL = 0  # Protocol 0 for SCServo SCS

# Motor IDs
MOTOR_IDS = list(range(1, 7))  # Motors 1-6

# Control parameters
CENTER_POSITION = 2048  # Center position (0 degree)

# Motor names for better readability
MOTOR_NAMES = {
    1: "Shoulder Pan",
    2: "Shoulder Lift",
    3: "Elbow Flex",
    4: "Wrist Flex",
    5: "Wrist Roll",
    6: "Gripper"
}

# Key register addresses for SCServo motors
ADDR_TORQUE_ENABLE = 40       # Torque enable
ADDR_PRESENT_POSITION = 56    # Present position
ADDR_GOAL_POSITION = 42       # Goal position
ADDR_OPERATING_MODE = 11      # Operating mode
ADDR_MAX_TORQUE = 34          # Max torque setting
ADDR_GOAL_SPEED = 46          # Movement speed
ADDR_RETURN_DELAY = 5         # Return delay time
ADDR_COMPLIANCE_P_GAIN = 29   # Position P gain
ADDR_COMPLIANCE_D_GAIN = 28   # Position D gain
ADDR_COMPLIANCE_I_GAIN = 27   # Position I gain
ADDR_COMPLIANCE_MARGIN = 24   # Compliance margin
ADDR_PUNCH = 48               # Punch setting
ADDR_ALARM_SHUTDOWN = 18      # Alarm shutdown flags
ADDR_VOLTAGE_LIMIT = 22       # Voltage limit
ADDR_TEMPERATURE_LIMIT = 20   # Temperature limit
ADDR_TORQUE_LIMIT = 35        # Torque limit

def signal_handler(sig, frame):
    print("\nExiting program...")
    follower_port_handler.closePort()
    sys.exit(0)

# Initialize port handlers
follower_port_handler = scs.PortHandler(FOLLOWER_PORT)
follower_packet_handler = scs.PacketHandler(PROTOCOL)

def open_port():
    """Open the follower port with error handling"""
    try:
        if follower_port_handler.openPort():
            print(f"✓ Successfully opened follower port {FOLLOWER_PORT}")
        else:
            print(f"✗ Failed to open follower port {FOLLOWER_PORT}")
            return False

        if follower_port_handler.setBaudRate(BAUDRATE):
            print(f"✓ Changed follower baudrate to {BAUDRATE}")
        else:
            print(f"✗ Failed to change follower baudrate")
            follower_port_handler.closePort()
            return False

        return True
    except Exception as e:
        print(f"✗ Error with follower port: {e}")
        return False

def reset_motor(motor_id):
    """Reset critical motor parameters to defaults"""
    print(f"Resetting motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")

    # Disable torque first (required to change some settings)
    result, error = follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, ADDR_TORQUE_ENABLE, 0)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to disable torque: {follower_packet_handler.getTxRxResult(result)}")
        return False

    # Reset to position control mode
    result, error = follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, ADDR_OPERATING_MODE, 0)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to set position control mode: {follower_packet_handler.getTxRxResult(result)}")
    else:
        print(f"  ✓ Set position control mode")

    # Set max torque to 100%
    result, error = follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, ADDR_MAX_TORQUE, 1023)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to set max torque: {follower_packet_handler.getTxRxResult(result)}")
    else:
        print(f"  ✓ Set max torque to 100%")

    # Set goal speed to medium-fast value
    result, error = follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, ADDR_GOAL_SPEED, 500)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to set goal speed: {follower_packet_handler.getTxRxResult(result)}")
    else:
        print(f"  ✓ Set goal speed")

    # Set return delay time to minimum
    result, error = follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, ADDR_RETURN_DELAY, 0)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to set return delay: {follower_packet_handler.getTxRxResult(result)}")
    else:
        print(f"  ✓ Set return delay to minimum")

    # Set compliance P gain (control stiffness)
    try:
        result, error = follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, ADDR_COMPLIANCE_P_GAIN, 32)
        if result != scs.COMM_SUCCESS:
            print(f"  ✗ Failed to set P gain: {follower_packet_handler.getTxRxResult(result)}")
        else:
            print(f"  ✓ Set P gain")
    except Exception as e:
        print(f"  ✗ Error setting P gain: {e}")

    # Set compliance margin (deadband, lower is more precise)
    try:
        result, error = follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, ADDR_COMPLIANCE_MARGIN, 0)
        if result != scs.COMM_SUCCESS:
            print(f"  ✗ Failed to set compliance margin: {follower_packet_handler.getTxRxResult(result)}")
        else:
            print(f"  ✓ Set compliance margin")
    except Exception as e:
        print(f"  ✗ Error setting compliance margin: {e}")

    # Set punch (minimum current, higher means more power/less precision)
    try:
        result, error = follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, ADDR_PUNCH, 200)
        if result != scs.COMM_SUCCESS:
            print(f"  ✗ Failed to set punch: {follower_packet_handler.getTxRxResult(result)}")
        else:
            print(f"  ✓ Set punch")
    except Exception as e:
        print(f"  ✗ Error setting punch: {e}")

    # Reset alarm shutdown conditions
    try:
        result, error = follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, ADDR_ALARM_SHUTDOWN, 3)
        if result != scs.COMM_SUCCESS:
            print(f"  ✗ Failed to reset alarm: {follower_packet_handler.getTxRxResult(result)}")
        else:
            print(f"  ✓ Reset alarm shutdown conditions")
    except Exception as e:
        print(f"  ✗ Error resetting alarm: {e}")

    # Re-enable torque
    result, error = follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, ADDR_TORQUE_ENABLE, 1)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to enable torque: {follower_packet_handler.getTxRxResult(result)}")
        return False
    else:
        print(f"  ✓ Torque enabled")

    return True

def test_motor_movement(motor_id):
    """Test if motor can move to target position"""
    print(f"Testing movement on motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")

    # Read current position
    position, result, error = follower_packet_handler.read2ByteTxRx(follower_port_handler, motor_id, ADDR_PRESENT_POSITION)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to read position: {follower_packet_handler.getTxRxResult(result)}")
        return False

    print(f"  Current position: {position}")

    # Move 100 steps clockwise
    target_position = (position + 100) % 4096
    print(f"  Moving to position: {target_position}")

    result, error = follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, ADDR_GOAL_POSITION, target_position)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to send command: {follower_packet_handler.getTxRxResult(result)}")
        return False

    # Wait for movement
    time.sleep(1)

    # Read new position
    new_position, result, error = follower_packet_handler.read2ByteTxRx(follower_port_handler, motor_id, ADDR_PRESENT_POSITION)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to read new position: {follower_packet_handler.getTxRxResult(result)}")
        return False

    print(f"  New position: {new_position}")

    # Calculate difference
    diff = abs(new_position - target_position)
    if diff < 20:
        print(f"  ✓ Motor moved successfully! (Difference: {diff})")
        success = True
    else:
        print(f"  ✗ Motor did not move correctly (Difference: {diff})")
        success = False

    # Return to original position
    result, error = follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, ADDR_GOAL_POSITION, position)
    if result != scs.COMM_SUCCESS:
        print(f"  ✗ Failed to return to original position: {follower_packet_handler.getTxRxResult(result)}")
    else:
        print(f"  ✓ Returned to original position")
        time.sleep(1)

    return success

def read_motor_status(motor_id):
    """Read and display detailed motor status"""
    print(f"Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}) status:")

    try:
        # Read position
        position, pos_result, _ = follower_packet_handler.read2ByteTxRx(follower_port_handler, motor_id, ADDR_PRESENT_POSITION)
        if pos_result == scs.COMM_SUCCESS:
            print(f"  Position: {position}")
        else:
            print(f"  Position: ERROR")

        # Read operating mode
        mode, mode_result, _ = follower_packet_handler.read1ByteTxRx(follower_port_handler, motor_id, ADDR_OPERATING_MODE)
        if mode_result == scs.COMM_SUCCESS:
            mode_str = "Position Control" if mode == 0 else f"Other Mode ({mode})"
            print(f"  Operating Mode: {mode_str}")
        else:
            print(f"  Operating Mode: ERROR")

        # Read torque status
        torque, torque_result, _ = follower_packet_handler.read1ByteTxRx(follower_port_handler, motor_id, ADDR_TORQUE_ENABLE)
        if torque_result == scs.COMM_SUCCESS:
            status = "ENABLED" if torque == 1 else "DISABLED"
            print(f"  Torque: {status}")
        else:
            print(f"  Torque: ERROR")

        # Read max torque
        max_torque, max_torque_result, _ = follower_packet_handler.read2ByteTxRx(follower_port_handler, motor_id, ADDR_MAX_TORQUE)
        if max_torque_result == scs.COMM_SUCCESS:
            print(f"  Max Torque: {max_torque}/1023 ({max_torque/10.23:.1f}%)")
        else:
            print(f"  Max Torque: ERROR")

        # Read voltage
        voltage, voltage_result, _ = follower_packet_handler.read1ByteTxRx(follower_port_handler, motor_id, 62)  # Voltage at register 62
        if voltage_result == scs.COMM_SUCCESS:
            print(f"  Voltage: {voltage/10.0}V")
        else:
            print(f"  Voltage: ERROR")

        # Read temperature
        temp, temp_result, _ = follower_packet_handler.read1ByteTxRx(follower_port_handler, motor_id, 63)  # Temperature at register 63
        if temp_result == scs.COMM_SUCCESS:
            print(f"  Temperature: {temp}°C")
        else:
            print(f"  Temperature: ERROR")

    except Exception as e:
        print(f"  Error reading status: {e}")

def set_to_center_position():
    """Set all follower motors to center position"""
    print("\nSetting all motors to center position...")

    for motor_id in MOTOR_IDS:
        print(f"Moving motor {motor_id} to center position ({CENTER_POSITION})...")

        # Enable torque first
        result, error = follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, ADDR_TORQUE_ENABLE, 1)
        if result != scs.COMM_SUCCESS:
            print(f"  ✗ Failed to enable torque: {follower_packet_handler.getTxRxResult(result)}")
            continue

        # Set position to center
        result, error = follower_packet_handler.write2ByteTxRx(follower_port_handler, motor_id, ADDR_GOAL_POSITION, CENTER_POSITION)
        if result != scs.COMM_SUCCESS:
            print(f"  ✗ Failed to send command: {follower_packet_handler.getTxRxResult(result)}")
        else:
            print(f"  ✓ Command sent successfully")

    # Wait for movement to complete
    print("Waiting for movement to complete...")
    time.sleep(3)

    # Check final positions
    print("\nVerifying final positions:")
    for motor_id in MOTOR_IDS:
        position, result, error = follower_packet_handler.read2ByteTxRx(follower_port_handler, motor_id, ADDR_PRESENT_POSITION)
        if result == scs.COMM_SUCCESS:
            diff = abs(position - CENTER_POSITION)
            if diff < 20:
                print(f"  ✓ Motor {motor_id} at position {position} (diff: {diff})")
            else:
                print(f"  ✗ Motor {motor_id} at position {position}, off target by {diff}")
        else:
            print(f"  ✗ Failed to read position of motor {motor_id}: {follower_packet_handler.getTxRxResult(result)}")

def main():
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    print("=== SO-101 Follower Motor Reset Tool ===")

    # Open port
    if not open_port():
        print("Failed to open port. Exiting...")
        return

    try:
        # Read initial status
        print("\n=== Initial Motor Status ===")
        for motor_id in MOTOR_IDS:
            read_motor_status(motor_id)
            print()

        # Reset all motors
        print("\n=== Resetting Motor Parameters ===")
        for motor_id in MOTOR_IDS:
            reset_motor(motor_id)
            print()

        # Test movement
        print("\n=== Testing Motor Movement ===")
        for motor_id in MOTOR_IDS:
            test_motor_movement(motor_id)
            print()

        # Set to center position
        set_to_center_position()

        # Read final status
        print("\n=== Final Motor Status ===")
        for motor_id in MOTOR_IDS:
            read_motor_status(motor_id)
            print()

        print("\nMotor reset and test complete!")
        print("You can now run the teleoperation script.")

    finally:
        # Clean up
        follower_port_handler.closePort()
        print("Port closed.")

if __name__ == "__main__":
    main()

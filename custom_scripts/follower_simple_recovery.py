"""
SO-101 Follower Simple Recovery

This script just tries a few simple operations to verify basic communication
with the follower arm and attempt to enable torque on the motors.
"""

import sys
import os
import time

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

# Initialize port handlers
port_handler = scs.PortHandler(FOLLOWER_PORT)
packet_handler = scs.PacketHandler(PROTOCOL)

def open_port():
    """Open the follower port"""
    try:
        if port_handler.openPort():
            print(f"✓ Successfully opened port {FOLLOWER_PORT}")
        else:
            print(f"✗ Failed to open port {FOLLOWER_PORT}")
            return False

        if port_handler.setBaudRate(BAUDRATE):
            print(f"✓ Changed baudrate to {BAUDRATE}")
        else:
            print(f"✗ Failed to change baudrate")
            port_handler.closePort()
            return False

        return True
    except Exception as e:
        print(f"✗ Error with port: {e}")
        return False

def reboot_motor(motor_id):
    """Try to reboot the motor"""
    print(f"Attempting to reboot motor {motor_id}...")
    try:
        # The reboot command can vary by servo model, trying common ones
        result, error = packet_handler.reboot(port_handler, motor_id)
        if result == scs.COMM_SUCCESS:
            print(f"  ✓ Successfully sent reboot command to motor {motor_id}")
            return True
        else:
            print(f"  ✗ Failed to reboot motor {motor_id}: {packet_handler.getTxRxResult(result)}")
            return False
    except Exception as e:
        print(f"  ✗ Exception rebooting motor {motor_id}: {e}")
        return False

def ping_motor(motor_id):
    """Ping a motor to check if it's responsive"""
    print(f"Pinging motor {motor_id}...")

    try:
        comm_result = packet_handler.ping(port_handler, motor_id)
        if comm_result[0] == scs.COMM_SUCCESS:
            print(f"  ✓ Motor {motor_id} responded to ping! Model: {comm_result[1]}")
            return True
        else:
            print(f"  ✗ Failed to ping motor {motor_id}: {packet_handler.getTxRxResult(comm_result[0])}")
            return False
    except Exception as e:
        print(f"  ✗ Exception pinging motor {motor_id}: {e}")
        return False

def try_enable_torque(motor_id):
    """Try to enable torque on a motor"""
    print(f"Enabling torque on motor {motor_id}...")

    # Try to disable first (sometime helps reset state)
    try:
        result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 40, 0)  # 40 = Torque Enable
        if result != scs.COMM_SUCCESS:
            print(f"  Failed to disable torque: {packet_handler.getTxRxResult(result)}")
        time.sleep(0.1)
    except:
        pass

    # Try to enable
    try:
        result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 40, 1)  # 40 = Torque Enable
        if result == scs.COMM_SUCCESS:
            print(f"  ✓ Successfully enabled torque on motor {motor_id}")
            return True
        else:
            print(f"  ✗ Failed to enable torque: {packet_handler.getTxRxResult(result)}")
            return False
    except Exception as e:
        print(f"  ✗ Exception enabling torque: {e}")
        return False

def try_move_motor(motor_id, position):
    """Try to move a motor to a position"""
    print(f"Moving motor {motor_id} to position {position}...")

    try:
        result, error = packet_handler.write2ByteTxRx(port_handler, motor_id, 42, position)  # 42 = Goal Position
        if result == scs.COMM_SUCCESS:
            print(f"  ✓ Successfully sent move command to motor {motor_id}")
            return True
        else:
            print(f"  ✗ Failed to send move command: {packet_handler.getTxRxResult(result)}")
            return False
    except Exception as e:
        print(f"  ✗ Exception moving motor: {e}")
        return False

def read_position(motor_id):
    """Try to read the position of a motor"""
    print(f"Reading position of motor {motor_id}...")

    try:
        position, result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)  # 56 = Present Position
        if result == scs.COMM_SUCCESS:
            print(f"  ✓ Position: {position}")
            return position
        else:
            print(f"  ✗ Failed to read position: {packet_handler.getTxRxResult(result)}")
            return None
    except Exception as e:
        print(f"  ✗ Exception reading position: {e}")
        return None

def main():
    print("=== SO-101 Follower Simple Recovery Tool ===")

    if not open_port():
        print("Failed to open port. Exiting...")
        return

    try:
        # Step 1: Ping all motors
        print("\n=== Testing Motor Communication ===")
        responsive_motors = []
        for motor_id in MOTOR_IDS:
            if ping_motor(motor_id):
                responsive_motors.append(motor_id)

        if not responsive_motors:
            print("\nNo motors responded to ping. Check connections and power.")
            return

        print(f"\nResponsive motors: {responsive_motors}")

        # Step 2: Try rebooting motors
        print("\n=== Rebooting Motors ===")
        for motor_id in responsive_motors:
            reboot_motor(motor_id)

        # Wait for reboot
        print("Waiting for motors to reboot...")
        time.sleep(2)

        # Step 3: Try enabling torque on all responsive motors
        print("\n=== Enabling Torque ===")
        torque_enabled_motors = []
        for motor_id in responsive_motors:
            if try_enable_torque(motor_id):
                torque_enabled_motors.append(motor_id)

        print(f"\nMotors with torque enabled: {torque_enabled_motors}")

        # Step 4: Read positions
        print("\n=== Reading Positions ===")
        positions = {}
        for motor_id in responsive_motors:
            position = read_position(motor_id)
            if position is not None:
                positions[motor_id] = position

        print(f"\nCurrent positions: {positions}")

        # Step 5: Try moving motors
        if torque_enabled_motors:
            print("\n=== Testing Movement ===")
            for motor_id in torque_enabled_motors:
                current_pos = positions.get(motor_id)
                if current_pos is not None:
                    target_pos = (current_pos + 100) % 4096
                else:
                    target_pos = 2048  # Center position

                if try_move_motor(motor_id, target_pos):
                    print("  Waiting for movement...")
                    time.sleep(1)
                    new_pos = read_position(motor_id)
                    if new_pos is not None:
                        diff = abs(new_pos - target_pos)
                        if diff < 20:
                            print(f"  ✓ Motor {motor_id} moved successfully! (Position: {new_pos}, Difference: {diff})")
                        else:
                            print(f"  ✗ Motor {motor_id} didn't move correctly (Position: {new_pos}, Difference: {diff})")

        # Step 6: Try to center all motors
        print("\n=== Moving All Motors to Center ===")
        for motor_id in responsive_motors:
            try_enable_torque(motor_id)
            if try_move_motor(motor_id, 2048):  # 2048 = Center position
                print(f"  Moving motor {motor_id} to center position...")

        print("Waiting for movement to complete...")
        time.sleep(3)

        # Read final positions
        print("\n=== Final Positions ===")
        for motor_id in responsive_motors:
            read_position(motor_id)

    finally:
        port_handler.closePort()
        print("\nPort closed. Recovery attempts complete.")

if __name__ == "__main__":
    main()

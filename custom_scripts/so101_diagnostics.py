"""
SO-101 Diagnostic Tool

This script will help diagnose issues with the teleoperation between leader and follower arms.
It performs individual tests on:
1. Leader arm motor response
2. Follower arm motor response
3. Ability to write positions to follower
4. Monitoring changes in leader position

Usage:
    python so101_diagnostics.py
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
LEADER_PORT = "COM3"
FOLLOWER_PORT = "COM4"
BAUDRATE = 1000000
PROTOCOL = 0  # Protocol 0 for SCServo SCS

# Control parameters
MOTOR_IDS = list(range(1, 7))  # Motors 1-6
CENTER_POSITION = 2048  # Center position (0 degree)

def signal_handler(sig, frame):
    print("\nExiting program...")
    sys.exit(0)

def test_ports():
    """Test port connections"""
    print("\n=== Testing Port Connections ===")

    # Test leader port
    leader_port = scs.PortHandler(LEADER_PORT)
    if leader_port.openPort():
        print(f"✓ Successfully opened leader port {LEADER_PORT}")
        if leader_port.setBaudRate(BAUDRATE):
            print(f"✓ Changed leader baudrate to {BAUDRATE}")
        else:
            print(f"✗ Failed to change leader baudrate")
        leader_port.closePort()
    else:
        print(f"✗ Failed to open leader port {LEADER_PORT}")

    # Test follower port
    follower_port = scs.PortHandler(FOLLOWER_PORT)
    if follower_port.openPort():
        print(f"✓ Successfully opened follower port {FOLLOWER_PORT}")
        if follower_port.setBaudRate(BAUDRATE):
            print(f"✓ Changed follower baudrate to {BAUDRATE}")
        else:
            print(f"✗ Failed to change follower baudrate")
        follower_port.closePort()
    else:
        print(f"✗ Failed to open follower port {FOLLOWER_PORT}")

def test_leader_motors():
    """Test leader arm motors"""
    print("\n=== Testing Leader Arm Motors ===")

    leader_port = scs.PortHandler(LEADER_PORT)
    leader_packet = scs.PacketHandler(PROTOCOL)

    if not leader_port.openPort():
        print(f"✗ Failed to open leader port {LEADER_PORT}")
        return

    if not leader_port.setBaudRate(BAUDRATE):
        print(f"✗ Failed to change leader baudrate")
        leader_port.closePort()
        return

    # Test each motor
    for motor_id in MOTOR_IDS:
        # Try to read present position
        position, result, error = leader_packet.read2ByteTxRx(leader_port, motor_id, 56)  # Read present position (address 56)
        if result == scs.COMM_SUCCESS:
            print(f"✓ Motor {motor_id} responded with position: {position}")

            # Try to read additional info
            torque, torque_res, _ = leader_packet.read1ByteTxRx(leader_port, motor_id, 50)  # Read torque enable
            if torque_res == scs.COMM_SUCCESS:
                print(f"  - Torque status: {'Enabled' if torque else 'Disabled'}")

            # Try to read voltage
            voltage, voltage_res, _ = leader_packet.read1ByteTxRx(leader_port, motor_id, 62)  # Read voltage
            if voltage_res == scs.COMM_SUCCESS:
                print(f"  - Voltage: {voltage/10.0}V")
        else:
            print(f"✗ Motor {motor_id} did not respond: {leader_packet.getTxRxResult(result)}")

    leader_port.closePort()

def test_follower_motors():
    """Test follower arm motors"""
    print("\n=== Testing Follower Arm Motors ===")

    follower_port = scs.PortHandler(FOLLOWER_PORT)
    follower_packet = scs.PacketHandler(PROTOCOL)

    if not follower_port.openPort():
        print(f"✗ Failed to open follower port {FOLLOWER_PORT}")
        return

    if not follower_port.setBaudRate(BAUDRATE):
        print(f"✗ Failed to change follower baudrate")
        follower_port.closePort()
        return

    # Test each motor
    for motor_id in MOTOR_IDS:
        # Try to read present position
        position, result, error = follower_packet.read2ByteTxRx(follower_port, motor_id, 56)  # Read present position (address 56)
        if result == scs.COMM_SUCCESS:
            print(f"✓ Motor {motor_id} responded with position: {position}")

            # Try to read torque status
            torque, torque_res, _ = follower_packet.read1ByteTxRx(follower_port, motor_id, 50)  # Read torque enable
            if torque_res == scs.COMM_SUCCESS:
                print(f"  - Torque status: {'Enabled' if torque else 'Disabled'}")

            # Try to read voltage
            voltage, voltage_res, _ = follower_packet.read1ByteTxRx(follower_port, motor_id, 62)  # Read voltage
            if voltage_res == scs.COMM_SUCCESS:
                print(f"  - Voltage: {voltage/10.0}V")
        else:
            print(f"✗ Motor {motor_id} did not respond: {follower_packet.getTxRxResult(result)}")

    follower_port.closePort()

def test_follower_movement():
    """Test follower arm movement"""
    print("\n=== Testing Follower Arm Movement ===")

    follower_port = scs.PortHandler(FOLLOWER_PORT)
    follower_packet = scs.PacketHandler(PROTOCOL)

    if not follower_port.openPort():
        print(f"✗ Failed to open follower port {FOLLOWER_PORT}")
        return

    if not follower_port.setBaudRate(BAUDRATE):
        print(f"✗ Failed to change follower baudrate")
        follower_port.closePort()
        return

    # Test each motor with a small movement
    for motor_id in MOTOR_IDS:
        # Read current position first
        current_pos, result, error = follower_packet.read2ByteTxRx(follower_port, motor_id, 56)
        if result != scs.COMM_SUCCESS:
            print(f"✗ Failed to read position from motor {motor_id}")
            continue

        # Enable torque
        print(f"Enabling torque for motor {motor_id}...")
        torque_result, _ = follower_packet.write1ByteTxRx(follower_port, motor_id, 50, 1)
        if torque_result != scs.COMM_SUCCESS:
            print(f"✗ Failed to enable torque on motor {motor_id}")
            continue

        # Set goal position to current + small offset (if safe)
        target_pos = min(max(current_pos + 50, 0), 4095)  # Stay within safe limits
        print(f"Moving motor {motor_id} from {current_pos} to {target_pos}...")

        move_result, _ = follower_packet.write2ByteTxRx(follower_port, motor_id, 60, target_pos)
        if move_result != scs.COMM_SUCCESS:
            print(f"✗ Failed to write position to motor {motor_id}")
        else:
            print(f"✓ Command sent to motor {motor_id}")

            # Wait for movement
            time.sleep(1)

            # Read new position
            new_pos, read_result, _ = follower_packet.read2ByteTxRx(follower_port, motor_id, 56)
            if read_result == scs.COMM_SUCCESS:
                difference = abs(new_pos - target_pos)
                if difference < 20:
                    print(f"✓ Motor {motor_id} moved to {new_pos} (target: {target_pos})")
                else:
                    print(f"✗ Motor {motor_id} moved to {new_pos}, but is off target by {difference}")
            else:
                print(f"✗ Failed to read new position from motor {motor_id}")

        # Return to original position
        follower_packet.write2ByteTxRx(follower_port, motor_id, 60, current_pos)
        time.sleep(1)

        # Disable torque
        follower_packet.write1ByteTxRx(follower_port, motor_id, 50, 0)

    follower_port.closePort()

def monitor_leader_positions():
    """Monitor leader arm positions for a few seconds to check if they change when moved manually"""
    print("\n=== Monitoring Leader Arm Positions ===")
    print("Please move the leader arm physically during the next 10 seconds...")

    leader_port = scs.PortHandler(LEADER_PORT)
    leader_packet = scs.PacketHandler(PROTOCOL)

    if not leader_port.openPort():
        print(f"✗ Failed to open leader port {LEADER_PORT}")
        return

    if not leader_port.setBaudRate(BAUDRATE):
        print(f"✗ Failed to change leader baudrate")
        leader_port.closePort()
        return

    # First reading of positions
    initial_positions = []
    for motor_id in MOTOR_IDS:
        position, result, _ = leader_packet.read2ByteTxRx(leader_port, motor_id, 56)
        if result == scs.COMM_SUCCESS:
            initial_positions.append(position)
        else:
            initial_positions.append(None)
            print(f"✗ Could not read initial position of motor {motor_id}")

    print(f"Initial positions: {initial_positions}")
    print("Move the leader arm now...")

    # Monitor for changes
    changed_motors = [False] * len(MOTOR_IDS)
    start_time = time.time()

    while time.time() - start_time < 10:  # Monitor for 10 seconds
        for i, motor_id in enumerate(MOTOR_IDS):
            position, result, _ = leader_packet.read2ByteTxRx(leader_port, motor_id, 56)
            if result == scs.COMM_SUCCESS:
                if initial_positions[i] is not None and abs(position - initial_positions[i]) > 10:
                    changed_motors[i] = True

        # Print progress
        print(f"Monitoring: {'.' * int((time.time() - start_time))} {int(time.time() - start_time)}s", end="\r")
        time.sleep(0.2)

    print("\nMonitoring complete!")

    # Print results
    print("Motors that registered movement:")
    for i, motor_id in enumerate(MOTOR_IDS):
        status = "✓ Changed" if changed_motors[i] else "✗ No change detected"
        print(f"Motor {motor_id}: {status}")

    leader_port.closePort()

def check_teleoperation_prerequisites():
    """Check all prerequisites for teleoperation"""
    print("\n=== Checking Teleoperation Prerequisites ===")

    # Check leader arm
    leader_port = scs.PortHandler(LEADER_PORT)
    leader_packet = scs.PacketHandler(PROTOCOL)

    if not leader_port.openPort():
        print(f"✗ Leader port {LEADER_PORT} not available")
        return False

    if not leader_port.setBaudRate(BAUDRATE):
        print(f"✗ Failed to set leader baudrate")
        leader_port.closePort()
        return False

    leader_motors_working = True
    for motor_id in MOTOR_IDS:
        _, result, _ = leader_packet.read2ByteTxRx(leader_port, motor_id, 56)
        if result != scs.COMM_SUCCESS:
            leader_motors_working = False
            print(f"✗ Leader motor {motor_id} not responding")

    if leader_motors_working:
        print(f"✓ All leader motors responding")

    # Check follower arm
    follower_port = scs.PortHandler(FOLLOWER_PORT)
    follower_packet = scs.PacketHandler(PROTOCOL)

    if not follower_port.openPort():
        print(f"✗ Follower port {FOLLOWER_PORT} not available")
        leader_port.closePort()
        return False

    if not follower_port.setBaudRate(BAUDRATE):
        print(f"✗ Failed to set follower baudrate")
        leader_port.closePort()
        follower_port.closePort()
        return False

    follower_motors_working = True
    for motor_id in MOTOR_IDS:
        _, result, _ = follower_packet.read2ByteTxRx(follower_port, motor_id, 56)
        if result != scs.COMM_SUCCESS:
            follower_motors_working = False
            print(f"✗ Follower motor {motor_id} not responding")

    if follower_motors_working:
        print(f"✓ All follower motors responding")

    # Check follower motor torque capability
    torque_working = True
    for motor_id in MOTOR_IDS:
        # Try to enable torque
        result, _ = follower_packet.write1ByteTxRx(follower_port, motor_id, 50, 1)
        if result != scs.COMM_SUCCESS:
            torque_working = False
            print(f"✗ Cannot enable torque on follower motor {motor_id}")

        # Set back to disabled
        follower_packet.write1ByteTxRx(follower_port, motor_id, 50, 0)

    if torque_working:
        print(f"✓ Torque control working on all follower motors")

    leader_port.closePort()
    follower_port.closePort()

    all_good = leader_motors_working and follower_motors_working and torque_working
    if all_good:
        print("\n✓ All prerequisites for teleoperation met!")
    else:
        print("\n✗ Some prerequisites for teleoperation not met.")

    return all_good

def main():
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    print("=== SO-101 Diagnostics Tool ===\n")
    print("Running comprehensive diagnostics on both leader and follower arms...")

    # Run diagnostic tests
    test_ports()
    test_leader_motors()
    test_follower_motors()
    test_follower_movement()
    monitor_leader_positions()
    check_teleoperation_prerequisites()

    print("\nDiagnostic tests complete!")

if __name__ == "__main__":
    main()

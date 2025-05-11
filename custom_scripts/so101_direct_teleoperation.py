"""
SO-101 Direct Teleoperation Fix

This script implements a more direct approach to teleoperation by:
1. Using lower-level commands to directly write positions
2. Implementing a better calibration system
3. Including more detailed diagnostics
4. Using a different protocol approach that worked in the follower_test_fixed.py script

Usage:
    python so101_direct_teleoperation.py
"""

import sys
import os
import time
import signal
import keyboard  # pip install keyboard
import threading
import serial

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
UPDATE_FREQUENCY = 0.05  # seconds
MOTOR_IDS = list(range(1, 7))  # Motors 1-6
DEBUG_MODE = False
DIRECT_MODE = True  # Use direct serial commands instead of SDK
CENTER_POSITION = 2048  # Center position (0 degree)

# Motor names for readability
MOTOR_NAMES = {
    1: "Shoulder Pan",
    2: "Shoulder Lift",
    3: "Elbow Flex",
    4: "Wrist Flex",
    5: "Wrist Roll",
    6: "Gripper"
}

# Global variables
leader_port_handler = scs.PortHandler(LEADER_PORT)
leader_packet_handler = scs.PacketHandler(PROTOCOL)
follower_port_handler = scs.PortHandler(FOLLOWER_PORT)
follower_packet_handler = scs.PacketHandler(PROTOCOL)
teleoperation_active = True
position_offsets = [0, 0, 0, 0, 0, 0]  # Offsets between leader and follower
leader_serial = None
follower_serial = None
lock = threading.Lock()

def signal_handler(sig, frame):
    """Clean up on exit"""
    print("\nExiting program...")
    disable_all_motors()
    close_ports()
    sys.exit(0)

def close_ports():
    """Close all ports"""
    if leader_port_handler:
        leader_port_handler.closePort()
    if follower_port_handler:
        follower_port_handler.closePort()
    if leader_serial:
        try:
            leader_serial.close()
        except:
            pass
    if follower_serial:
        try:
            follower_serial.close()
        except:
            pass
    print("All ports closed.")

def open_ports():
    """Open communication ports for both arms"""
    global leader_serial, follower_serial, DIRECT_MODE
    
    success = True
    
    if not DIRECT_MODE:
        # Use SDK mode only
        # Open leader port using SDK
        try:
            if leader_port_handler.openPort():
                print(f"✓ Successfully opened leader port {LEADER_PORT}")
            else:
                print(f"✗ Failed to open leader port {LEADER_PORT}")
                success = False
            
            if leader_port_handler.setBaudRate(BAUDRATE):
                print(f"✓ Changed leader baudrate to {BAUDRATE}")
            else:
                print(f"✗ Failed to change leader baudrate")
                leader_port_handler.closePort()
                success = False
        except Exception as e:
            print(f"✗ Error with leader port: {e}")
            success = False
        
        # Open follower port using SDK
        try:
            if follower_port_handler.openPort():
                print(f"✓ Successfully opened follower port {FOLLOWER_PORT}")
            else:
                print(f"✗ Failed to open follower port {FOLLOWER_PORT}")
                success = False
            
            if follower_port_handler.setBaudRate(BAUDRATE):
                print(f"✓ Changed follower baudrate to {BAUDRATE}")
            else:
                print(f"✗ Failed to change follower baudrate")
                follower_port_handler.closePort()
                success = False
        except Exception as e:
            print(f"✗ Error with follower port: {e}")
            success = False
    else:
        # Use direct serial mode
        try:
            # We'll only use direct serial communication
            print("Using direct serial mode...")
            leader_serial = serial.Serial(LEADER_PORT, BAUDRATE, timeout=0.1)
            print(f"✓ Successfully opened direct leader serial port")
            follower_serial = serial.Serial(FOLLOWER_PORT, BAUDRATE, timeout=0.1)
            print(f"✓ Successfully opened direct follower serial port")
        except Exception as e:
            print(f"✗ Error opening direct serial ports: {e}")
            # Try to fall back to SDK mode
            print("Falling back to SDK mode...")
            DIRECT_MODE = False
            return open_ports()  # Recursively try again in SDK mode

    return success

def disable_all_motors():
    """Disable torque for all follower motors"""
    print("Disabling torque for all motors...")

    if DIRECT_MODE and follower_serial:
        # Direct mode using serial
        for motor_id in MOTOR_IDS:
            # Format for write1Byte: 0xFF 0xFF ID LENGTH INSTRUCTION PARAM1 ... CHECKSUM
            # Torque off: 0xFF 0xFF ID 0x04 0x03 0x28 0x00 CHECKSUM
            # (0x28 = register 40 = Torque Enable, 0x00 = value to write)
            checksum = 0xFF - ((motor_id + 0x04 + 0x03 + 0x28 + 0x00) % 256)
            command = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 0x28, 0x00, checksum])
            try:
                follower_serial.write(command)
                time.sleep(0.01)
                follower_serial.read(follower_serial.in_waiting or 1)  # Clear buffer
            except:
                pass  # Ignore errors during shutdown
    else:
        # SDK mode
        try:
            for motor_id in MOTOR_IDS:
                follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 40, 0)
        except:
            pass  # Ignore errors during shutdown

def read_leader_positions():
    """Read positions from leader arm"""
    positions = []
    errors = 0

    for motor_id in MOTOR_IDS:
        try:
            position, result, _ = leader_packet_handler.read2ByteTxRx(
                leader_port_handler, motor_id, 56)  # Read present position (address 56)

            if result == scs.COMM_SUCCESS:
                positions.append(position)
                if DEBUG_MODE:
                    print(f"Read leader motor {motor_id}: {position}")
            else:
                error_msg = leader_packet_handler.getTxRxResult(result)
                if DEBUG_MODE:
                    print(f"Failed to read position from leader motor {motor_id}: {error_msg}")
                positions.append(2048)  # Use center position as fallback
                errors += 1
        except Exception as e:
            if DEBUG_MODE:
                print(f"Exception reading leader motor {motor_id}: {e}")
            positions.append(2048)
            errors += 1

    if errors > 0 and DEBUG_MODE:
        print(f"Warning: {errors}/{len(MOTOR_IDS)} leader motor reads failed")

    return positions

def set_follower_positions(positions):
    """Set positions for follower arm, with both direct mode and SDK as fallback"""
    success_count = 0

    if DIRECT_MODE and follower_serial:
        # Direct mode using serial
        for motor_id, position in zip(MOTOR_IDS, positions):
            # Format for write2Byte: 0xFF 0xFF ID LENGTH INSTRUCTION PARAM1 PARAM2 PARAM3 CHECKSUM
            # Position write: 0xFF 0xFF ID 0x05 0x03 0x2A POS_L POS_H CHECKSUM
            # (0x2A = register 42 = Goal Position, POS_L and POS_H are low and high bytes of position)
            pos_l = position & 0xFF  # Low byte
            pos_h = (position >> 8) & 0xFF  # High byte
            checksum = 0xFF - ((motor_id + 0x05 + 0x03 + 0x2A + pos_l + pos_h) % 256)
            command = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 0x2A, pos_l, pos_h, checksum])

            try:
                if DEBUG_MODE:
                    print(f"Setting motor {motor_id} to position {position}")
                    print(f"Command: {' '.join([hex(b) for b in command])}")

                follower_serial.write(command)
                time.sleep(0.01)  # Small delay between commands

                # Clear buffer, but we don't need the response
                if follower_serial.in_waiting:
                    follower_serial.read(follower_serial.in_waiting)

                success_count += 1
            except Exception as e:
                if DEBUG_MODE:
                    print(f"Exception setting follower motor {motor_id}: {e}")
    else:
        # SDK mode as fallback
        for motor_id, position in zip(MOTOR_IDS, positions):
            try:
                # Ensure position is within valid range
                safe_position = max(0, min(4095, int(position)))

                # Write goal position (address 42)
                result, _ = follower_packet_handler.write2ByteTxRx(
                    follower_port_handler, motor_id, 42, safe_position)

                if result == scs.COMM_SUCCESS:
                    success_count += 1
                    if DEBUG_MODE:
                        print(f"Motor {motor_id} moved to {safe_position}")
            except Exception as e:
                if DEBUG_MODE:
                    print(f"Exception moving motor {motor_id}: {e}")

    if DEBUG_MODE and success_count != len(MOTOR_IDS):
        print(f"Only {success_count}/{len(MOTOR_IDS)} follower motors were successfully moved")

    return success_count

def enable_all_follower_motors():
    """Enable torque for all follower motors"""
    print("Enabling torque for all follower motors...")
    success_count = 0

    if DIRECT_MODE and follower_serial:
        # Direct mode using serial
        for motor_id in MOTOR_IDS:
            # Torque on: 0xFF 0xFF ID 0x04 0x03 0x28 0x01 CHECKSUM
            # (0x28 = register 40 = Torque Enable, 0x01 = value to write)
            checksum = 0xFF - ((motor_id + 0x04 + 0x03 + 0x28 + 0x01) % 256)
            command = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 0x28, 0x01, checksum])

            try:
                follower_serial.write(command)
                time.sleep(0.01)

                # Check for response
                if follower_serial.in_waiting:
                    response = follower_serial.read(follower_serial.in_waiting)
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        success_count += 1
                        if DEBUG_MODE:
                            print(f"Successfully enabled torque on motor {motor_id}")
            except Exception as e:
                if DEBUG_MODE:
                    print(f"Exception enabling motor {motor_id}: {e}")
    else:
        # SDK mode as fallback
        for motor_id in MOTOR_IDS:
            try:
                result, _ = follower_packet_handler.write1ByteTxRx(follower_port_handler, motor_id, 40, 1)
                if result == scs.COMM_SUCCESS:
                    success_count += 1
                    if DEBUG_MODE:
                        print(f"Successfully enabled torque on motor {motor_id}")
            except Exception as e:
                if DEBUG_MODE:
                    print(f"Exception enabling motor {motor_id}: {e}")

    if success_count == len(MOTOR_IDS):
        print("All follower motors enabled!")
    else:
        print(f"Only {success_count}/{len(MOTOR_IDS)} follower motors were enabled")

    return success_count

def ping_all_motors():
    """Ping all motors to check communication"""
    print("\n=== Testing Motor Communication ===")

    # Test leader motors
    print("Leader arm motors:")
    leader_success = 0
    for motor_id in MOTOR_IDS:
        try:
            model_number, comm_result, error = leader_packet_handler.ping(leader_port_handler, motor_id)
            if comm_result == scs.COMM_SUCCESS:
                print(f"  ✓ Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}) responded")
                leader_success += 1
            else:
                print(f"  ✗ Motor {motor_id} did not respond")
        except Exception as e:
            print(f"  ✗ Motor {motor_id}: Error {e}")

    print(f"Leader arm: {leader_success}/{len(MOTOR_IDS)} motors responding")

    # Test follower motors
    print("\nFollower arm motors:")
    follower_success = 0

    if DIRECT_MODE and follower_serial:
        # Use direct serial for follower
        for motor_id in MOTOR_IDS:
            try:
                # Basic ping packet: 0xFF 0xFF ID 0x02 0x01 CHECKSUM
                checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])

                follower_serial.write(ping_packet)
                time.sleep(0.1)  # Wait for response

                if follower_serial.in_waiting:
                    response = follower_serial.read(follower_serial.in_waiting)
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        print(f"  ✓ Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}) responded")
                        follower_success += 1
                    else:
                        print(f"  ✗ Motor {motor_id} invalid response: {' '.join([hex(b) for b in response])}")
                else:
                    print(f"  ✗ Motor {motor_id} did not respond")
            except Exception as e:
                print(f"  ✗ Motor {motor_id}: Error {e}")
    else:
        # Use SDK for follower
        for motor_id in MOTOR_IDS:
            try:
                model_number, comm_result, error = follower_packet_handler.ping(follower_port_handler, motor_id)
                if comm_result == scs.COMM_SUCCESS:
                    print(f"  ✓ Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}) responded")
                    follower_success += 1
                else:
                    print(f"  ✗ Motor {motor_id} did not respond")
            except Exception as e:
                print(f"  ✗ Motor {motor_id}: Error {e}")

    print(f"Follower arm: {follower_success}/{len(MOTOR_IDS)} motors responding")
    return leader_success, follower_success

def calibrate_offset():
    """Calibrate offset between leader and follower positions"""
    print("\n=== Calibrating Position Offsets ===")
    global position_offsets

    # Read current leader positions
    leader_positions = read_leader_positions()

    # Set offsets to move from current leader position to center position
    # This will make the follower start at center (2048)
    position_offsets = [CENTER_POSITION - l for l in leader_positions]

    print("Calibrated offsets:")
    for i, offset in enumerate(position_offsets):
        motor_id = i + 1
        print(f"Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')}): Leader {leader_positions[i]} -> Follower {leader_positions[i] + offset} (Offset: {offset})")

    print("Calibration complete!")
    return position_offsets

def test_follower_arm():
    """Test if the follower arm responds to commands"""
    print("\n=== Testing Follower Arm ===")

    # Ensure torque is enabled
    enable_all_follower_motors()

    # Test moving each motor
    for motor_id in MOTOR_IDS:
        print(f"Testing motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")

        # Move to center position
        if DIRECT_MODE and follower_serial:
            # Direct mode
            pos_l = CENTER_POSITION & 0xFF
            pos_h = (CENTER_POSITION >> 8) & 0xFF
            checksum = 0xFF - ((motor_id + 0x05 + 0x03 + 0x2A + pos_l + pos_h) % 256)
            command = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 0x2A, pos_l, pos_h, checksum])

            try:
                follower_serial.write(command)
                time.sleep(0.5)  # Allow time to move

                # Now check position
                # Read present position: 0xFF 0xFF ID 0x04 0x02 0x38 0x02 CHECKSUM
                # (0x38 = register 56 = Present Position, 0x02 = number of bytes to read)
                checksum = 0xFF - ((motor_id + 0x04 + 0x02 + 0x38 + 0x02) % 256)
                read_cmd = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x02, 0x38, 0x02, checksum])

                follower_serial.write(read_cmd)
                time.sleep(0.1)

                if follower_serial.in_waiting:
                    response = follower_serial.read(follower_serial.in_waiting)
                    if len(response) >= 8:  # Status packet with position
                        pos_low = response[5]
                        pos_high = response[6]
                        position = (pos_high << 8) + pos_low
                        print(f"  Position: {position}")

                        diff = abs(position - CENTER_POSITION)
                        if diff < 50:
                            print(f"  ✓ Motor responded correctly (within {diff} steps of target)")
                        else:
                            print(f"  ✗ Motor position is off by {diff} steps")
                    else:
                        print(f"  ✗ Invalid position response: {' '.join([hex(b) for b in response])}")
                else:
                    print("  ✗ No response from motor")
            except Exception as e:
                print(f"  ✗ Error: {e}")
        else:
            # SDK mode
            try:
                result, _ = follower_packet_handler.write2ByteTxRx(
                    follower_port_handler, motor_id, 42, CENTER_POSITION)

                if result == scs.COMM_SUCCESS:
                    print("  ✓ Command sent successfully")
                    time.sleep(0.5)  # Wait for movement

                    # Read position
                    position, read_result, _ = follower_packet_handler.read2ByteTxRx(
                        follower_port_handler, motor_id, 56)

                    if read_result == scs.COMM_SUCCESS:
                        diff = abs(position - CENTER_POSITION)
                        if diff < 50:
                            print(f"  ✓ Motor responded correctly (position: {position}, diff: {diff})")
                        else:
                            print(f"  ✗ Motor position is off by {diff} steps (position: {position})")
                    else:
                        print("  ✗ Failed to read position")
                else:
                    print("  ✗ Failed to send command")
            except Exception as e:
                print(f"  ✗ Error: {e}")

    print("Follower arm test complete!")

def reset_to_center():
    """Reset all follower motors to center position"""
    print("\nResetting follower arm to center position...")
    positions = [CENTER_POSITION] * len(MOTOR_IDS)
    set_follower_positions(positions)
    print("Reset command sent.")

def print_instructions():
    """Print the keyboard controls"""
    print("\n=== SO-101 Direct Teleoperation Controls ===")
    print("ESC: Exit program")
    print("SPACE: Toggle teleoperation (ON/OFF)")
    print("R: Reset follower to center position")
    print("D: Toggle debug information")
    print("C: Calibrate position offsets")
    print("T: Test follower arm responsiveness")
    print("P: Ping all motors")
    print("=====================================\n")

def print_status(leader_positions, is_active):
    """Print current status"""
    status = "ACTIVE" if is_active else "PAUSED"
    print(f"\rTeleoperation: {status} | ", end="")

    # Calculate positions that will be sent to follower
    follower_targets = [(leader_pos + offset) % 4096 for leader_pos, offset in zip(leader_positions, position_offsets)]

    for i, (leader_pos, follower_pos) in enumerate(zip(leader_positions, follower_targets)):
        motor_id = i + 1
        print(f"{motor_id}:{leader_pos}->{follower_pos} ", end="")

    print(" ", end="\r")  # Extra space to overwrite previous line
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
            reset_to_center()
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('d'):
            with lock:
                DEBUG_MODE = not DEBUG_MODE
                print(f"\nDebug mode {'enabled' if DEBUG_MODE else 'disabled'}")
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('c'):
            calibrate_offset()
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('t'):
            test_follower_arm()
            time.sleep(0.3)  # Debounce

        elif keyboard.is_pressed('p'):
            ping_all_motors()
            time.sleep(0.3)  # Debounce

        time.sleep(0.1)

def main():
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    print("=== SO-101 Direct Teleoperation Script ===")

    # Open communication ports
    if not open_ports():
        print("Failed to open ports. Exiting...")
        return

    print_instructions()

    # Test communication
    leader_success, follower_success = ping_all_motors()

    if leader_success == 0:
        print("No leader motors responding. Check connections and power.")
        close_ports()
        return

    if follower_success == 0:
        print("No follower motors responding. Check connections and power.")
        close_ports()
        return

    # Enable motors on follower arm
    print("\nEnabling follower motors...")
    enable_all_follower_motors()

    # Calibrate offsets initially
    calibrate_offset()

    # Test follower arm
    test_follower_arm()

    # Start keyboard monitoring in a separate thread
    keyboard_thread = threading.Thread(target=monitor_keyboard_input, daemon=True)
    keyboard_thread.start()

    # Reset to center to start
    reset_to_center()

    # Main loop
    print("\nStarting teleoperation. Move the leader arm to control the follower.")

    # Smooth the position changes with a simple moving average
    smoothed_positions = read_leader_positions()
    previous_positions = smoothed_positions.copy()

    try:
        while True:
            try:
                with lock:
                    current_teleoperation_active = teleoperation_active

                # Read leader positions
                leader_positions = read_leader_positions()

                # Apply smoothing only if values have changed significantly
                alpha = 0.2  # Low value = more smoothing
                smoothed_positions = [
                    alpha * current + (1 - alpha) * smoothed
                    for current, smoothed in zip(leader_positions, smoothed_positions)
                ]

                # Only send commands if position has changed enough
                position_changed = False
                for i, (current, previous) in enumerate(zip(smoothed_positions, previous_positions)):
                    if abs(current - previous) > 5:  # Threshold to avoid unnecessary commands
                        position_changed = True
                        break

                if current_teleoperation_active and position_changed:
                    # Apply offsets to convert leader positions to follower positions
                    follower_positions = [(int(pos) + offset) % 4096
                                         for pos, offset in zip(smoothed_positions, position_offsets)]

                    # Send positions to follower
                    set_follower_positions(follower_positions)

                    # Update previous positions
                    previous_positions = smoothed_positions.copy()

                # Print status periodically (every ~10 cycles)
                if not DEBUG_MODE and teleoperation_active:
                    print_status(leader_positions, current_teleoperation_active)

            except Exception as e:
                if DEBUG_MODE:
                    print(f"Error in main loop: {e}")

            time.sleep(UPDATE_FREQUENCY)

    except KeyboardInterrupt:
        print("\nProgram interrupted.")

    finally:
        # Clean up
        disable_all_motors()
        close_ports()
        print("Program terminated.")

if __name__ == "__main__":
    main()

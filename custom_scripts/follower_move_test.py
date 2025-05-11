"""
SO-101 Follower Basic Move Test

This script attempts to move the follower arm motors using direct serial commands
based on the approach in follower_test_fixed.py, which successfully pinged the motors.
"""

import sys
import os
import time
import serial

def test_follower_move(port_name="COM4", baudrate=1000000):
    """Test moving the follower arm motors"""
    print(f"Testing follower arm motor movement on {port_name} at {baudrate} baud...")

    try:
        # Try to open the port
        ser = serial.Serial(port_name, baudrate, timeout=0.5)
        print(f"Successfully opened {port_name}")

        # Test each motor ID from 1 to 6
        for motor_id in range(1, 7):
            print(f"\n=== Testing motor ID {motor_id} ===")

            # 1. First ping the motor
            checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
            ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])

            print(f"  Pinging motor ID {motor_id}...")
            ser.write(ping_packet)
            time.sleep(0.1)  # Wait for response

            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"  Response received: {' '.join([hex(b) for b in response])}")

                if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    print(f"  ✓ Valid ping response from motor ID {motor_id}")
                else:
                    print(f"  ✗ Invalid response format")
                    continue
            else:
                print(f"  ✗ No response from motor ID {motor_id}")
                continue

            # 2. Enable torque on the motor (register 40=0x28, value 1)
            print(f"  Enabling torque on motor ID {motor_id}...")
            checksum = 0xFF - ((motor_id + 0x04 + 0x03 + 0x28 + 0x01) % 256)
            torque_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 0x28, 0x01, checksum])
            ser.write(torque_packet)
            time.sleep(0.1)

            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"  Response: {' '.join([hex(b) for b in response])}")

            # 3. Read current position (register 56=0x38, 2 bytes)
            print(f"  Reading current position of motor ID {motor_id}...")
            checksum = 0xFF - ((motor_id + 0x04 + 0x02 + 0x38 + 0x02) % 256)
            read_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x02, 0x38, 0x02, checksum])
            ser.write(read_packet)
            time.sleep(0.1)

            current_pos = None
            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"  Response: {' '.join([hex(b) for b in response])}")

                if len(response) >= 8:
                    pos_low = response[5]
                    pos_high = response[6]
                    current_pos = (pos_high << 8) + pos_low
                    print(f"  Current position: {current_pos}")

            # 4. Try moving to center position (2048)
            center_pos = 2048
            pos_l = center_pos & 0xFF
            pos_h = (center_pos >> 8) & 0xFF

            print(f"  Moving motor ID {motor_id} to position {center_pos}...")
            checksum = 0xFF - ((motor_id + 0x05 + 0x03 + 0x2A + pos_l + pos_h) % 256)
            move_packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 0x2A, pos_l, pos_h, checksum])
            ser.write(move_packet)
            time.sleep(0.5)  # Give time to move

            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"  Response: {' '.join([hex(b) for b in response])}")

            # 5. Read position again to see if it changed
            print(f"  Reading new position of motor ID {motor_id}...")
            ser.write(read_packet)
            time.sleep(0.1)

            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"  Response: {' '.join([hex(b) for b in response])}")

                if len(response) >= 8:
                    pos_low = response[5]
                    pos_high = response[6]
                    new_pos = (pos_high << 8) + pos_low
                    print(f"  New position: {new_pos}")

                    if current_pos is not None:
                        if abs(new_pos - center_pos) < 50:
                            print(f"  ✓ Motor moved successfully to {new_pos}")
                        else:
                            print(f"  ✗ Motor did not move to target (difference: {abs(new_pos - center_pos)})")

            # 6. Disable torque
            print(f"  Disabling torque on motor ID {motor_id}...")
            checksum = 0xFF - ((motor_id + 0x04 + 0x03 + 0x28 + 0x00) % 256)
            torque_off_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 0x28, 0x00, checksum])
            ser.write(torque_off_packet)
            time.sleep(0.1)

            if ser.in_waiting:
                response = ser.read(ser.in_waiting)
                print(f"  Response: {' '.join([hex(b) for b in response])}")

        # Close the port
        ser.close()
        print(f"\nClosed {port_name}")
        return True

    except Exception as e:
        print(f"\nError testing {port_name}: {e}")
        return False

if __name__ == "__main__":
    print("=== SO-101 FOLLOWER ARM MOVEMENT TEST ===")
    success = test_follower_move()

    if success:
        print("\nTest completed! Check above for movement results.")
    else:
        print("\nTest failed. Check error message above.")

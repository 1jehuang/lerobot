import sys
import os
import time
import serial

def test_ports_swapped():
    """Test if COM3 and COM4 might be swapped in the configuration"""
    print("=== Testing Swapped Ports Configuration ===")
    
    try:
        # Try to open COM3 (which might be the follower arm)
        print("\nTesting COM3 as follower arm...")
        with serial.Serial("COM3", 1000000, timeout=0.5) as ser:
            print("Successfully opened COM3")
            
            # Try pinging all motors
            for motor_id in range(1, 7):
                # Basic ping packet for Feetech SCS motors
                checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                
                # Send ping and read response
                print(f"  Pinging motor ID {motor_id} on COM3...")
                ser.write(ping_packet)
                time.sleep(0.1)  # Wait for response
                
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"  Response received: {' '.join([hex(b) for b in response])}")
                    
                    # Check if response is valid for this motor ID
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        print(f"  SUCCESS! Valid response from motor ID {motor_id} on COM3")
                else:
                    print(f"  No response from motor ID {motor_id}")
            
            print("  Closed COM3")
    except Exception as e:
        print(f"  Error with COM3: {e}")
    
    try:
        # Try to open COM4 (which might be the leader arm)
        print("\nTesting COM4 as leader arm...")
        with serial.Serial("COM4", 1000000, timeout=0.5) as ser:
            print("Successfully opened COM4")
            
            # Try pinging all motors
            for motor_id in range(1, 7):
                # Basic ping packet for Feetech SCS motors
                checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                
                # Send ping and read response
                print(f"  Pinging motor ID {motor_id} on COM4...")
                ser.write(ping_packet)
                time.sleep(0.1)  # Wait for response
                
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"  Response received: {' '.join([hex(b) for b in response])}")
                    
                    # Check if response is valid for this motor ID
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        print(f"  SUCCESS! Valid response from motor ID {motor_id} on COM4")
                else:
                    print(f"  No response from motor ID {motor_id}")
            
            print("  Closed COM4")
    except Exception as e:
        print(f"  Error with COM4: {e}")

def check_power_supply():
    """Provide guidance for checking power supply issues"""
    print("\n=== Power Supply Check ===")
    print("If neither port responds with all motors, the issue is likely with the power supply:")
    print("1. Ensure the 7.4V power supply is connected to both arms")
    print("2. Check for any LED indicators on the controller boards")
    print("3. Verify all motor connections are secure")
    print("4. Check if the USB cables are different types (USB-A vs USB-C)")
    print("5. Try different USB ports on your computer")

def update_instructions():
    """Instructions for using the swapped config if needed"""
    print("\n=== Using Swapped Configuration ===")
    print("If we find that the ports are swapped, use the swapped configuration with:")
    print("python lerobot/scripts/control_robot.py --robot.type=so101_windows_swapped --control.type=teleoperate")
    print("\nIf neither port works with all motors, try checking the power supply again.")

if __name__ == "__main__":
    print("=== Port Swap Test ===")
    print("Testing if COM3 and COM4 might be swapped for the leader and follower arms")
    
    # Fix any permissions issues
    print("\nResetting serial ports...")
    os.system("mode COM3:9600,n,8,1")
    os.system("mode COM4:9600,n,8,1")
    time.sleep(1)
    
    # Test if ports are swapped
    test_ports_swapped()
    
    # Check power supply
    check_power_supply()
    
    # Update instructions
    update_instructions()

import sys
import os
import time
import serial

def test_speeds(port_name="COM3"):
    """Test different speeds and configurations for the leader arm"""
    print(f"Testing different speeds on {port_name}...")
    
    # Try different baudrates
    baudrates = [9600, 19200, 38400, 57600, 115200, 128000, 230400, 250000, 500000, 1000000]
    
    for baudrate in baudrates:
        print(f"\n=== Testing baudrate {baudrate} ===")
        try:
            # Try to open the port
            ser = serial.Serial(port_name, baudrate, timeout=1.0)  # Longer timeout
            print(f"Successfully opened {port_name} at {baudrate} baud")
            
            # Try different delays for motor responsiveness
            for delay in [0.1, 0.2, 0.5, 1.0]:
                print(f"\n- Testing with {delay}s delay -")
                
                # Test each motor ID from 1 to 10
                for motor_id in range(1, 11):
                    # Basic ping packet for Feetech SCS motors
                    # Header (0xFF, 0xFF) + ID + LEN + INST(PING=0x01) + CHECKSUM
                    checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                    ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                    
                    # Send ping and read response with longer delay
                    print(f"  Pinging motor ID {motor_id}...")
                    ser.write(ping_packet)
                    time.sleep(delay)  # Use the specified delay
                    
                    if ser.in_waiting:
                        response = ser.read(ser.in_waiting)
                        print(f"  Response received: {' '.join([hex(b) for b in response])}")
                        
                        # Check if response is valid for this motor ID
                        if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                            print(f"  SUCCESS! Valid ping response from motor ID {motor_id}")
                            print(f"\n!!! FOUND WORKING CONFIGURATION !!!")
                            print(f"Baudrate: {baudrate}")
                            print(f"Delay: {delay}s")
                            print(f"Motor ID: {motor_id}")
                    else:
                        print(f"  No response from motor ID {motor_id}")
            
            # Close the port
            ser.close()
            print(f"Closed {port_name}")
            
        except Exception as e:
            print(f"Error testing at {baudrate} baud: {e}")

def check_power_supply():
    """Guidance for checking the power supply issues"""
    print("\n--- Power Supply Check ---")
    print("The leader arm motors are not responding, which is commonly due to power supply issues.")
    print("Please verify the following:")
    print("1. Is the leader arm power supply connected and turned on?")
    print("2. Are there any LED indicators on the motor controller (on the board, not the motors)?")
    print("3. The leader arm requires a 7.4V power supply for STS3215 motors.")
    print("4. Try disconnecting and reconnecting the power supply.")
    print("5. Check if the power supply connector is properly seated in the control board.")
    print("6. Verify that all wires are firmly connected between the controller and motors.")

if __name__ == "__main__":
    print("=== LEADER ARM SPEED TEST ===")
    print("This script will try different baudrates and delays to communicate with the leader arm\n")
    
    test_speeds()
    
    # Provide power supply check guidance
    check_power_supply()
    
    print("\nTest complete. If no successful response was found:")
    print("1. The issue is most likely with the power supply to the leader arm.")
    print("2. You can continue using just the follower arm with the follower_arm_controller.py script.")
    print("3. Consider contacting LeRobot/Hugging Face support for further assistance.")

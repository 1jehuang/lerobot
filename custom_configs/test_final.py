import sys
import os
import time
import serial

def test_com3():
    """Test COM3 for any motor response"""
    print("\n=== Testing COM3 ===")
    try:
        with serial.Serial("COM3", 1000000, timeout=0.5) as ser:
            print("Successfully opened COM3")
            
            # Try pinging all motors
            for motor_id in range(1, 7):
                # Basic ping packet
                checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                
                # Send ping
                print(f"  Pinging motor ID {motor_id}...")
                ser.write(ping_packet)
                time.sleep(0.1)
                
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"  Response received from motor {motor_id}: {' '.join([hex(b) for b in response])}")
                    
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        print(f"  SUCCESS! Valid response from motor ID {motor_id}")
                else:
                    print(f"  No response from motor ID {motor_id}")
            
            ser.close()
            print("COM3 test complete")
            
    except Exception as e:
        print(f"Error with COM3: {e}")

def test_com4():
    """Test COM4 for any motor response"""
    print("\n=== Testing COM4 ===")
    try:
        with serial.Serial("COM4", 1000000, timeout=0.5) as ser:
            print("Successfully opened COM4")
            
            # Try pinging all motors
            for motor_id in range(1, 7):
                # Basic ping packet
                checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                
                # Send ping
                print(f"  Pinging motor ID {motor_id}...")
                ser.write(ping_packet)
                time.sleep(0.1)
                
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"  Response received from motor {motor_id}: {' '.join([hex(b) for b in response])}")
                    
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        print(f"  SUCCESS! Valid response from motor ID {motor_id}")
                else:
                    print(f"  No response from motor ID {motor_id}")
            
            ser.close()
            print("COM4 test complete")
            
    except Exception as e:
        print(f"Error with COM4: {e}")

def final_recommendations():
    """Provide final recommendations based on the test results"""
    print("\n=== FINAL RECOMMENDATIONS ===")
    print("Based on our extensive testing, here are the recommendations:")
    
    print("\n1. Check the physical USB connections:")
    print("   - The leader arm may be using USB-C instead of USB-A")
    print("   - Try different USB ports on your computer")
    print("   - Ensure the cables are properly seated")
    
    print("\n2. Verify the power supply:")
    print("   - Confirm the 7.4V power supply is connected to both arms")
    print("   - Check for any LED indicators on the controller boards")
    print("   - Try a different power supply if available")
    
    print("\n3. Use the follower arm independently:")
    print("   - We created a follower_arm_controller.py script that works with the follower arm")
    print("   - You can continue your project using just the follower arm while troubleshooting the leader arm")
    
    print("\n4. Contact support:")
    print("   - Reach out to LeRobot/Hugging Face support for additional assistance")
    print("   - Provide details of our testing and the specific issues you're experiencing")
    
    print("\nYour working solution for now is:")
    print("python C:\\Users\\jerem\\Downloads\\lerobot\\custom_configs\\follower_arm_controller.py")

if __name__ == "__main__":
    print("=== FINAL PORT TEST ===")
    print("Running final test on COM3 and COM4 ports")
    
    # Test each port
    test_com3()
    test_com4()
    
    # Provide final recommendations
    final_recommendations()

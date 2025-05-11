import sys
import os
import time
import serial
import serial.tools.list_ports

def print_all_usb_devices():
    """Print detailed information about all USB devices"""
    print("=== ALL USB DEVICES ===")
    
    # Get list of all serial ports
    ports = list(serial.tools.list_ports.comports())
    print(f"Found {len(ports)} serial ports:")
    
    for port in ports:
        print(f"\nPort: {port.device}")
        print(f"  Description: {port.description}")
        print(f"  Hardware ID: {port.hwid}")
        print(f"  Product: {port.product if port.product else 'None'}")
        print(f"  Manufacturer: {port.manufacturer if port.manufacturer else 'None'}")
        print(f"  Serial Number: {port.serial_number if port.serial_number else 'None'}")
        print(f"  Location: {port.location if port.location else 'None'}")
        print(f"  Interface: {port.interface if port.interface else 'None'}")

def try_all_possible_com_ports():
    """Try to communicate with motors on all possible COM ports"""
    print("\n=== TESTING ALL POSSIBLE COM PORTS ===")
    
    # Try COM1 through COM20
    for com_port in range(1, 21):
        port_name = f"COM{com_port}"
        print(f"\nTesting {port_name}...")
        
        try:
            # Try to open the port
            ser = serial.Serial(port_name, 1000000, timeout=0.5)
            print(f"  Successfully opened {port_name}")
            
            # Try pinging all motors
            for motor_id in range(1, 7):
                # Basic ping packet
                checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                
                # Send ping
                print(f"  Pinging motor ID {motor_id} on {port_name}...")
                ser.write(ping_packet)
                time.sleep(0.1)
                
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"  Response received from motor {motor_id}: {' '.join([hex(b) for b in response])}")
                    
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        print(f"  SUCCESS! Valid response from motor ID {motor_id} on {port_name}")
                else:
                    print(f"  No response from motor ID {motor_id}")
            
            ser.close()
            print(f"  {port_name} test complete")
            
        except serial.SerialException as e:
            if "could not open port" in str(e) and "PermissionError" in str(e):
                print(f"  {port_name} exists but is in use or permission denied")
            elif "could not open port" in str(e):
                print(f"  {port_name} does not exist or cannot be opened")
            else:
                print(f"  Error with {port_name}: {e}")
        except Exception as e:
            print(f"  Error with {port_name}: {e}")

def check_usb_c_devices():
    """Provide instructions for checking USB-C devices"""
    print("\n=== USB-C CHECK INSTRUCTIONS ===")
    print("Since the USB-C devices aren't being properly detected as COM ports, try these steps:")
    print("1. Disconnect both USB-C cables from your computer")
    print("2. Open Device Manager (already opened for you)")
    print("3. Reconnect ONE USB-C cable")
    print("4. Watch for a new device appearing in Device Manager")
    print("5. If a new device appears with a yellow warning sign, it may need drivers")
    print("6. Repeat with the other USB-C cable")
    print("\nIf you suspect the USB-C cables are using a different protocol than the CH343,")
    print("you may need to find and install the correct driver for these devices.")

def final_recommendations():
    """Provide final recommendations based on test results"""
    print("\n=== CURRENT FINDINGS ===")
    print("1. COM3 and COM4 are detected as CH343 USB-Serial adapters")
    print("2. COM4 responds properly to all motor commands")
    print("3. COM3 does not respond to any motor commands")
    print("4. No USB-C devices are currently detected as COM ports")
    
    print("\n=== RECOMMENDATIONS ===")
    print("1. Use the working arm controller to control the arm on COM4:")
    print("   python C:\\Users\\jerem\\Downloads\\lerobot\\custom_configs\\working_arm_controller.py")
    
    print("\n2. For the USB-C devices:")
    print("   a. Check your USB-C connections and try different USB ports")
    print("   b. Look for unknown devices in Device Manager")
    print("   c. Try installing specific USB-C to Serial drivers if needed")
    
    print("\n3. For the non-responsive COM3:")
    print("   a. Check power connections for this arm")
    print("   b. Verify there are lights on the controller board")
    print("   c. Try replacing power supply if available")

if __name__ == "__main__":
    print("=== USB-C DEVICE VERIFICATION ===")
    
    # Print all USB devices
    print_all_usb_devices()
    
    # Try all possible COM ports
    try_all_possible_com_ports()
    
    # Instructions for checking USB-C devices
    check_usb_c_devices()
    
    # Final recommendations
    final_recommendations()

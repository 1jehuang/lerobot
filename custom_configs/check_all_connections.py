import sys
import os
import time
import serial
import serial.tools.list_ports

def check_all_serial_ports():
    """Check all available serial ports for the leader arm"""
    print("=== Checking All Serial Ports ===")
    
    # Get list of all serial ports
    ports = serial.tools.list_ports.comports()
    print(f"Found {len(ports)} serial ports:")
    
    for port in ports:
        print(f"\nPort: {port.device}")
        print(f"  Description: {port.description}")
        print(f"  Hardware ID: {port.hwid}")
        print(f"  Product: {port.product}")
        print(f"  Manufacturer: {port.manufacturer}")
        
        # Try to open this port
        try:
            ser = serial.Serial(port.device, 1000000, timeout=0.5)
            print(f"  Successfully opened {port.device}")
            
            # Test each motor ID from 1 to 6
            for motor_id in range(1, 7):
                # Basic ping packet for Feetech SCS motors
                checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                
                # Send ping and read response
                print(f"  Pinging motor ID {motor_id} on {port.device}...")
                ser.write(ping_packet)
                time.sleep(0.1)  # Wait for response
                
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"  Response received: {' '.join([hex(b) for b in response])}")
                    
                    # Check if response is valid for this motor ID
                    if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                        print(f"  SUCCESS! Valid ping response from motor ID {motor_id} on {port.device}")
                else:
                    print(f"  No response from motor ID {motor_id}")
            
            # Close the port
            ser.close()
            print(f"  Closed {port.device}")
            
        except Exception as e:
            print(f"  Error with {port.device}: {e}")

def check_usb_c_devices():
    """Check specifically for USB-C devices that might be the leader arm"""
    print("\n=== USB-C Leader Arm Investigation ===")
    print("The leader arm might be connected through USB-C and not properly recognized as a serial device.")
    print("Options to investigate:")
    print("1. Check Device Manager (devmgmt.msc) for any unknown or unrecognized devices")
    print("2. Look for 'USB Serial Device' instead of 'USB-Enhanced-SERIAL CH343'")
    print("3. Try different USB ports, especially USB-C ports if your computer has them")
    print("4. Check if the USB cable for the leader arm is different than the follower arm")
    print("\nPossible solutions:")
    print("1. If you find a different USB device for the leader arm, note the COM port number")
    print("2. Update the so101_windows_config.py file with the correct port")
    print("3. If the device isn't recognized at all, try installing drivers for USB-C serial devices")
    
    # Physical check
    print("\nPhysical check:")
    print("1. Is the leader arm connected by a USB-C cable?")
    print("2. Try disconnecting and reconnecting the USB cable for the leader arm")
    print("3. Try a different USB port, especially a USB-C port if available")
    print("4. Check if the USB cable is damaged or faulty")

def update_config_file():
    """Instructions to update the config file if a new port is found"""
    print("\n=== Updating Configuration File ===")
    print("If you find a different port for the leader arm, update the config file:")
    print("1. Open C:\\Users\\jerem\\Downloads\\lerobot\\custom_configs\\so101_windows_config.py")
    print("2. Find the leader_arms section and update the port value:")
    print('   port="COMx",  # Replace COMx with the correct port')
    print("3. Save the file and try running the leader arm test again")

if __name__ == "__main__":
    print("=== USB-C Leader Arm Connection Check ===")
    print("This script will check all serial ports to find the leader arm")
    
    # Check all serial ports
    check_all_serial_ports()
    
    # Check for USB-C devices
    check_usb_c_devices()
    
    # Instructions to update config
    update_config_file()
    
    print("\nTest complete. Please provide any information about USB-C connections for the leader arm.")

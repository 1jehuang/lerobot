
import sys
import os
import time
import serial
import serial.tools.list_ports

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import scservo_sdk as scs
    print("Successfully imported scservo_sdk")
except ImportError:
    print("Failed to import scservo_sdk. Make sure it's installed.")
    sys.exit(1)

def check_port_details(port_name):
    """Check detailed information about the port"""
    print(f"\n--- Detailed Port Information for {port_name} ---")
    
    try:
        # Find the port in the list of all ports
        for port in serial.tools.list_ports.comports():
            if port.device == port_name:
                print(f"Device: {port.device}")
                print(f"Name: {port.name}")
                print(f"Description: {port.description}")
                print(f"Hardware ID: {port.hwid}")
                print(f"VID:PID: {port.vid:04x}:{port.pid:04x}")
                print(f"Serial Number: {port.serial_number}")
                print(f"Location: {port.location}")
                print(f"Manufacturer: {port.manufacturer}")
                print(f"Product: {port.product}")
                print(f"Interface: {port.interface}")
                return
        print(f"Port {port_name} not found in system")
    except Exception as e:
        print(f"Error retrieving port details: {e}")

def check_direct_serial_communication(port_name):
    """Try direct serial communication with the port"""
    print(f"\n--- Direct Serial Communication Test for {port_name} ---")
    
    # List of baudrates to try
    baudrates = [1000000, 500000, 250000, 128000, 115200, 57600, 38400, 19200, 9600]
    
    for baudrate in baudrates:
        print(f"\nTesting baudrate: {baudrate}")
        
        try:
            # Open the serial port directly
            with serial.Serial(port_name, baudrate=baudrate, timeout=0.5) as ser:
                print(f"Successfully opened port at {baudrate} baud")
                
                # Flush any existing data
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                
                # Try to ping each potential motor ID with a raw packet
                for motor_id in range(1, 15):  # Try more IDs just in case
                    # PING command for Feetech servo (protocol 0)
                    # Header(0xFF, 0xFF) + ID + Length + Command(PING=0x01) + Checksum
                    ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01])
                    checksum = (~(sum(ping_packet[2:]) % 256)) & 0xFF
                    ping_packet.append(checksum)
                    
                    print(f"  Sending PING to ID {motor_id}: {' '.join(f'{b:02X}' for b in ping_packet)}")
                    ser.write(ping_packet)
                    
                    # Read response
                    time.sleep(0.1)  # Give time for the response
                    if ser.in_waiting:
                        response = ser.read(ser.in_waiting)
                        print(f"  Response received: {' '.join(f'{b:02X}' for b in response)}")
                        
                        # Check if it's a valid response for this ID
                        if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                            print(f"  ✅ Valid response from motor ID {motor_id}!")
                    else:
                        print(f"  No response from ID {motor_id}")
                
        except serial.SerialException as e:
            print(f"Error opening port at {baudrate} baud: {e}")
        except Exception as e:
            print(f"Error during communication: {e}")

def try_alternative_scan(port_name):
    """Try scanning for motors with modified timing and retries"""
    print(f"\n--- Alternative Scan for {port_name} ---")
    
    # Initialize port handler
    port_handler = scs.PortHandler(port_name)
    
    try:
        if port_handler.openPort():
            print(f"Successfully opened {port_name}")
            
            # Try multiple baudrates with increased timeout
            baudrates = [1000000, 500000, 250000, 128000, 115200, 57600, 38400, 19200]
            
            for baudrate in baudrates:
                if port_handler.setBaudRate(baudrate):
                    print(f"\nSet baudrate to {baudrate}")
                    
                    # Set longer packet timeout
                    port_handler.setPacketTimeoutMillis(2000)  # 2 seconds timeout
                    
                    # Initialize packet handler for both protocol versions
                    for protocol in [0, 1]:
                        packet_handler = scs.PacketHandler(protocol)
                        print(f"Testing with protocol version {protocol}")
                        
                        # Try to scan with bulk read
                        group_bulk_read = scs.GroupBulkRead(port_handler, packet_handler)
                        
                        # Add parameters for IDs 1-20 (wider range)
                        for motor_id in range(1, 21):
                            # Try to read model number (address 3, 2 bytes)
                            try:
                                group_bulk_read.addParam(motor_id, 3, 2)
                            except Exception:
                                pass  # Ignore errors in adding parameters
                        
                        # Try multiple times with different timeouts
                        for attempt in range(3):
                            try:
                                # Execute bulk read
                                comm_result = group_bulk_read.txRxPacket()
                                
                                # Check if any data was received
                                any_data = False
                                for motor_id in range(1, 21):
                                    if group_bulk_read.isAvailable(motor_id, 3, 2):
                                        any_data = True
                                        model_number = group_bulk_read.getData(motor_id, 3, 2)
                                        print(f"  ✅ Found motor ID {motor_id} with model number: {model_number}")
                                
                                if not any_data:
                                    print(f"  No motors found in bulk read (attempt {attempt+1})")
                            except Exception as e:
                                print(f"  Error in bulk read (attempt {attempt+1}): {e}")
                            
                            # Try individual reads as well
                            for motor_id in range(1, 15):
                                for address in [3, 5, 56]:  # Model Number, ID, Present Position
                                    try:
                                        value, comm_result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, address)
                                        if comm_result == scs.COMM_SUCCESS:
                                            print(f"  ✅ Successfully read from motor ID {motor_id}, address {address}: {value}")
                                    except Exception:
                                        pass  # Ignore errors in individual reads
                    
            # Close the port
            port_handler.closePort()
        else:
            print(f"Failed to open port {port_name}")
    except Exception as e:
        print(f"Error in alternative scan: {e}")
        if port_handler.is_open:
            port_handler.closePort()

def swap_ports_test():
    """Test if swapping COM3 and COM4 makes a difference"""
    print("\n--- Swap Ports Test ---")
    print("This test will try to confirm if both controllers are working but might be swapped.")
    
    # Test COM4 (known working port) with leader arm settings
    print("\nTesting COM4 (Follower) with leader arm motor IDs:")
    
    try:
        port_handler = scs.PortHandler("COM4")
        if port_handler.openPort() and port_handler.setBaudRate(1000000):
            packet_handler = scs.PacketHandler(0)
            for motor_id in range(1, 7):
                try:
                    position, comm_result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)
                    if comm_result == scs.COMM_SUCCESS:
                        print(f"  ✅ Motor ID {motor_id} present position: {position}")
                    else:
                        print(f"  Motor ID {motor_id} did not respond: {packet_handler.getTxRxResult(comm_result)}")
                except Exception as e:
                    print(f"  Error reading from motor ID {motor_id}: {e}")
            port_handler.closePort()
    except Exception as e:
        print(f"Error testing COM4: {e}")
        
    print("\nIf the follower arm motors responded, but the leader arm motors didn't,")
    print("it suggests the leader arm controller might be defective or unpowered.")

def check_power_supply():
    """Guidance for checking the power supply issues"""
    print("\n--- Power Supply Check ---")
    print("The leader arm motors might not be responding due to power supply issues.")
    print("Please verify the following:")
    print("1. Is the leader arm power supply connected and turned on?")
    print("2. Can you check the LED indicators on the motor controller?")
    print("3. Are there any visible signs that the motors are receiving power?")
    print("4. Try disconnecting and reconnecting the power supply.")
    print("5. Ensure the motors are properly connected to the controller board.")

if __name__ == "__main__":
    # Run all diagnostic tests
    print("===== SO-101 Leader Arm Diagnostics =====")
    print("Running comprehensive diagnostics on COM3 (Leader arm)")
    
    # Check port details
    check_port_details("COM3")
    
    # Check direct serial communication
    check_direct_serial_communication("COM3")
    
    # Try alternative scanning
    try_alternative_scan("COM3")
    
    # Test port swapping
    swap_ports_test()
    
    # Check power supply
    check_power_supply()
    
    print("\nDiagnostics complete! Check the results above to identify the issue.")

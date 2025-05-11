
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

# Test if COM ports might be swapped or if there's a fundamental hardware issue
def test_port(port, name):
    print(f"\n==== Testing {name} on {port} ====")
    try:
        # Initialize PortHandler
        port_handler = scs.PortHandler(port)
        
        # Try to open the port
        if port_handler.openPort():
            print(f"Successfully opened {port}")
            
            # Get port details
            print(f"Port name: {port_handler.port_name}")
            print(f"Is port open: {port_handler.is_open}")
            
            # Try different baudrates
            for baudrate in [1000000, 115200]:
                if port_handler.setBaudRate(baudrate):
                    print(f"Changed baudrate to {baudrate}")
                    
                    # Initialize packet handler
                    packet_handler = scs.PacketHandler(0)  # Protocol version 0 for SCS
                    
                    # Set read timeout
                    port_handler.setPacketTimeoutMillis(1000)
                    
                    # Print port settings
                    print(f"Port settings: {baudrate} baud, Timeout: {port_handler.getPacketTimeoutMillis()}ms")
                    
                    # Try pinging each motor ID from 1 to 10
                    found_motors = 0
                    for motor_id in range(1, 11):
                        # Try to read Present_Position (address 56, 2 bytes)
                        position, comm_result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)
                        
                        if comm_result == scs.COMM_SUCCESS:
                            print(f"  Motor ID {motor_id} found! Position: {position}")
                            found_motors += 1
                    
                    if found_motors == 0:
                        print(f"  No motors found at baudrate {baudrate}")
                else:
                    print(f"Failed to change baudrate to {baudrate}")
            
            # Close the port
            port_handler.closePort()
            print(f"Closed {port}")
        else:
            print(f"Failed to open {port}")
    except Exception as e:
        print(f"Error with {port}: {e}")

# Test suggestion: try swapping USB connections for COM3 and COM4
print("IMPORTANT TEST SUGGESTION:")
print("If one arm is working (follower/COM4) and the other isn't (leader/COM3),")
print("try physically swapping the USB cables between the ports to see if the issue follows the arm or the port.")
print("\nCurrent test assumes standard configuration: Leader on COM3, Follower on COM4")

# Test both COM ports
test_port("COM3", "Leader arm")
test_port("COM4", "Follower arm")

print("\n==== NEXT STEPS ====")
print("1. If motors were found on COM4 but not COM3, the problem is likely with the leader arm hardware.")
print("2. Try swapping the USB cables between COM3 and COM4 and run this test again.")
print("3. If after swapping, the problem follows the arm (still no motors on leader), it's a hardware issue with the arm.")
print("4. If after swapping, the problem follows the port (now no motors on COM4), it could be a driver or USB port issue.")
print("5. Check all connections, power supply, and cables on the leader arm.")

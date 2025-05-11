
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

# Testing COM3 (Leader)
print("\nTesting COM3 (Leader arm)...")
try:
    # Initialize PortHandler
    port_handler_com3 = scs.PortHandler("COM3")
    
    # Try to open the port
    if port_handler_com3.openPort():
        print("Successfully opened COM3")
        
        # Set baudrate
        if port_handler_com3.setBaudRate(1000000):
            print("Changed baudrate to 1000000")
            
            # Initialize packet handler
            packet_handler = scs.PacketHandler(0)  # Protocol version 0 for SCS
            
            # Set read timeout
            port_handler_com3.setPacketTimeoutMillis(1000)
            
            # Try to read Present_Position from each motor ID from 1 to 6
            for motor_id in range(1, 7):
                print(f"Testing motor ID {motor_id}...")
                try:
                    # Read the present position (address 56, 2 bytes)
                    position, comm_result, error = packet_handler.read2ByteTxRx(port_handler_com3, motor_id, 56)
                    
                    if comm_result == scs.COMM_SUCCESS:
                        print(f"  Motor ID {motor_id} present position: {position}")
                    else:
                        print(f"  Motor ID {motor_id} did not respond: {packet_handler.getTxRxResult(comm_result)}")
                except Exception as e:
                    print(f"  Error reading from motor ID {motor_id}: {e}")
            
            # Close the port
            port_handler_com3.closePort()
        else:
            print("Failed to change baudrate")
    else:
        print("Failed to open COM3")
except Exception as e:
    print(f"Error with COM3: {e}")

# Testing COM4 (Follower)
print("\nTesting COM4 (Follower arm)...")
try:
    # Initialize PortHandler
    port_handler_com4 = scs.PortHandler("COM4")
    
    # Try to open the port
    if port_handler_com4.openPort():
        print("Successfully opened COM4")
        
        # Set baudrate
        if port_handler_com4.setBaudRate(1000000):
            print("Changed baudrate to 1000000")
            
            # Initialize packet handler
            packet_handler = scs.PacketHandler(0)  # Protocol version 0 for SCS
            
            # Set read timeout
            port_handler_com4.setPacketTimeoutMillis(1000)
            
            # Try to read Present_Position from each motor ID from 1 to 6
            for motor_id in range(1, 7):
                print(f"Testing motor ID {motor_id}...")
                try:
                    # Read the present position (address 56, 2 bytes)
                    position, comm_result, error = packet_handler.read2ByteTxRx(port_handler_com4, motor_id, 56)
                    
                    if comm_result == scs.COMM_SUCCESS:
                        print(f"  Motor ID {motor_id} present position: {position}")
                    else:
                        print(f"  Motor ID {motor_id} did not respond: {packet_handler.getTxRxResult(comm_result)}")
                except Exception as e:
                    print(f"  Error reading from motor ID {motor_id}: {e}")
            
            # Close the port
            port_handler_com4.closePort()
        else:
            print("Failed to change baudrate")
    else:
        print("Failed to open COM4")
except Exception as e:
    print(f"Error with COM4: {e}")

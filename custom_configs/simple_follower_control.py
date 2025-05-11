
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

# Initialize port handler for follower arm (COM4)
port_handler = scs.PortHandler("COM4")
packet_handler = scs.PacketHandler(0)  # Protocol version 0 for SCS

if port_handler.openPort():
    print("Successfully opened COM4")
    
    if port_handler.setBaudRate(1000000):
        print("Changed baudrate to 1000000")
        
        # Read current positions of all motors
        positions = []
        for motor_id in range(1, 7):
            position, comm_result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)
            if comm_result == scs.COMM_SUCCESS:
                print(f"Motor ID {motor_id} current position: {position}")
                positions.append(position)
            else:
                print(f"Motor ID {motor_id} read failed: {packet_handler.getTxRxResult(comm_result)}")
                positions.append(None)
        
        # Let's try a simple movement with motor ID 6 (gripper)
        if positions[5] is not None:  # Check if gripper position was read successfully
            motor_id = 6
            current_position = positions[5]
            
            # Enable torque
            print(f"Enabling torque for motor ID {motor_id}...")
            _, comm_result, _ = packet_handler.write1ByteTxRx(port_handler, motor_id, 40, 1)  # Address 40 is Torque_Enable
            if comm_result != scs.COMM_SUCCESS:
                print(f"Failed to enable torque: {packet_handler.getTxRxResult(comm_result)}")
            else:
                print("Torque enabled")
                
                # Move the motor a bit - open the gripper
                goal_position = current_position + 200
                print(f"Moving motor ID {motor_id} from {current_position} to {goal_position}...")
                
                # Use write2ByteTxRx to send the goal position command
                _, comm_result, _ = packet_handler.write2ByteTxRx(port_handler, motor_id, 42, goal_position)  # Address 42 is Goal_Position
                
                if comm_result != scs.COMM_SUCCESS:
                    print(f"Failed to send goal position: {packet_handler.getTxRxResult(comm_result)}")
                else:
                    print(f"Goal position sent, waiting for movement...")
                    
                    # Wait for the movement to complete
                    time.sleep(1)
                    
                    # Read the new position
                    new_position, comm_result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)
                    if comm_result == scs.COMM_SUCCESS:
                        print(f"Motor moved to position: {new_position}")
                    else:
                        print(f"Failed to read new position: {packet_handler.getTxRxResult(comm_result)}")
                
                # Close the gripper by returning to the original position
                time.sleep(1)
                print(f"Moving motor ID {motor_id} back to {current_position}...")
                
                _, comm_result, _ = packet_handler.write2ByteTxRx(port_handler, motor_id, 42, current_position)
                
                if comm_result != scs.COMM_SUCCESS:
                    print(f"Failed to send goal position: {packet_handler.getTxRxResult(comm_result)}")
                else:
                    print(f"Goal position sent, waiting for movement...")
                    
                    # Wait for the movement to complete
                    time.sleep(1)
                    
                    # Read the new position
                    new_position, comm_result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)
                    if comm_result == scs.COMM_SUCCESS:
                        print(f"Motor returned to position: {new_position}")
                    else:
                        print(f"Failed to read new position: {packet_handler.getTxRxResult(comm_result)}")
                
                # Disable torque
                print(f"Disabling torque for motor ID {motor_id}...")
                _, comm_result, _ = packet_handler.write1ByteTxRx(port_handler, motor_id, 40, 0)
                if comm_result != scs.COMM_SUCCESS:
                    print(f"Failed to disable torque: {packet_handler.getTxRxResult(comm_result)}")
                else:
                    print("Torque disabled")
        
        # Close the port
        port_handler.closePort()
        print("Port closed")
    else:
        print("Failed to change baudrate")
        port_handler.closePort()
else:
    print("Failed to open COM4")

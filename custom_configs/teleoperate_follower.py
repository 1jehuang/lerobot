
import sys
import os
import time
import msvcrt  # For Windows keyboard input

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

# Control step size
STEP_SIZE = 50  # Steps to move per key press
REST_POSITIONS = [3014, 890, 2954, 1084, 74, 2065]  # Initial/rest positions for all motors

def print_menu():
    print("\nFollower Arm Control Menu:")
    print("1-6: Select motor (1-6)")
    print("w: Move +")
    print("s: Move -")
    print("r: Return all motors to rest position")
    print("t: Toggle torque (on/off)")
    print("q: Quit")
    print("\nCurrent motor: ", end="")

def main():
    if not port_handler.openPort():
        print("Failed to open COM4")
        return
    
    if not port_handler.setBaudRate(1000000):
        print("Failed to change baudrate")
        port_handler.closePort()
        return
    
    print("Successfully connected to follower arm")
    
    # Read initial positions
    current_positions = []
    for motor_id in range(1, 7):
        position, comm_result, error = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)
        if comm_result == scs.COMM_SUCCESS:
            print(f"Motor ID {motor_id} current position: {position}")
            current_positions.append(position)
        else:
            print(f"Motor ID {motor_id} read failed: {packet_handler.getTxRxResult(comm_result)}")
            current_positions.append(REST_POSITIONS[motor_id-1])  # Use rest position as fallback
    
    # Enable torque on all motors
    torque_enabled = True
    for motor_id in range(1, 7):
        comm_result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 40, 1)
        if comm_result != scs.COMM_SUCCESS:
            print(f"Failed to enable torque on motor {motor_id}: {packet_handler.getTxRxResult(comm_result)}")
    
    # Main control loop
    selected_motor = 1  # Start with motor 1 selected
    
    try:
        print_menu()
        print(f"{selected_motor}")
        
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                
                if key == 'q':
                    print("\nQuitting...")
                    break
                
                # Motor selection
                elif key in '123456':
                    selected_motor = int(key)
                    print(f"\rCurrent motor: {selected_motor}")
                
                # Movement control
                elif key == 'w':  # Move +
                    motor_idx = selected_motor - 1
                    target_position = current_positions[motor_idx] + STEP_SIZE
                    
                    print(f"\rMoving motor {selected_motor} to position {target_position}...")
                    comm_result, error = packet_handler.write2ByteTxRx(port_handler, selected_motor, 42, target_position)
                    
                    if comm_result == scs.COMM_SUCCESS:
                        current_positions[motor_idx] = target_position
                    else:
                        print(f"\nFailed to move motor: {packet_handler.getTxRxResult(comm_result)}")
                
                elif key == 's':  # Move -
                    motor_idx = selected_motor - 1
                    target_position = current_positions[motor_idx] - STEP_SIZE
                    
                    print(f"\rMoving motor {selected_motor} to position {target_position}...")
                    comm_result, error = packet_handler.write2ByteTxRx(port_handler, selected_motor, 42, target_position)
                    
                    if comm_result == scs.COMM_SUCCESS:
                        current_positions[motor_idx] = target_position
                    else:
                        print(f"\nFailed to move motor: {packet_handler.getTxRxResult(comm_result)}")
                
                # Return to rest position
                elif key == 'r':
                    print("\nReturning all motors to rest position...")
                    for motor_id in range(1, 7):
                        motor_idx = motor_id - 1
                        rest_position = REST_POSITIONS[motor_idx]
                        
                        comm_result, error = packet_handler.write2ByteTxRx(port_handler, motor_id, 42, rest_position)
                        if comm_result == scs.COMM_SUCCESS:
                            current_positions[motor_idx] = rest_position
                        else:
                            print(f"Failed to move motor {motor_id}: {packet_handler.getTxRxResult(comm_result)}")
                    
                    print("All motors returned to rest position")
                
                # Toggle torque
                elif key == 't':
                    torque_enabled = not torque_enabled
                    torque_value = 1 if torque_enabled else 0
                    
                    print(f"\nTorque {'enabled' if torque_enabled else 'disabled'} for all motors")
                    for motor_id in range(1, 7):
                        comm_result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 40, torque_value)
                        if comm_result != scs.COMM_SUCCESS:
                            print(f"Failed to {'enable' if torque_enabled else 'disable'} torque on motor {motor_id}: {packet_handler.getTxRxResult(comm_result)}")
                
                elif key == '\r':  # Enter key - refresh menu
                    print_menu()
                    print(f"{selected_motor}")
            
            time.sleep(0.05)  # Small delay to reduce CPU usage
            
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    finally:
        # Disable torque on all motors before exit
        print("Disabling torque on all motors...")
        for motor_id in range(1, 7):
            comm_result, error = packet_handler.write1ByteTxRx(port_handler, motor_id, 40, 0)
        
        # Close the port
        port_handler.closePort()
        print("Port closed")

if __name__ == "__main__":
    main()

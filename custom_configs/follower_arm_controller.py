import sys
import os
import time
import msvcrt
import serial

class FollowerArmController:
    """Controller for the SO-101 follower arm"""
    
    def __init__(self, port="COM4", baudrate=1000000):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connected = False
        
        # Default positions for each motor
        self.rest_positions = [3014, 890, 2954, 1084, 74, 2065]  # Initial/rest positions
        self.current_positions = list(self.rest_positions)
        self.motor_names = ["Shoulder Pan", "Shoulder Lift", "Elbow Flex", "Wrist Flex", "Wrist Roll", "Gripper"]
        
        # Control settings
        self.selected_motor = 0  # Index of currently selected motor (0-5)
        self.step_size = 50      # Steps to move per key press
        self.torque_enabled = True
        
    def connect(self):
        """Connect to the follower arm"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.5)
            self.connected = True
            print(f"Successfully connected to follower arm on {self.port}")
            return True
        except Exception as e:
            print(f"Error connecting to follower arm: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the follower arm"""
        if self.connected and self.ser:
            self.disable_torque_all()
            self.ser.close()
            self.connected = False
            print("Disconnected from follower arm")
    
    def ping_motors(self):
        """Ping all motors to verify communication"""
        if not self.connected:
            print("Not connected to follower arm")
            return False
        
        all_responsive = True
        for motor_id in range(1, 7):
            # Basic ping packet for Feetech SCS motors
            checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
            ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
            
            # Send ping and read response
            self.ser.write(ping_packet)
            time.sleep(0.1)  # Wait for response
            
            if self.ser.in_waiting:
                response = self.ser.read(self.ser.in_waiting)
                if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    print(f"Motor {motor_id} ({self.motor_names[motor_id-1]}) is responsive")
                else:
                    print(f"Motor {motor_id} ({self.motor_names[motor_id-1]}) responded but with unexpected data")
                    all_responsive = False
            else:
                print(f"Motor {motor_id} ({self.motor_names[motor_id-1]}) is not responding")
                all_responsive = False
        
        return all_responsive
    
    def read_positions(self):
        """Read current positions of all motors"""
        if not self.connected:
            print("Not connected to follower arm")
            return False
        
        for motor_id in range(1, 7):
            # Read present position (address 56, 2 bytes)
            read_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x02, 56, 0x02])
            checksum = 0
            for b in read_packet[2:-1]:
                checksum += b
            read_packet.append((~checksum) & 0xFF)
            
            # Send read and get response
            self.ser.write(read_packet)
            time.sleep(0.05)
            
            if self.ser.in_waiting:
                response = self.ser.read(self.ser.in_waiting)
                
                # Parse position if valid response
                if len(response) >= 8 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                    position = response[5] + (response[6] << 8)
                    self.current_positions[motor_id-1] = position
                    print(f"Motor {motor_id} ({self.motor_names[motor_id-1]}) position: {position}")
                else:
                    print(f"Invalid response from motor {motor_id}")
            else:
                print(f"No response from motor {motor_id} when reading position")
        
        return True
    
    def set_position(self, motor_id, position):
        """Set the position of a specific motor"""
        if not self.connected:
            print("Not connected to follower arm")
            return False
        
        if motor_id < 1 or motor_id > 6:
            print(f"Invalid motor ID: {motor_id}")
            return False
        
        # Ensure position is within valid range
        position = max(0, min(4095, position))
        
        # Write goal position (address 42, 2 bytes)
        write_packet = bytearray([0xFF, 0xFF, motor_id, 0x05, 0x03, 42, position & 0xFF, (position >> 8) & 0xFF])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        # Send write command
        self.ser.write(write_packet)
        time.sleep(0.05)
        
        # Check for response
        if self.ser.in_waiting:
            response = self.ser.read(self.ser.in_waiting)
            if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                self.current_positions[motor_id-1] = position
                return True
        
        print(f"Failed to set position for motor {motor_id}")
        return False
    
    def set_torque(self, motor_id, enable):
        """Enable or disable torque on a specific motor"""
        if not self.connected:
            print("Not connected to follower arm")
            return False
        
        # Write torque enable (address 40, 1 byte)
        torque_value = 1 if enable else 0
        write_packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x03, 40, torque_value])
        checksum = 0
        for b in write_packet[2:-1]:
            checksum += b
        write_packet.append((~checksum) & 0xFF)
        
        # Send write command
        self.ser.write(write_packet)
        time.sleep(0.05)
        
        # Check for response
        if self.ser.in_waiting:
            response = self.ser.read(self.ser.in_waiting)
            if len(response) >= 6 and response[0] == 0xFF and response[1] == 0xFF and response[2] == motor_id:
                return True
        
        print(f"Failed to set torque for motor {motor_id}")
        return False
    
    def enable_torque_all(self):
        """Enable torque on all motors"""
        all_success = True
        for motor_id in range(1, 7):
            success = self.set_torque(motor_id, True)
            all_success = all_success and success
        
        self.torque_enabled = True
        print("Torque enabled on all motors")
        return all_success
    
    def disable_torque_all(self):
        """Disable torque on all motors"""
        all_success = True
        for motor_id in range(1, 7):
            success = self.set_torque(motor_id, False)
            all_success = all_success and success
        
        self.torque_enabled = False
        print("Torque disabled on all motors")
        return all_success
    
    def toggle_torque(self):
        """Toggle torque state on all motors"""
        if self.torque_enabled:
            return self.disable_torque_all()
        else:
            return self.enable_torque_all()
    
    def return_to_rest(self):
        """Move all motors to their rest positions"""
        print("Returning to rest position...")
        all_success = True
        
        for motor_id in range(1, 7):
            rest_position = self.rest_positions[motor_id-1]
            success = self.set_position(motor_id, rest_position)
            all_success = all_success and success
        
        print("All motors returned to rest position")
        return all_success
    
    def run_interactive_control(self):
        """Run interactive control loop for the follower arm"""
        if not self.connected:
            if not self.connect():
                print("Failed to connect to follower arm")
                return
        
        # Read initial positions
        self.read_positions()
        
        # Enable torque
        self.enable_torque_all()
        
        # Print menu
        self.print_menu()
        
        try:
            running = True
            while running:
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').lower()
                    
                    if key == 'q':
                        print("\nExiting...")
                        running = False
                    
                    # Motor selection
                    elif key in '123456':
                        self.selected_motor = int(key) - 1
                        print(f"\nSelected motor: {int(key)} ({self.motor_names[self.selected_motor]})")
                    
                    # Movement control
                    elif key == 'w':  # Move +
                        self.move_selected_motor(self.step_size)
                    
                    elif key == 's':  # Move -
                        self.move_selected_motor(-self.step_size)
                    
                    # Return to rest position
                    elif key == 'r':
                        self.return_to_rest()
                    
                    # Toggle torque
                    elif key == 't':
                        self.toggle_torque()
                    
                    # Step size adjustment
                    elif key == '+' or key == '=':
                        self.step_size += 10
                        print(f"\nStep size increased to {self.step_size}")
                    
                    elif key == '-':
                        self.step_size = max(10, self.step_size - 10)
                        print(f"\nStep size decreased to {self.step_size}")
                    
                    # Refresh menu
                    elif key == '\r':  # Enter key
                        self.print_menu()
                
                time.sleep(0.05)  # Small delay to reduce CPU usage
                
        except KeyboardInterrupt:
            print("\nProgram interrupted")
        finally:
            # Disable torque on all motors before exit
            self.disable_torque_all()
            
            # Close the port
            self.disconnect()
    
    def move_selected_motor(self, steps):
        """Move the selected motor by the specified number of steps"""
        motor_id = self.selected_motor + 1
        current_pos = self.current_positions[self.selected_motor]
        new_pos = current_pos + steps
        
        print(f"\nMoving motor {motor_id} ({self.motor_names[self.selected_motor]}) from {current_pos} to {new_pos}")
        self.set_position(motor_id, new_pos)
    
    def print_menu(self):
        """Print the interactive control menu"""
        print("\n==== Follower Arm Control Menu ====")
        print("1-6: Select motor")
        print("  1: Shoulder Pan")
        print("  2: Shoulder Lift")
        print("  3: Elbow Flex")
        print("  4: Wrist Flex")
        print("  5: Wrist Roll")
        print("  6: Gripper")
        print("w: Move selected motor +")
        print("s: Move selected motor -")
        print("+/-: Increase/decrease step size")
        print("r: Return all motors to rest position")
        print("t: Toggle torque (on/off)")
        print("q: Quit")
        print(f"\nCurrent motor: {self.selected_motor + 1} ({self.motor_names[self.selected_motor]})")
        print(f"Current step size: {self.step_size}")
        print(f"Torque: {'Enabled' if self.torque_enabled else 'Disabled'}")


if __name__ == "__main__":
    print("=== SO-101 Follower Arm Controller ===")
    print("This script provides interactive control of the follower arm")
    
    controller = FollowerArmController()
    controller.run_interactive_control()

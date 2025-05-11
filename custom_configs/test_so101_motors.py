import sys
import os
import time

# Add the custom_configs directory to the Python path
sys.path.append(os.path.join(os.getcwd(), 'custom_configs'))

# Import our custom configuration
from so101_windows_config import So101WindowsRobotConfig

# Import required lerobot modules
from lerobot.common.robot_devices.robots.base_robot import BaseRobot
from lerobot.common.robot_devices.robots.register_all import register_all_robots

def main():
    # Register all robots including our custom so101_windows
    register_all_robots()
    
    print("Creating SO-101 robot configuration...")
    config = So101WindowsRobotConfig()
    
    print("Initializing robot...")
    robot = BaseRobot.from_config(config)
    
    try:
        print("Connecting to robot...")
        robot.connect()
        print("Successfully connected to robot!")
        
        # Get connected motor ports
        print("\nConnected Leader Arms:")
        for arm_name, arm in robot.leader_arms.items():
            print(f"  {arm_name}: {arm.port}")
            print("  Motors:")
            for motor_name, motor in arm.motors.items():
                print(f"    {motor_name}: Motor ID {motor.motor_id}, Model {motor.model}")
        
        print("\nConnected Follower Arms:")
        for arm_name, arm in robot.follower_arms.items():
            print(f"  {arm_name}: {arm.port}")
            print("  Motors:")
            for motor_name, motor in arm.motors.items():
                print(f"    {motor_name}: Motor ID {motor.motor_id}, Model {motor.model}")
        
        # Read current positions
        print("\nCurrent motor positions:")
        for arm_name, arm in robot.follower_arms.items():
            print(f"  {arm_name}:")
            for motor_name, motor in arm.motors.items():
                try:
                    position = motor.read_present_position()
                    print(f"    {motor_name}: {position} degrees")
                except Exception as e:
                    print(f"    {motor_name}: Error reading position - {str(e)}")
        
        print("\nTest completed successfully!")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        print("Disconnecting from robot...")
        robot.disconnect()
        print("Done!")

if __name__ == "__main__":
    main()

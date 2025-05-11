import sys
import os
import time
import serial
import serial.tools.list_ports

def test_power_indicators(port_name):
    """Test modem control signals that might indicate power status"""
    print(f"\n=== TESTING POWER INDICATORS FOR {port_name} ===")
    
    try:
        with serial.Serial(port_name, 9600, timeout=1) as ser:
            # Get modem control signals
            print(f"Port {port_name} successfully opened")
            
            # Check control signals
            print("Control signals:")
            print(f"  CTS (Clear To Send): {ser.cts}")  # Might indicate if device has power
            print(f"  DSR (Data Set Ready): {ser.dsr if hasattr(ser, 'dsr') else 'Not available'}")
            print(f"  CD (Carrier Detect): {ser.cd if hasattr(ser, 'cd') else 'Not available'}")
            print(f"  RI (Ring Indicator): {ser.ri if hasattr(ser, 'ri') else 'Not available'}")
            
            # Try manipulating RTS to see if device responds
            print("\nTesting device response:")
            ser.rts = True
            time.sleep(0.2)
            print(f"  After setting RTS=True, CTS={ser.cts}")
            
            ser.rts = False
            time.sleep(0.2)
            print(f"  After setting RTS=False, CTS={ser.cts}")
            
            return True
    except Exception as e:
        print(f"Error testing {port_name}: {e}")
        return False

def check_visual_indicators():
    """Prompt user to check physical indicators"""
    print("\n=== VISUAL POWER INDICATOR CHECK ===")
    print("Please check the physical indicators on both arms:")
    print("1. Are there any LED lights on the leader arm control board?")
    print("2. Does the follower arm show any power indicator lights?")
    print("3. Check if the power supply for the leader arm is properly connected and powered on.")
    print("4. Verify that the leader arm has the correct voltage power supply (7.4V for STS3215 motors).")
    
    print("\nPower supply checklist:")
    print("- Leader arm requires 7.4V power supply for STS3215 motors")
    print("- Ensure power supply is plugged into the wall outlet and turned on")
    print("- Verify power supply connector is firmly seated in the control board")
    print("- Check for any loose wires or connections")

if __name__ == "__main__":
    # Show available ports
    print("=== AVAILABLE COM PORTS ===")
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        print(f"{port.device}: {port.description}")
    
    # Test power indicators
    leader_powered = test_power_indicators("COM3")
    follower_powered = test_power_indicators("COM4")
    
    # Physical check
    check_visual_indicators()
    
    print("\n=== SUMMARY ===")
    print(f"Leader arm (COM3) port indicators: {'OK' if leader_powered else 'FAILED'}")
    print(f"Follower arm (COM4) port indicators: {'OK' if follower_powered else 'FAILED'}")
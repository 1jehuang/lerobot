
import sys
import os
import time
import serial

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_uart_voltage(port):
    """Check if the UART port is receiving power by measuring RTS/CTS signals"""
    try:
        with serial.Serial(port, 9600, timeout=1) as ser:
            # Set RTS high
            ser.rts = True
            time.sleep(0.1)
            
            # Check CTS (this can indicate if the device is powered)
            cts_status = ser.cts
            
            # Get more serial port details
            dsr_status = ser.dsr if hasattr(ser, 'dsr') else "Not available"
            cd_status = ser.cd if hasattr(ser, 'cd') else "Not available"
            ri_status = ser.ri if hasattr(ser, 'ri') else "Not available"
            
            print(f"Port {port} status:")
            print(f"  CTS (Clear To Send): {cts_status}")
            print(f"  DSR (Data Set Ready): {dsr_status}")
            print(f"  CD (Carrier Detect): {cd_status}")
            print(f"  RI (Ring Indicator): {ri_status}")
            
            return cts_status
    except Exception as e:
        print(f"Error checking {port}: {e}")
        return False

def send_basic_ping(port, baudrates):
    """Try to send a simple ping command to see if we get any response"""
    for baudrate in baudrates:
        try:
            print(f"\nTrying baudrate {baudrate} on {port}...")
            with serial.Serial(port, baudrate, timeout=0.5) as ser:
                # Flush any pending data
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                
                # Try a basic ping packet for Feetech SCS motors
                # Packet structure: [0xFF, 0xFF, ID, LEN, INST, PARAM1...PARAMN, CHECKSUM]
                # Ping command: [0xFF, 0xFF, ID, 0x02, 0x01, CHECKSUM]
                
                # Try all possible IDs
                for motor_id in range(1, 253):  # Possible ID range for SCS servos
                    # Calculate checksum: ~(ID + LEN + INST)
                    checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                    ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                    
                    # Send ping
                    ser.write(ping_packet)
                    time.sleep(0.01)  # Small delay
                    
                    # Check for response
                    response = ser.read(10)  # Try to read a response
                    if response and len(response) >= 6:
                        print(f"Response received from ID {motor_id}! Response: {[hex(b) for b in response]}")
                        return True
                
                print(f"No response at baudrate {baudrate}")
        except Exception as e:
            print(f"Error with {port} at baudrate {baudrate}: {e}")
    
    return False

# Test both COM ports
print("Checking power supply and connection status for both arms...\n")

# Check voltage indicators on both ports
print("==== VOLTAGE CHECK ====")
leader_powered = check_uart_voltage("COM3")
follower_powered = check_uart_voltage("COM4")

print(f"\nLeader arm (COM3) appears to be {'powered' if leader_powered else 'NOT powered or properly connected'}")
print(f"Follower arm (COM4) appears to be {'powered' if follower_powered else 'NOT powered or properly connected'}")

# Try to send a basic ping to all possible motor IDs with different baudrates
print("\n==== BASIC PING TEST ====")
baudrates = [1000000, 500000, 250000, 128000, 115200, 57600, 38400, 19200]

print("\nTesting leader arm (COM3)...")
leader_responsive = send_basic_ping("COM3", baudrates)

print("\nTesting follower arm (COM4)...")
follower_responsive = send_basic_ping("COM4", baudrates)

print("\n==== SUMMARY ====")
print(f"Leader arm (COM3): Power indicators {'OK' if leader_powered else 'FAILED'}, Communication {'OK' if leader_responsive else 'FAILED'}")
print(f"Follower arm (COM4): Power indicators {'OK' if follower_powered else 'FAILED'}, Communication {'OK' if follower_responsive else 'FAILED'}")

if not leader_powered:
    print("\nThe leader arm appears to have a power supply issue. Please check:")
    print("1. Is the power adapter connected and working?")
    print("2. Is the power switch turned on (if there is one)?")
    print("3. Are there any lights or indicators on the control board?")
elif not leader_responsive:
    print("\nThe leader arm has power but is not responding to commands. Possible issues:")
    print("1. Different communication protocol than expected")
    print("2. Motors configured with IDs outside the standard range")
    print("3. Hardware failure in the control board")
    print("4. Damaged cable between control board and motors")

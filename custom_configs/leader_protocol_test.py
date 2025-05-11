import sys
import os
import time
import serial

def test_protocol(port_name="COM3", baudrate=1000000):
    """Test different protocol versions for the leader arm"""
    print(f"Testing leader arm on {port_name} with baudrate {baudrate}...")
    
    try:
        # Try to open the port
        ser = serial.Serial(port_name, baudrate, timeout=0.5)
        print(f"Successfully opened {port_name} at {baudrate} baud")
        
        # Try different protocol packet formats
        protocols = [
            "Protocol 0 (Feetech/SCS)",
            "Protocol 1 (Alternative format)",
            "Protocol 2 (ROBOTIS format)"
        ]
        
        for protocol_idx, protocol_name in enumerate(protocols):
            print(f"\n=== Testing {protocol_name} ===")
            
            # Test each motor ID from 1 to 6
            for motor_id in range(1, 7):
                print(f"  Pinging motor ID {motor_id}...")
                
                # Send appropriate ping packet based on protocol
                if protocol_idx == 0:
                    # Protocol 0 (Feetech SCS)
                    # Header (0xFF, 0xFF) + ID + LEN + INST(PING=0x01) + CHECKSUM
                    checksum = 0xFF - ((motor_id + 0x02 + 0x01) % 256)
                    ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, checksum])
                elif protocol_idx == 1:
                    # Protocol 1 (Alternative format)
                    # Different packet structure
                    ping_packet = bytearray([0xFF, 0xFF, motor_id, 0x02, 0x01, 0x00])
                    checksum = 0
                    for b in ping_packet[2:-1]:
                        checksum += b
                    ping_packet[-1] = (~checksum) & 0xFF
                else:
                    # Protocol 2 (ROBOTIS format)
                    # Header (0xFF, 0xFF, 0xFD, 0x00) + ID + LEN_L + LEN_H + INST(PING=0x01) + CRC
                    ping_packet = bytearray([0xFF, 0xFF, 0xFD, 0x00, motor_id, 0x03, 0x00, 0x01])
                    # Add simple CRC (this is simplified)
                    ping_packet.append(0x00)
                    ping_packet.append(0x00)
                
                # Send ping and read response
                ser.write(ping_packet)
                time.sleep(0.1)  # Wait for response
                
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting)
                    print(f"  Response received: {' '.join([hex(b) for b in response])}")
                    
                    # Simplified check if we got any response
                    if len(response) > 0:
                        print(f"  SUCCESS! Got response using {protocol_name} for motor ID {motor_id}")
                else:
                    print(f"  No response from motor ID {motor_id}")
            
        # Close the port
        ser.close()
        print(f"Closed {port_name}")
        return True
        
    except Exception as e:
        print(f"Error testing {port_name}: {e}")
        return False

if __name__ == "__main__":
    print("=== LEADER ARM PROTOCOL TEST ===")
    success = test_protocol()
    
    if not success:
        print("\nTest failed. Most likely causes:")
        print("1. Power supply is not connected or not turned on")
        print("2. Leader arm needs a 7.4V power supply for STS3215 motors")
        print("3. Control board may be defective")
        print("4. Motor connections may be loose or damaged")
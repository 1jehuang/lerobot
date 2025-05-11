import serial.tools.list_ports
import time
import sys

def list_com_ports():
    ports = list(serial.tools.list_ports.comports())
    print(f"Found {len(ports)} COM ports:")
    for port in ports:
        print(f"  {port.device}: {port.description}")
    return ports

def monitor_for_new_devices(duration=30):
    """
    Monitor for new USB devices for the specified duration (in seconds)
    """
    print(f"Initial state:")
    initial_ports = list_com_ports()
    
    print(f"\nPlease connect your device now. Monitoring for {duration} seconds...")
    end_time = time.time() + duration
    
    try:
        while time.time() < end_time:
            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()
            
            # Check every 5 seconds
            if int(end_time - time.time()) % 5 == 0:
                current_ports = list(serial.tools.list_ports.comports())
                new_ports = [p for p in current_ports if p.device not in [ip.device for ip in initial_ports]]
                
                if new_ports:
                    print("\nNew devices detected:")
                    for port in new_ports:
                        print(f"  {port.device}: {port.description}")
                    initial_ports = current_ports
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    
    print("\nFinal state:")
    final_ports = list_com_ports()
    
    # Check for new devices
    new_devices = [p for p in final_ports if p.device not in [ip.device for ip in initial_ports]]
    if new_devices:
        print("\nDevices added during monitoring:")
        for device in new_devices:
            print(f"  {device.device}: {device.description}")
    else:
        print("\nNo new devices detected during monitoring.")

if __name__ == "__main__":
    monitor_for_new_devices(30)  # Monitor for 30 seconds

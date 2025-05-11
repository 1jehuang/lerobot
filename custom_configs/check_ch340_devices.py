import serial.tools.list_ports
import re

def find_ch340_devices():
    """Find all connected CH340 devices"""
    print("Looking for CH340 devices...")
    
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("No COM ports found at all. Make sure your devices are connected.")
        return []
    
    ch340_pattern = re.compile(r'(?i)ch340|usb.*serial|feetech|sts|servo', re.IGNORECASE)
    ch340_ports = []
    
    print("All COM ports found:")
    for port in ports:
        print(f"  {port.device}: {port.description}")
        if (ch340_pattern.search(port.description.lower()) or 
            (hasattr(port, 'manufacturer') and port.manufacturer and ch340_pattern.search(port.manufacturer.lower()))):
            ch340_ports.append(port)
    
    if ch340_ports:
        print("\nPossible CH340 devices:")
        for port in ch340_ports:
            print(f"  {port.device}: {port.description}")
            # Print additional details if available
            if hasattr(port, 'manufacturer') and port.manufacturer:
                print(f"    Manufacturer: {port.manufacturer}")
            if hasattr(port, 'product') and port.product:
                print(f"    Product: {port.product}")
            if hasattr(port, 'serial_number') and port.serial_number:
                print(f"    Serial Number: {port.serial_number}")
            if hasattr(port, 'hwid') and port.hwid:
                print(f"    Hardware ID: {port.hwid}")
    else:
        print("\nNo CH340 devices found. Please connect your motor controller.")
    
    return ch340_ports

if __name__ == "__main__":
    find_ch340_devices()

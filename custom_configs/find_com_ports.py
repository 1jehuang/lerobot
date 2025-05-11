import serial.tools.list_ports

def find_com_ports():
    """Find all the available COM ports and their descriptions"""
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("No COM ports found. Make sure your devices are connected.")
        return []
    
    print("Available COM ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    
    return ports

if __name__ == "__main__":
    find_com_ports()

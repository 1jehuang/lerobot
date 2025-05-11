import serial.tools.list_ports; ports = list(serial.tools.list_ports.comports()); print(f"Found {len(ports)} COM ports:"); [print(f"{p.device} - {p.description}") for p in ports]  

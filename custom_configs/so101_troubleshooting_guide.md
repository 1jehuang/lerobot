# SO-101 Robot Arm Troubleshooting Guide

## Current Status

1. **Hardware Identified**:
   - Leader arm: Connected to COM3 (USB-Enhanced-SERIAL CH343)
   - Follower arm: Connected to COM4 (USB-Enhanced-SERIAL CH343)

2. **Current Issues**:
   - **Leader arm (COM3)**: Not responding to any commands
   - **Both arms**: Currently showing "Access denied" errors when attempting to open serial ports

## Step-by-Step Troubleshooting

### 1. Restart Your Computer

The "Access denied" errors suggest that serial ports may be locked by previous processes. A full system restart will clear all these locks.

### 2. Power Supply Check

The most likely issue with the leader arm is a power supply problem:

- **Verify power connection**: Make sure the power supply is properly connected to the leader arm controller
- **Check the power supply**: The leader arm requires a 7.4V power supply for STS3215 motors
- **Inspect indicator lights**: Check if there are any LED lights on the leader arm controller
- **Check connectors**: Ensure all wires are firmly seated and not loose
- **Test with multimeter**: If available, verify voltage output from the power supply

### 3. Hardware Inspection

- **Visual inspection**: Check for any damaged wires or connectors
- **Motor connections**: Ensure all motors are properly connected to the controller board
- **Controller board**: Look for any visible damage or loose components

### 4. Testing After Restart

After restarting, run this simplified test script:

```bash
cd C:\Users\jerem\Downloads\lerobot\custom_configs
python simplified_motor_test.py
```

### 5. Swap Test

Try swapping USB connections to verify if it's a port issue:

- Disconnect both USB cables
- Connect the leader arm USB to COM4 and the follower arm USB to COM3
- Run the swap test script:

```bash
cd C:\Users\jerem\Downloads\lerobot\custom_configs
python swap_test.py
```

### 6. Try Different Baudrates and Protocol Versions

The leader arm might be configured differently:

```bash
cd C:\Users\jerem\Downloads\lerobot\custom_configs
python leader_protocol_test.py
```

### 7. Basic Functionality Test

If the follower arm works after restart, use this script to verify its functions:

```bash
cd C:\Users\jerem\Downloads\lerobot\custom_configs
python teleoperate_follower.py
```

## Possible Issues and Solutions

1. **Power Supply Issues**:
   - **Problem**: Leader arm not receiving power
   - **Solution**: Check power supply connections, verify voltage, test with an alternative power supply if available

2. **Serial Port Issues**:
   - **Problem**: Software unable to access COM ports
   - **Solution**: Restart computer, check Device Manager, reinstall drivers if needed

3. **Controller Board Issues**:
   - **Problem**: Defective controller board on leader arm
   - **Solution**: If power is reaching the board but motors don't respond, the controller may need replacement

4. **Motor Configuration Issues**:
   - **Problem**: Leader arm motors might be using different IDs or protocol
   - **Solution**: Try scanning for motors with IDs 1-20 and test different protocol versions (0, 1, 2)

5. **Wiring Issues**:
   - **Problem**: Disconnected or damaged wires
   - **Solution**: Check all connections between controller and motors

## Working with the Follower Arm Only

If you're unable to get the leader arm working, you can still use the follower arm:

1. Operate the follower arm using the teleoperate_follower.py script
2. Modify your project goals to use only one arm
3. Consider ordering a replacement controller board for the leader arm if it's determined to be defective

## Next Steps

1. Restart your computer
2. Run through the tests in the order presented above
3. Document what works and what doesn't
4. If the leader arm still doesn't respond after power checks, consider contacting technical support or ordering replacement parts
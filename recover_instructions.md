# Recovery Instructions for the SO-101 Robot Arms

Based on the available documentation and tests, we need to perform a complete recovery procedure:

## Step 1: Complete Power Cycle

1. Disconnect the power supply from both the leader and follower arms
2. Disconnect the USB cables from the computer
3. Wait 30 seconds for capacitors to discharge
4. Reconnect the power supply to both arms
5. Reconnect the USB cables to the computer

## Step 2: Check Physical State

1. Verify no physical locks are engaged on the follower arm joints
2. Check if motors can be moved manually (gently, by hand - do this carefully)
3. Ensure all cables are firmly connected
4. Make sure nothing is obstructing the arm's movement

## Step 3: Check COM Port Assignments

After reconnecting, run this command to find what COM ports are assigned:

```
cd c:\Users\jerem\Downloads\lerobot && python -c "import serial.tools.list_ports; ports = list(serial.tools.list_ports.comports()); print(f'Found {len(ports)} COM ports:'); [print(f'{p.device} - {p.description}') for p in ports]"
```

## Step 4: Test with Working Arm Controller

Once you've identified the correct COM port for the working arm (previously on COM4), try:

```
cd c:\Users\jerem\Downloads\lerobot && python custom_configs\working_arm_controller.py
```

You may need to edit the port in the script if it's changed from COM4.

## Step 5: If No COM Ports Appear

If no COM ports appear after reconnection:
1. Try different USB ports on your computer
2. Check if the USB cables need to be replaced
3. Look for any LED indicators on the USB adapters to verify they're receiving power

## Step 6: After Ports are Detected

Once ports are detected, use the scripts in the following order:
1. Run `follower_test_fixed.py` to verify communication
2. Run `direct_reset_follower_motors.py` to reset motor parameters
3. Run `follower_move_test.py` to test if motors can move
4. Run `working_arm_controller.py` for interactive control

Remember to edit any scripts if the COM port numbers have changed from COM3 and COM4.

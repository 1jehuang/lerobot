# SO-101 Follower Arm Recovery Guide

## Initial Troubleshooting

1. **Complete Power Cycle**
   - Disconnect the power supply from both the leader and follower arms
   - Disconnect the USB cables from the computer
   - Wait 30 seconds for capacitors to discharge
   - Reconnect the power supply
   - Reconnect the USB cables

2. **Check Physical State**
   - Ensure there are no physical locks engaged on the follower arm joints
   - Check if the motors can be moved manually (gently, by hand)
   - Verify all cables are firmly connected
   - Make sure nothing is obstructing the arm's movement

## Software Reset Procedure

3. **Factory Reset the Motors**
   - Run the revised reset script below that uses a different approach
   - This will restore default parameters and clear any invalid states

4. **Test Movement**
   - After reset, test with the enhanced movement test script

## Hardware Recovery Options

If software reset doesn't work:

5. **Check Hardware Reset Button**
   - Many servo motors have a small reset button or pin hole
   - Check the documentation for the STS3215 motors
   - If present, use a paperclip to press the reset button on each motor

6. **Check Alternative Power Source**
   - Try connecting the follower arm to a different power supply
   - Measure voltage at the power input (should be close to 12V)

7. **Check USB-to-Serial Adapter**
   - Try replacing the USB-to-Serial adapter if available
   - Ensure driver is properly installed

## Port Swapping Test

8. **Try the Follower on the Leader Port**
   - This will verify if there's an issue with the specific port
   - Run the port swap test script

## Final Options

9. **Firmware Re-flash**
   - If available, use manufacturer's software to reflash the motor firmware
   - This would require the official Feetech motor configuration tool

10. **Mechanical Inspection**
    - If all else fails, physically inspect the motors for damage
    - Look for physical brake mechanisms that might need manual release

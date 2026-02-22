"""
Quick test to see if multi-turn works in Mode 3
"""

import time
import config
from python_st3215 import ST3215

print("QUICK MULTI-TURN TEST")
print("="*50)

controller = ST3215(config.SERIAL_CONFIG['port'])
servo = controller.wrap_servo(config.SERVO_CONFIG['default_id'])

try:
    # Simple test: Set to mode 3 and try to go beyond 4095
    servo.sram.torque_enable()

    print("1. Setting mode to 3...")
    servo.eeprom.write_operating_mode(3)
    time.sleep(0.3)

    mode = servo.eeprom.read_operating_mode()
    print(f"   Current mode: {mode}")

    if mode == 3:
        print("\n2. Testing position beyond 4095...")
        start = servo.sram.read_current_location()
        print(f"   Start position: {start}")

        target = 10000  # Beyond single-turn range
        print(f"   Target position: {target}")

        servo.sram.write_running_speed(800)
        servo.sram.write_target_location(target)
        time.sleep(3)

        end = servo.sram.read_current_location()
        print(f"   End position: {end}")

        if end > 4095:
            print("\n✓ SUCCESS: Multi-turn works!")
            print(f"   Moved to position {end} (> 4095)")
        elif end == target:
            print("\n✓ SUCCESS: Reached target exactly!")
            print("   (Might still be multi-turn, just within range)")
        else:
            print(f"\n⚠ Result: Position {end}")
            print("   Try larger target (e.g., 10000) to confirm multi-turn")

    else:
        print("\n✗ Failed to set mode 3")

finally:
    # Reset
    servo.sram.write_running_speed(0)
    servo.eeprom.write_operating_mode(0)
    servo.sram.torque_disable()
    controller.close()

# physical_test.py
from python_st3215 import ST3215
import time

controller = ST3215('COM4')
servo = controller.wrap_servo(1)

print("=== PHYSICAL TORQUE TEST ===")
print("\n1. Torque ENABLED - try to move servo (should be very stiff)")
servo.sram.torque_enable()
time.sleep(1)
input("   Press Enter when ready...")

print("\n2. Torque DISABLED - try to move servo")
servo.sram.torque_disable()
time.sleep(1)
input("   Press Enter when ready...")

print("\n3. Note the difference:")
print("   - If BOTH feel stiff: torque isn't disabling")
print("   - If disabled feels slightly easier: it's working")
print("   - Gearboxes are always somewhat stiff")

controller.close()

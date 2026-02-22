import time
import tkinter as tk
from tkinter import messagebox
from python_st3215 import ST3215, ServoNotRespondingError
import threading
import config
from gui import ServoControllerGUI

# Configuration
SCS_ID = config.SERVO_CONFIG['default_id']
portName = config.SERIAL_CONFIG['port']
MAX_SPEED = config.get_servo_params()['max_speed']

# Global variables
controller = None
servo = None
speed_percent = 10
MAX_SPEED = 32766
current_speed = 0
direction = 0
running = True
monitoring = False
comm_lock = threading.Lock()
current_position = None
gui = None
current_mode = 0  # Track mode: 0=Position, 1=Wheel


def initialize_servo():
    """Initialize servo connection and read initial position"""
    global controller, servo, monitoring, current_position, current_mode
    try:
        # Use config values
        controller = ST3215(portName)
        servo = controller.wrap_servo(SCS_ID)

        # Get servo params from config
        servo_params = config.get_servo_params()

        print(f"=== INITIALIZATION ===")
        print(f"Port: {portName}")
        print(f"Servo ID: {SCS_ID}")
        print(f"Servo Type: {config.SERVO_CONFIG['servo_type']}")
        print(f"Digital Range: {servo_params['digital_range']}")
        print(f"Angle Range: {servo_params['angle_range']}°")

        # START IN POSITION MODE (not wheel mode!)
        print("=== INITIALIZATION ===")
        print("Setting to POSITION mode (mode 0)...")
        servo.eeprom.write_operating_mode(0)
        time.sleep(0.5)
        current_mode = 0

        servo.sram.torque_enable()
        time.sleep(0.1)

        # Read initial position on startup
        current_position = servo.sram.read_current_location()
        if current_position is not None:
            angle = (current_position / 4096.0) * 360.0
            gui.update_telemetry({
                'position': current_position,
                'angle': angle
            })
            gui.set_knob_angle(angle)
            print(f"=== STARTUP ===")
            print(f"Initial position: {current_position}")
            print(f"Initial angle: {angle:.1f}°")
            print(f"Operating mode: {current_mode} (Position Mode)")

        gui.update_status("✓ Servo connected (Position Mode)", "green")
        monitoring = True
        threading.Thread(target=monitor_servo, daemon=True).start()
        return True
    except ServoNotRespondingError:
        gui.update_status("✗ Cannot connect to servo!", "red")
        return False
    except Exception as e:
        print(f"Initialization error: {e}")
        import traceback
        traceback.print_exc()
        gui.update_status("✗ Connection error!", "red")
        return False


def monitor_servo():
    """Background thread to read servo telemetry continuously"""
    global current_position
    while running and monitoring:
        try:
            if servo and not comm_lock.locked():
                with comm_lock:
                    position = servo.sram.read_current_location()
                    speed = servo.sram.read_current_speed()
                    temp = servo.sram.read_current_temperature()
                    voltage = servo.sram.read_current_voltage()
                    current = servo.sram.read_current_current()
                    load = servo.sram.read_current_load()
                    moving = servo.sram.is_moving()

                # Update current position global variable
                if position is not None:
                    current_position = position
                    angle = (position / 4096.0) * 360.0

                    # Update GUI
                    telemetry_data = {
                        'position': position,
                        'angle': angle,
                        'speed': speed if speed is not None else '--',
                        'temp': temp if temp is not None else '--',
                        'voltage': voltage if voltage is not None else '--',
                        'current': current if current is not None else '--',
                        'load': load if load is not None else '--',
                        'moving': moving if moving is not None else False
                    }

                    gui.root.after(0, lambda d=telemetry_data: gui.update_telemetry(d))
                    gui.root.after(0, lambda a=angle: gui.set_knob_angle(a))

        except Exception as e:
            pass

        time.sleep(0.2)


def update_speed():
    """Update the current speed value based on percentage"""
    global current_speed
    current_speed = int((speed_percent / 100.0) * MAX_SPEED)


def stop_servo():
    """Stop all servo movement and switch back to position mode"""
    global direction, current_mode
    if servo:
        with comm_lock:
            servo.sram.write_running_speed(0)
            time.sleep(0.3)

            # If in wheel mode, switch back to position mode
            if current_mode == 1:
                print("Stopping: Switching back to position mode...")
                servo.eeprom.write_operating_mode(0)
                time.sleep(0.3)
                current_mode = 0
                servo.sram.torque_enable()
                if gui:
                    gui.update_status("✓ Servo connected (Position Mode)", "green")

        direction = 0
        if gui:
            gui.update_direction("Direction: STOPPED", "gray")


def move_cw():
    """Start continuous clockwise rotation - switches to WHEEL MODE"""
    global direction, current_mode
    if not servo:
        return

    with comm_lock:
        # Switch to wheel mode for continuous rotation
        if current_mode == 0:
            print("CW: Switching to wheel mode for continuous rotation...")
            servo.sram.write_running_speed(0)
            time.sleep(0.2)
            servo.eeprom.write_operating_mode(1)
            time.sleep(0.3)
            current_mode = 1
            servo.sram.torque_enable()
            time.sleep(0.2)

        direction = 1
        # For CW rotation (clockwise), use NEGATIVE speed
        # Remove the inverted calculation, use direct negative speed
        cw_speed = -current_speed  # Simple negative for clockwise
        servo.sram.write_running_speed(cw_speed)

    # Update GUI through the gui object
    if gui:
        gui.update_direction("Direction: CLOCKWISE ➜ (Wheel Mode)", "blue")
        gui.update_status("✓ Wheel Mode (Continuous Rotation)", "blue")

def move_ccw():
    """Start continuous counter-clockwise rotation - switches to WHEEL MODE"""
    global direction, current_mode
    if not servo:
        return

    with comm_lock:
        # Switch to wheel mode for continuous rotation
        if current_mode == 0:
            print("CCW: Switching to wheel mode for continuous rotation...")
            servo.sram.write_running_speed(0)
            time.sleep(0.2)
            servo.eeprom.write_operating_mode(1)
            time.sleep(0.3)
            current_mode = 1
            servo.sram.torque_enable()
            time.sleep(0.2)

        direction = -1
        # For CCW rotation (counter-clockwise), use POSITIVE speed
        servo.sram.write_running_speed(current_speed)

    # Update GUI through the gui object
    if gui:
        gui.update_direction("Direction: ← COUNTER-CLOCKWISE (Wheel Mode)", "orange")
        gui.update_status("✓ Wheel Mode (Continuous Rotation)", "orange")



def go_to_angle_cw():
    """Go to absolute angle (0-360°) - reads from CW input field - STAYS IN POSITION MODE"""
    global current_mode
    try:
        target_angle = float(gui.get_cw_angle())  # ← Read from CW field!
        if target_angle < 0 or target_angle > 360:
            messagebox.showerror("Error", "Angle must be between 0 and 360")
            return

        target_position = int((target_angle / 360.0) * 4096.0)
        if target_position >= 4096:
            target_position = 4095

        print(f"\n=== GO TO {target_angle}° (CW) ===")
        print(f"Target position: {target_position}")

        with comm_lock:
            # Ensure we're in position mode
            if current_mode == 1:
                print("Switching from wheel to position mode...")
                servo.sram.write_running_speed(0)
                time.sleep(0.3)
                servo.eeprom.write_operating_mode(0)
                time.sleep(0.3)
                current_mode = 0
                servo.sram.torque_enable()
                time.sleep(0.2)

            servo.sram.write_running_speed(0)
            time.sleep(0.3)

            current_pos = servo.sram.read_current_location()
            if current_pos is not None:
                current_ang = (current_pos / 4096.0) * 360.0
                print(f"Current position: {current_pos} ({current_ang:.1f}°)")

            print("Already in position mode, moving...")
            servo.sram.torque_enable()
            time.sleep(0.1)

            speed = int(MAX_SPEED * 0.3)
            print(f"Setting speed: {speed}, acceleration: 100")
            servo.sram.write_running_speed(speed)
            servo.sram.write_acceleration(100)
            time.sleep(0.1)

            print(f"Moving to position {target_position}...")
            servo.sram.write_target_location(target_position)

        gui.update_status(f"Moving to {target_angle}°...", "blue")

        def monitor_movement():
            print("Monitoring movement...")
            time.sleep(1)

            for i in range(50):
                with comm_lock:
                    current_pos = servo.sram.read_current_location()
                    is_moving = servo.sram.is_moving()

                if current_pos is not None:
                    current_ang = (current_pos / 4096.0) * 360.0
                    print(
                        f"Position: {current_pos} ({current_ang:.1f}°), Target: {target_position}, Moving: {is_moving}")

                if current_pos and abs(current_pos - target_position) < 20:
                    print(f"✓ Reached target!")
                    break

                if not is_moving and i > 5:
                    print("Movement stopped")
                    break

                time.sleep(0.2)

            # STAY IN POSITION MODE - just stop movement
            print("Stopping movement (staying in position mode)...")
            with comm_lock:
                servo.sram.write_running_speed(0)

            print("Done!\n")
            gui.update_status("✓ Servo connected (Position Mode)", "green")

        threading.Thread(target=monitor_movement, daemon=True).start()

    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Error: {str(e)}")


def go_to_angle_ccw():
    """Go to absolute angle (0-360°) - reads from CCW input field - STAYS IN POSITION MODE"""
    global current_mode
    try:
        target_angle = float(gui.get_ccw_angle())  # ← Read from CCW field!
        if target_angle < 0 or target_angle > 360:
            messagebox.showerror("Error", "Angle must be between 0 and 360")
            return

        target_position = int((target_angle / 360.0) * 4096.0)
        if target_position >= 4096:
            target_position = 4095

        print(f"\n=== GO TO {target_angle}° (CCW) ===")
        print(f"Target position: {target_position}")

        with comm_lock:
            # Ensure we're in position mode
            if current_mode == 1:
                print("Switching from wheel to position mode...")
                servo.sram.write_running_speed(0)
                time.sleep(0.3)
                servo.eeprom.write_operating_mode(0)
                time.sleep(0.3)
                current_mode = 0
                servo.sram.torque_enable()
                time.sleep(0.2)

            servo.sram.write_running_speed(0)
            time.sleep(0.3)

            current_pos = servo.sram.read_current_location()
            if current_pos is not None:
                current_ang = (current_pos / 4096.0) * 360.0
                print(f"Current position: {current_pos} ({current_ang:.1f}°)")

            print("Already in position mode, moving...")
            servo.sram.torque_enable()
            time.sleep(0.1)

            speed = int(MAX_SPEED * 0.3)
            print(f"Setting speed: {speed}, acceleration: 100")
            servo.sram.write_running_speed(speed)
            servo.sram.write_acceleration(100)
            time.sleep(0.1)

            print(f"Moving to position {target_position}...")
            servo.sram.write_target_location(target_position)

        gui.update_status(f"Moving to {target_angle}°...", "blue")

        def monitor_movement():
            print("Monitoring movement...")
            time.sleep(1)

            for i in range(50):
                with comm_lock:
                    current_pos = servo.sram.read_current_location()
                    is_moving = servo.sram.is_moving()

                if current_pos is not None:
                    current_ang = (current_pos / 4096.0) * 360.0
                    print(
                        f"Position: {current_pos} ({current_ang:.1f}°), Target: {target_position}, Moving: {is_moving}")

                if current_pos and abs(current_pos - target_position) < 20:
                    print(f"✓ Reached target!")
                    break

                if not is_moving and i > 5:
                    print("Movement stopped")
                    break

                time.sleep(0.2)

            # STAY IN POSITION MODE - just stop movement
            print("Stopping movement (staying in position mode)...")
            with comm_lock:
                servo.sram.write_running_speed(0)

            print("Done!\n")
            gui.update_status("✓ Servo connected (Position Mode)", "green")

        threading.Thread(target=monitor_movement, daemon=True).start()

    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Error: {str(e)}")


def increment_angle_cw():
    """Move by increment angle in positive direction - STAYS IN POSITION MODE"""
    global current_mode
    try:
        increment = float(gui.get_increment())
        print(f"\n=== INCREMENT +{increment}° ===")

        with comm_lock:
            # Ensure we're in position mode
            if current_mode == 1:
                print("Switching from wheel to position mode...")
                servo.sram.write_running_speed(0)
                time.sleep(0.3)
                servo.eeprom.write_operating_mode(0)
                time.sleep(0.3)
                current_mode = 0
                servo.sram.torque_enable()
                time.sleep(0.2)

            servo.sram.write_running_speed(0)
            time.sleep(0.3)

        with comm_lock:
            current_pos = servo.sram.read_current_location()
            print(f"Current position: {current_pos}")

            if current_pos is None:
                messagebox.showwarning("Warning", "Cannot read position")
                return

            current_angle = (current_pos / 4096.0) * 360.0
            target_angle = (current_angle + increment) % 360.0
            target_position = int((target_angle / 360.0) * 4096.0)
            if target_position >= 4096:
                target_position = 4095

            print(f"Current: {current_angle:.1f}°")
            print(f"Target: {target_angle:.1f}°")
            print(f"Target position: {target_position}")

            print("Already in position mode, moving...")
            servo.sram.torque_enable()
            time.sleep(0.1)

            speed = int(MAX_SPEED * 0.2)
            print(f"Setting speed: {speed}, acceleration: 100")
            servo.sram.write_running_speed(speed)
            servo.sram.write_acceleration(100)
            time.sleep(0.1)

            print(f"Moving to position {target_position}...")
            servo.sram.write_target_location(target_position)

        gui.update_status(f"Moving +{increment}° → {target_angle:.1f}°", "blue")

        def monitor_movement():
            print("Monitoring...")
            time.sleep(1)

            for i in range(20):
                with comm_lock:
                    moving = servo.sram.is_moving()
                    current = servo.sram.read_current_location()

                if current:
                    current_ang = (current / 4096.0) * 360.0
                    print(f"Position: {current} ({current_ang:.1f}°), Moving: {moving}")

                if not moving:
                    print("✓ Complete!")
                    break

                time.sleep(0.2)

            # STAY IN POSITION MODE - just stop movement
            print("Stopping movement (staying in position mode)...")
            with comm_lock:
                servo.sram.write_running_speed(0)

            print("Done!\n")
            gui.update_status("✓ Servo connected (Position Mode)", "green")

        threading.Thread(target=monitor_movement, daemon=True).start()

    except ValueError:
        messagebox.showerror("Error", "Enter valid number")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Error: {str(e)}")


def decrement_angle_cw():
    """Move by increment angle in negative direction - STAYS IN POSITION MODE"""
    global current_mode
    try:
        increment = float(gui.get_increment())
        print(f"\n=== DECREMENT -{increment}° ===")

        with comm_lock:
            # Ensure we're in position mode
            if current_mode == 1:
                print("Switching from wheel to position mode...")
                servo.sram.write_running_speed(0)
                time.sleep(0.3)
                servo.eeprom.write_operating_mode(0)
                time.sleep(0.3)
                current_mode = 0
                servo.sram.torque_enable()
                time.sleep(0.2)

            servo.sram.write_running_speed(0)
            time.sleep(0.3)

        with comm_lock:
            current_pos = servo.sram.read_current_location()
            print(f"Current position: {current_pos}")

            if current_pos is None:
                messagebox.showwarning("Warning", "Cannot read position")
                return

            current_angle = (current_pos / 4096.0) * 360.0
            target_angle = (current_angle - increment) % 360.0
            target_position = int((target_angle / 360.0) * 4096.0)
            if target_position >= 4096:
                target_position = 4095

            print(f"Current: {current_angle:.1f}°")
            print(f"Target: {target_angle:.1f}°")
            print(f"Target position: {target_position}")

            print("Already in position mode, moving...")
            servo.sram.torque_enable()
            time.sleep(0.1)

            speed = int(MAX_SPEED * 0.2)
            print(f"Setting speed: {speed}, acceleration: 100")
            servo.sram.write_running_speed(speed)
            servo.sram.write_acceleration(100)
            time.sleep(0.1)

            print(f"Moving to position {target_position}...")
            servo.sram.write_target_location(target_position)

        gui.update_status(f"Moving -{increment}° → {target_angle:.1f}°", "orange")

        def monitor_movement():
            print("Monitoring...")
            time.sleep(1)

            for i in range(20):
                with comm_lock:
                    moving = servo.sram.is_moving()
                    current = servo.sram.read_current_location()

                if current:
                    current_ang = (current / 4096.0) * 360.0
                    print(f"Position: {current} ({current_ang:.1f}°), Moving: {moving}")

                if not moving:
                    print("✓ Complete!")
                    break

                time.sleep(0.2)

            # STAY IN POSITION MODE - just stop movement
            print("Stopping movement (staying in position mode)...")
            with comm_lock:
                servo.sram.write_running_speed(0)

            print("Done!\n")
            gui.update_status("✓ Servo connected (Position Mode)", "green")

        threading.Thread(target=monitor_movement, daemon=True).start()

    except ValueError:
        messagebox.showerror("Error", "Enter valid number")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Error: {str(e)}")


def increment_angle_ccw():
    increment_angle_cw()


def decrement_angle_ccw():
    decrement_angle_cw()


def debug_position():
    try:
        with comm_lock:
            pos = servo.sram.read_current_location()
            mode = servo.eeprom.read_operating_mode()
            target = servo.sram.read_target_location()

        if pos is not None:
            angle = (pos / 4096.0) * 360.0

            debug_text = f"""Position Information:
========================
Raw Position: {pos}
Angle: {angle:.2f}°
Operating Mode: {mode} (0=Position, 1=Wheel)
Target Location: {target}

Position Range: 0-4095 (4096 positions)
Angle Range: 0-360°
Current Global Variable: {current_position}
Software Mode Tracking: {current_mode}
"""

            messagebox.showinfo("Position Debug", debug_text)
            print(debug_text)

    except Exception as e:
        print(f"Debug error: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Debug failed: {str(e)}")


def increase_speed():
    global speed_percent
    if speed_percent < 100:
        speed_percent += 10
        update_speed()
        gui.update_speed_display(speed_percent)
        if direction == 1:
            move_cw()
        elif direction == -1:
            move_ccw()


def decrease_speed():
    global speed_percent
    if speed_percent > 10:
        speed_percent -= 10
        update_speed()
        gui.update_speed_display(speed_percent)
        if direction == 1:
            move_cw()
        elif direction == -1:
            move_ccw()


def on_slider_change(val):
    global speed_percent
    speed_percent = int(float(val))
    gui.update_speed_display(speed_percent)
    update_speed()
    if direction == 1:
        move_cw()
    elif direction == -1:
        move_ccw()


def on_closing():
    global running, monitoring
    running = False
    monitoring = False
    if servo:
        stop_servo()
    if controller:
        controller.close()
    root.destroy()


# ... (keep all the existing functions up to the on_closing function) ...

def on_knob_angle_change(angle):
    """Handle knob angle changes"""
    global current_mode
    if not servo:
        return

    target_position = int((angle / 360.0) * 4096.0)
    if target_position >= 4096:
        target_position = 4095

    def move_servo():
        try:
            with comm_lock:
                # Ensure we're in position mode
                if current_mode == 1:
                    servo.sram.write_running_speed(0)
                    time.sleep(0.2)
                    servo.eeprom.write_operating_mode(0)
                    time.sleep(0.3)
                    current_mode = 0
                    servo.sram.torque_enable()
                    time.sleep(0.2)

                # Set target in position mode
                servo.sram.write_target_location(target_position)
                servo.sram.write_running_speed(int(MAX_SPEED * 0.5))
                servo.sram.write_acceleration(50)

        except Exception as e:
            print(f"Knob error: {e}")

    threading.Thread(target=move_servo, daemon=True).start()


def setup_callbacks():
    """Setup callback functions for GUI"""
    return {
        'move_cw': move_cw,
        'move_ccw': move_ccw,
        'stop_servo': stop_servo,
        'go_to_angle_cw': go_to_angle_cw,
        'go_to_angle_ccw': go_to_angle_ccw,
        'increment_angle_cw': increment_angle_cw,
        'decrement_angle_cw': decrement_angle_cw,
        'increment_angle_ccw': increment_angle_ccw,
        'decrement_angle_ccw': decrement_angle_ccw,
        'increase_speed': increase_speed,
        'decrease_speed': decrease_speed,
        'on_slider_change': on_slider_change,
        'debug_position': debug_position
    }


def main():
    """Main function to start the application"""
    global root, gui

    root = tk.Tk()

    # Setup callbacks
    callbacks = setup_callbacks()

    # Create GUI
    gui = ServoControllerGUI(root, callbacks)

    # Setup knob callback
    gui.set_knob_callback(on_knob_angle_change)

    update_speed()
    root.after(100, initialize_servo)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
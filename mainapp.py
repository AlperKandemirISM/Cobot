import time
import tkinter as tk
from tkinter import ttk, messagebox
from python_st3215 import ST3215, ServoNotRespondingError
import threading
import config
from gui import ServoControllerGUI

# Configuration
portName = config.SERIAL_CONFIG['port']
MAX_SPEED = config.get_servo_params()['max_speed']

# Global variables
controller = None
servos = {}  # Dictionary to hold servo objects by ID
active_servo_id = config.SERVO_CONFIG['default_id']  # Currently selected servo
servo_status = {}  # Track status of each servo
speed_percent = 10
current_speed = 0
direction = 0
running = True
monitoring = False
comm_lock = threading.Lock()
current_positions = {}  # Track positions for all servos
gui = None
current_modes = {}  # Track modes for each servo: 0=Position, 1=Wheel

# Servo IDs to manage - 1'den 7'ye kadar
SERVO_IDS = [1, 2, 3, 4, 5, 6, 7]  # 7. servo eklendi

def initialize_servos():
    """Initialize connection to all servos"""
    global controller, monitoring
    try:
        controller = ST3215(portName)
        servo_params = config.get_servo_params()

        print(f"=== INITIALIZATION ===")
        print(f"Port: {portName}")
        print(f"Servo Type: {config.SERVO_CONFIG['servo_type']}")
        print(f"Digital Range: {servo_params['digital_range']}")
        print(f"Angle Range: {servo_params['angle_range']}°")
        print(f"Total Servos: {len(SERVO_IDS)} (1-7)")

        # Initialize each servo
        connected_count = 0
        for servo_id in SERVO_IDS:
            try:
                servo = controller.wrap_servo(servo_id)

                # Test communication by reading a register that definitely exists
                # Use read_current_location() as a connection test
                test_pos = servo.sram.read_current_location()
                if test_pos is not None:
                    servos[servo_id] = servo

                    # Set to position mode initially
                    print(f"Servo ID {servo_id}: Setting to POSITION mode (mode 0)...")
                    servo.eeprom.write_operating_mode(0)
                    time.sleep(0.2)
                    current_modes[servo_id] = 0

                    # Enable torque
                    servo.sram.torque_enable()
                    time.sleep(0.1)

                    # Read initial position
                    pos = servo.sram.read_current_location()
                    if pos is not None:
                        current_positions[servo_id] = pos
                        angle = (pos / 4096.0) * 360.0
                        print(f"  ID {servo_id}: Initial position={pos}, angle={angle:.1f}°")

                    servo_status[servo_id] = "Connected"
                    connected_count += 1
                    print(f"✓ Servo ID {servo_id} connected successfully")
                else:
                    print(f"Servo ID {servo_id}: Failed to read position")
                    servos[servo_id] = None
                    servo_status[servo_id] = "Disconnected"

            except Exception as e:
                print(f"Servo ID {servo_id}: Failed to connect - {e}")
                servos[servo_id] = None
                servo_status[servo_id] = "Disconnected"

        # Update GUI with connection status
        if connected_count > 0:
            status_text = f"✓ Connected to {connected_count}/7 servos"
            gui.update_status(status_text, "green")

            # Update servo selector
            gui.update_servo_selector(SERVO_IDS, servo_status)

            # Select first connected servo
            for sid in SERVO_IDS:
                if servo_status[sid] == "Connected":
                    switch_active_servo(sid)
                    break
        else:
            gui.update_status("✗ No servos connected!", "red")
            return False

        # Start monitoring thread
        monitoring = True
        threading.Thread(target=monitor_all_servos, daemon=True).start()
        return True

    except Exception as e:
        print(f"Initialization error: {e}")
        import traceback
        traceback.print_exc()
        gui.update_status("✗ Connection error!", "red")
        return False


def switch_active_servo(servo_id):
    """Switch the active servo being controlled"""
    global active_servo_id

    if servo_id in servos and servos[servo_id] is not None:
        active_servo_id = servo_id
        print(f"Switched to servo ID {servo_id}")

        # Update GUI with current position of selected servo
        if servo_id in current_positions:
            pos = current_positions[servo_id]
            angle = (pos / 4096.0) * 360.0
            gui.set_knob_angle(angle)

            # Update direction label based on mode
            mode = current_modes.get(servo_id, 0)
            if mode == 0:
                gui.update_direction(f"Servo {servo_id}: Position Mode", "blue")
            else:
                gui.update_direction(f"Servo {servo_id}: Wheel Mode", "orange")

        # Update telemetry for this servo
        update_active_servo_telemetry()


def monitor_all_servos():
    """Background thread to read telemetry from all servos"""
    while running and monitoring:
        try:
            for servo_id, servo in servos.items():
                if servo and not comm_lock.locked():
                    try:
                        with comm_lock:
                            position = servo.sram.read_current_location()
                            if position is not None:
                                current_positions[servo_id] = position

                                # Read other telemetry
                                speed = servo.sram.read_current_speed()
                                temp = servo.sram.read_current_temperature()
                                voltage = servo.sram.read_current_voltage()
                                current_val = servo.sram.read_current_current()
                                load = servo.sram.read_current_load()
                                moving = servo.sram.is_moving()

                                # Store telemetry
                                servo_status[servo_id] = {
                                    'position': position,
                                    'speed': speed,
                                    'temp': temp,
                                    'voltage': voltage,
                                    'current': current_val,
                                    'load': load,
                                    'moving': moving
                                }
                    except Exception as e:
                        # Silently ignore communication errors for individual servos
                        pass

            # Update GUI with active servo's telemetry
            if active_servo_id in servo_status:
                gui.root.after(0, lambda: update_active_servo_telemetry())

            # Update servo selector status indicators
            gui.root.after(0, lambda: gui.update_servo_status_indicators(servo_status))

        except Exception as e:
            pass

        time.sleep(0.2)


def update_active_servo_telemetry():
    """Update GUI with telemetry from active servo"""
    if active_servo_id in servo_status:
        data = servo_status[active_servo_id]
        if isinstance(data, dict):
            # Calculate angle
            if 'position' in data and data['position'] is not None:
                angle = (data['position'] / 4096.0) * 360.0
                telemetry = {
                    'position': data['position'],
                    'angle': angle,
                    'speed': data.get('speed', '--'),
                    'temp': data.get('temp', '--'),
                    'voltage': data.get('voltage', '--'),
                    'current': data.get('current', '--'),
                    'load': data.get('load', '--'),
                    'moving': data.get('moving', False)
                }
                gui.update_telemetry(telemetry)
                gui.set_knob_angle(angle)


def get_active_servo():
    """Get the currently active servo object"""
    if active_servo_id in servos:
        return servos[active_servo_id]
    return None


def update_speed():
    """Update the current speed value based on percentage"""
    global current_speed
    current_speed = int((speed_percent / 100.0) * MAX_SPEED)


def stop_servo():
    """Stop all servo movement and switch back to position mode"""
    global direction

    servo = get_active_servo()
    if not servo:
        messagebox.showwarning("Warning", f"Servo {active_servo_id} not connected")
        return

    servo_id = active_servo_id

    with comm_lock:
        servo.sram.write_running_speed(0)
        time.sleep(0.3)

        # If in wheel mode, switch back to position mode
        if current_modes.get(servo_id) == 1:
            print(f"Servo {servo_id}: Switching back to position mode...")
            servo.eeprom.write_operating_mode(0)
            time.sleep(0.3)
            current_modes[servo_id] = 0
            servo.sram.torque_enable()
            gui.update_status(f"✓ Servo {servo_id} (Position Mode)", "green")

    direction = 0
    gui.update_direction(f"Servo {servo_id}: STOPPED", "gray")


def move_cw():
    """Start continuous clockwise rotation - switches to WHEEL MODE"""
    global direction

    servo = get_active_servo()
    if not servo:
        messagebox.showwarning("Warning", f"Servo {active_servo_id} not connected")
        return

    servo_id = active_servo_id

    with comm_lock:
        # Switch to wheel mode for continuous rotation
        if current_modes.get(servo_id) == 0:
            print(f"Servo {servo_id}: Switching to wheel mode for continuous rotation...")
            servo.sram.write_running_speed(0)
            time.sleep(0.2)
            servo.eeprom.write_operating_mode(1)
            time.sleep(0.3)
            current_modes[servo_id] = 1
            servo.sram.torque_enable()
            time.sleep(0.2)

        direction = 1
        # For CW rotation (clockwise), use NEGATIVE speed
        cw_speed = -current_speed
        servo.sram.write_running_speed(cw_speed)

    gui.update_direction(f"Servo {servo_id}: CLOCKWISE ➜ (Wheel Mode)", "blue")
    gui.update_status(f"✓ Servo {servo_id} - Wheel Mode", "blue")


def move_ccw():
    """Start continuous counter-clockwise rotation - switches to WHEEL MODE"""
    global direction

    servo = get_active_servo()
    if not servo:
        messagebox.showwarning("Warning", f"Servo {active_servo_id} not connected")
        return

    servo_id = active_servo_id

    with comm_lock:
        # Switch to wheel mode for continuous rotation
        if current_modes.get(servo_id) == 0:
            print(f"Servo {servo_id}: Switching to wheel mode for continuous rotation...")
            servo.sram.write_running_speed(0)
            time.sleep(0.2)
            servo.eeprom.write_operating_mode(1)
            time.sleep(0.3)
            current_modes[servo_id] = 1
            servo.sram.torque_enable()
            time.sleep(0.2)

        direction = -1
        # For CCW rotation, use POSITIVE speed
        servo.sram.write_running_speed(current_speed)

    gui.update_direction(f"Servo {servo_id}: ← COUNTER-CLOCKWISE (Wheel Mode)", "orange")
    gui.update_status(f"✓ Servo {servo_id} - Wheel Mode", "orange")


def go_to_angle_cw():
    """Go to absolute angle - reads from CW input field"""
    servo = get_active_servo()
    if not servo:
        messagebox.showwarning("Warning", f"Servo {active_servo_id} not connected")
        return

    servo_id = active_servo_id

    try:
        target_angle = float(gui.get_cw_angle())
        if target_angle < 0 or target_angle > 360:
            messagebox.showerror("Error", "Angle must be between 0 and 360")
            return

        target_position = int((target_angle / 360.0) * 4096.0)
        if target_position >= 4096:
            target_position = 4095

        print(f"\n=== Servo {servo_id}: GO TO {target_angle}° (CW) ===")
        print(f"Target position: {target_position}")

        with comm_lock:
            # Ensure we're in position mode
            if current_modes.get(servo_id) == 1:
                print(f"Switching from wheel to position mode...")
                servo.sram.write_running_speed(0)
                time.sleep(0.3)
                servo.eeprom.write_operating_mode(0)
                time.sleep(0.3)
                current_modes[servo_id] = 0
                servo.sram.torque_enable()
                time.sleep(0.2)

            servo.sram.write_running_speed(0)
            time.sleep(0.3)

            current_pos = servo.sram.read_current_location()
            if current_pos is not None:
                current_ang = (current_pos / 4096.0) * 360.0
                print(f"Current position: {current_pos} ({current_ang:.1f}°)")

            speed = int(MAX_SPEED * 0.3)
            servo.sram.write_running_speed(speed)
            servo.sram.write_acceleration(100)
            time.sleep(0.1)

            servo.sram.write_target_location(target_position)

        gui.update_status(f"Servo {servo_id}: Moving to {target_angle}°...", "blue")

        def monitor_movement():
            time.sleep(1)
            for i in range(50):
                with comm_lock:
                    current_pos = servo.sram.read_current_location()
                    is_moving = servo.sram.is_moving()

                if current_pos and abs(current_pos - target_position) < 20:
                    break
                if not is_moving and i > 5:
                    break
                time.sleep(0.2)

            with comm_lock:
                servo.sram.write_running_speed(0)

            gui.update_status(f"✓ Servo {servo_id} (Position Mode)", "green")

        threading.Thread(target=monitor_movement, daemon=True).start()

    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number")
    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")


def go_to_angle_ccw():
    """Go to absolute angle - reads from CCW input field"""
    servo = get_active_servo()
    if not servo:
        messagebox.showwarning("Warning", f"Servo {active_servo_id} not connected")
        return

    servo_id = active_servo_id

    try:
        target_angle = float(gui.get_ccw_angle())
        if target_angle < 0 or target_angle > 360:
            messagebox.showerror("Error", "Angle must be between 0 and 360")
            return

        target_position = int((target_angle / 360.0) * 4096.0)
        if target_position >= 4096:
            target_position = 4095

        print(f"\n=== Servo {servo_id}: GO TO {target_angle}° (CCW) ===")
        print(f"Target position: {target_position}")

        with comm_lock:
            # Ensure we're in position mode
            if current_modes.get(servo_id) == 1:
                print(f"Switching from wheel to position mode...")
                servo.sram.write_running_speed(0)
                time.sleep(0.3)
                servo.eeprom.write_operating_mode(0)
                time.sleep(0.3)
                current_modes[servo_id] = 0
                servo.sram.torque_enable()
                time.sleep(0.2)

            servo.sram.write_running_speed(0)
            time.sleep(0.3)

            current_pos = servo.sram.read_current_location()
            if current_pos is not None:
                current_ang = (current_pos / 4096.0) * 360.0
                print(f"Current position: {current_pos} ({current_ang:.1f}°)")

            speed = int(MAX_SPEED * 0.3)
            servo.sram.write_running_speed(speed)
            servo.sram.write_acceleration(100)
            time.sleep(0.1)

            servo.sram.write_target_location(target_position)

        gui.update_status(f"Servo {servo_id}: Moving to {target_angle}°...", "blue")

        def monitor_movement():
            time.sleep(1)
            for i in range(50):
                with comm_lock:
                    current_pos = servo.sram.read_current_location()
                    is_moving = servo.sram.is_moving()

                if current_pos and abs(current_pos - target_position) < 20:
                    break
                if not is_moving and i > 5:
                    break
                time.sleep(0.2)

            with comm_lock:
                servo.sram.write_running_speed(0)

            gui.update_status(f"✓ Servo {servo_id} (Position Mode)", "green")

        threading.Thread(target=monitor_movement, daemon=True).start()

    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number")
    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")


def increment_angle_cw():
    """Move by increment angle in positive direction"""
    servo = get_active_servo()
    if not servo:
        messagebox.showwarning("Warning", f"Servo {active_servo_id} not connected")
        return

    servo_id = active_servo_id

    try:
        increment = float(gui.get_increment())
        print(f"\n=== Servo {servo_id}: INCREMENT +{increment}° ===")

        with comm_lock:
            # Ensure we're in position mode
            if current_modes.get(servo_id) == 1:
                print(f"Switching from wheel to position mode...")
                servo.sram.write_running_speed(0)
                time.sleep(0.3)
                servo.eeprom.write_operating_mode(0)
                time.sleep(0.3)
                current_modes[servo_id] = 0
                servo.sram.torque_enable()
                time.sleep(0.2)

            servo.sram.write_running_speed(0)
            time.sleep(0.3)

            current_pos = servo.sram.read_current_location()
            if current_pos is None:
                messagebox.showwarning("Warning", "Cannot read position")
                return

            current_angle = (current_pos / 4096.0) * 360.0
            target_angle = (current_angle + increment) % 360.0
            target_position = int((target_angle / 360.0) * 4096.0)
            if target_position >= 4096:
                target_position = 4095

            speed = int(MAX_SPEED * 0.2)
            servo.sram.write_running_speed(speed)
            servo.sram.write_acceleration(100)
            time.sleep(0.1)

            servo.sram.write_target_location(target_position)

        gui.update_status(f"Servo {servo_id}: Moving +{increment}° → {target_angle:.1f}°", "blue")

        def monitor_movement():
            time.sleep(1)
            for i in range(20):
                with comm_lock:
                    moving = servo.sram.is_moving()
                if not moving:
                    break
                time.sleep(0.2)

            with comm_lock:
                servo.sram.write_running_speed(0)

            gui.update_status(f"✓ Servo {servo_id} (Position Mode)", "green")

        threading.Thread(target=monitor_movement, daemon=True).start()

    except ValueError:
        messagebox.showerror("Error", "Enter valid number")
    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")


def decrement_angle_cw():
    """Move by increment angle in negative direction"""
    servo = get_active_servo()
    if not servo:
        messagebox.showwarning("Warning", f"Servo {active_servo_id} not connected")
        return

    servo_id = active_servo_id

    try:
        increment = float(gui.get_increment())
        print(f"\n=== Servo {servo_id}: DECREMENT -{increment}° ===")

        with comm_lock:
            # Ensure we're in position mode
            if current_modes.get(servo_id) == 1:
                print(f"Switching from wheel to position mode...")
                servo.sram.write_running_speed(0)
                time.sleep(0.3)
                servo.eeprom.write_operating_mode(0)
                time.sleep(0.3)
                current_modes[servo_id] = 0
                servo.sram.torque_enable()
                time.sleep(0.2)

            servo.sram.write_running_speed(0)
            time.sleep(0.3)

            current_pos = servo.sram.read_current_location()
            if current_pos is None:
                messagebox.showwarning("Warning", "Cannot read position")
                return

            current_angle = (current_pos / 4096.0) * 360.0
            target_angle = (current_angle - increment) % 360.0
            target_position = int((target_angle / 360.0) * 4096.0)
            if target_position >= 4096:
                target_position = 4095

            speed = int(MAX_SPEED * 0.2)
            servo.sram.write_running_speed(speed)
            servo.sram.write_acceleration(100)
            time.sleep(0.1)

            servo.sram.write_target_location(target_position)

        gui.update_status(f"Servo {servo_id}: Moving -{increment}° → {target_angle:.1f}°", "orange")

        def monitor_movement():
            time.sleep(1)
            for i in range(20):
                with comm_lock:
                    moving = servo.sram.is_moving()
                if not moving:
                    break
                time.sleep(0.2)

            with comm_lock:
                servo.sram.write_running_speed(0)

            gui.update_status(f"✓ Servo {servo_id} (Position Mode)", "green")

        threading.Thread(target=monitor_movement, daemon=True).start()

    except ValueError:
        messagebox.showerror("Error", "Enter valid number")
    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")


def increment_angle_ccw():
    increment_angle_cw()


def decrement_angle_ccw():
    decrement_angle_cw()


def debug_position():
    """Debug current servo position and status"""
    servo = get_active_servo()
    if not servo:
        messagebox.showwarning("Warning", f"Servo {active_servo_id} not connected")
        return

    servo_id = active_servo_id

    try:
        with comm_lock:
            pos = servo.sram.read_current_location()
            mode = servo.eeprom.read_operating_mode()
            target = servo.sram.read_target_location()
            temp = servo.sram.read_current_temperature()
            voltage = servo.sram.read_current_voltage()

        if pos is not None:
            angle = (pos / 4096.0) * 360.0

            debug_text = f"""Servo ID: {servo_id}
========================
Raw Position: {pos}
Angle: {angle:.2f}°
Operating Mode: {mode} (0=Position, 1=Wheel)
Target Location: {target}
Temperature: {temp}°C
Voltage: {voltage / 10 if voltage else '--'}V

Position Range: 0-4095 (4096 positions)
Angle Range: 0-360°
"""

            messagebox.showinfo(f"Servo {servo_id} Debug", debug_text)
            print(debug_text)

    except Exception as e:
        print(f"Debug error: {e}")
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


def on_knob_angle_change(angle):
    """Handle knob angle changes"""
    servo = get_active_servo()
    if not servo:
        return

    servo_id = active_servo_id

    target_position = int((angle / 360.0) * 4096.0)
    if target_position >= 4096:
        target_position = 4095

    def move_servo():
        try:
            with comm_lock:
                # Ensure we're in position mode
                if current_modes.get(servo_id) == 1:
                    servo.sram.write_running_speed(0)
                    time.sleep(0.2)
                    servo.eeprom.write_operating_mode(0)
                    time.sleep(0.3)
                    current_modes[servo_id] = 0
                    servo.sram.torque_enable()
                    time.sleep(0.2)

                # Set target in position mode
                servo.sram.write_target_location(target_position)
                servo.sram.write_running_speed(int(MAX_SPEED * 0.5))
                servo.sram.write_acceleration(50)

        except Exception as e:
            print(f"Knob error: {e}")

    threading.Thread(target=move_servo, daemon=True).start()


def on_closing():
    global running, monitoring
    running = False
    monitoring = False
    time.sleep(0.5)  # Give threads time to stop

    # Stop all servos
    for servo_id, servo in servos.items():
        if servo:
            try:
                servo.sram.write_running_speed(0)
                time.sleep(0.1)
            except:
                pass

    if controller:
        controller.close()
    root.destroy()


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
        'debug_position': debug_position,
        'switch_servo': switch_active_servo
    }


def main():
    """Main function to start the application"""
    global root, gui

    root = tk.Tk()

    # Setup callbacks
    callbacks = setup_callbacks()

    # Create GUI (modified for multi-servo)
    gui = ServoControllerGUI(root, callbacks, multi_servo=True)

    # Setup knob callback
    gui.set_knob_callback(on_knob_angle_change)

    update_speed()
    root.after(100, initialize_servos)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
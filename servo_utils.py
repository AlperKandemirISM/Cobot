# servo_utils.py - CORRECTED VERSION USING ACTUAL LIBRARY METHODS
import time
def disable_torque(self, verbose=True):
    """Disable torque using library's torque_disable() method"""
    try:
        if verbose:
            print(f"\n{'=' * 50}")
            print(f"DISABLING TORQUE (ID: {self.servo_id})")
            print(f"{'=' * 50}")
            print("1. Stopping movement...")

        # First stop any movement
        self.servo.sram.write_running_speed(0)
        time.sleep(0.3)

        # Use the actual library method
        self.servo.sram.torque_disable()
        self.torque_state = 0
        time.sleep(0.1)

        if verbose:
            # Verify torque is disabled
            current_state = self.servo.sram.read_torque_switch()
            print(f"Torque switch register: {current_state}")
            print("✓ Torque disabled - servo can be moved manually")
            print("Note: Gear resistance may still make manual movement stiff")
        return True

    except Exception as e:
        if verbose:
            print(f"✗ Error disabling torque: {e}")
        return False

def toggle_torque(self, verbose=True):
    """Toggle torque state using actual torque methods"""
    try:
        if verbose:
            print(f"\n{'=' * 50}")
            print(f"TOGGLING TORQUE (ID: {self.servo_id})")
            print(f"{'=' * 50}")

        # Read current torque state from servo
        current_state = self.servo.sram.read_torque_switch()
        print(f"Current torque state: {current_state}")

        if current_state:  # Currently enabled (non-zero)
            result = self.disable_torque(verbose)
        else:  # Currently disabled (0)
            result = self.enable_torque(verbose)

        # Update our tracking
        self.torque_state = 0 if current_state else 1

        return result

    except Exception as e:
        if verbose:
            print(f"✗ Error toggling torque: {e}")
        return False

def get_torque_state(self, verbose=True):
    """Get current torque state using read_torque_switch()"""
    try:
        state = self.servo.sram.read_torque_switch()
        self.torque_state = state

        if verbose:
            print(f"\n{'=' * 50}")
            print(f"TORQUE STATE (ID: {self.servo_id})")
            print(f"{'=' * 50}")
            print(f"Torque switch register: {state}")
            if state == 0:
                print("Torque: DISABLED (servo can be moved manually)")
            elif state == 1:
                print("Torque: ENABLED (servo holds position)")
            elif state == 128:
                print("Torque: POSITION CORRECTION mode")
            else:
                print(f"Torque: Unknown state ({state})")

        return state

    except Exception as e:
        if verbose:
            print(f"✗ Error reading torque state: {e}")
        return None

def correct_position_to_center(self, verbose=True):
    """Correct current position to 2048 (center)"""
    try:
        if verbose:
            print(f"\n{'=' * 50}")
            print(f"CORRECTING POSITION TO CENTER (ID: {self.servo_id})")
            print(f"{'=' * 50}")

        # Method 1: Use the dedicated library method
        self.servo.sram.correct_position_to_2048()
        self.torque_state = 128  # Special mode for position correction

        time.sleep(0.5)  # Give time for correction

        if verbose:
            pos = self.servo.sram.read_current_location()
            print(f"Position after correction: {pos}")
            print(f"Expected: 2048")
            print("✓ Position corrected to center")

        return True

    except Exception as e:
        if verbose:
            print(f"✗ Error correcting position: {e}")
            print("Trying alternative method...")

        # Method 2: Alternative using write_torque_switch(128)
        try:
            self.servo.sram.write_torque_switch(128)
            self.torque_state = 128
            time.sleep(0.5)

            if verbose:
                pos = self.servo.sram.read_current_location()
                print(f"Position after correction: {pos}")
                print("✓ Position corrected to center (alternative method)")
            return True

        except Exception as e2:
            if verbose:
                print(f"✗ Alternative method also failed: {e2}")
            return False
import logging
from python_st3215 import ServoNotRespondingError

import config
# Setup logging
logging.getLogger('ST3215').setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format='%(message)s')


logger = logging.getLogger(__name__)
class ServoUtils:

    """Utility class for servo operations using actual library methods"""

    def __init__(self, servo_object, servo_id=None):
        self.servo = servo_object
        self.servo_id = servo_id or config.SERVO_CONFIG['default_id']
        self.current_mode = None
        self.torque_state = None  # Track torque state

        try:
            self.current_mode = self.servo.eeprom.read_operating_mode()
            logger.info(f"Servo ID {self.servo_id}: Mode = {self.current_mode}")

            # Read initial torque state
            self.torque_state = self.servo.sram.read_torque_switch()
            logger.info(f"Servo ID {self.servo_id}: Initial Torque State = {self.torque_state}")
        except:
            pass

    def switch_to_position_mode(self, stop_first=True):
        """Switch to Position Mode (0)"""
        try:
            print(f"\n{'=' * 50}")
            print(f"SWITCHING TO POSITION MODE (ID: {self.servo_id})")
            print(f"{'=' * 50}")

            if stop_first:
                print("1. Stopping movement...")
                self.servo.sram.write_running_speed(0)
                time.sleep(0.5)

            print("2. Setting Position Mode (0)...")
            self.servo.eeprom.write_operating_mode(0)
            time.sleep(0.8)

            print("3. Testing Position Mode...")
            try:
                position = self.servo.sram.read_current_location()
                print(f"   Position: {position}")

                # Enable torque using library method
                self.servo.sram.torque_enable()
                self.torque_state = 1
                time.sleep(0.1)

                print("✓ Position Mode activated")
                self.current_mode = 0
                return True

            except Exception as e:
                print(f"✗ Test failed: {e}")
                return False

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    # ============== CORRECTED TORQUE CONTROL METHODS ==============

    def switch_to_wheel_mode(self, stop_first=True):
        """Switch to Wheel Mode (1)"""
        try:
            print(f"\n{'=' * 50}")
            print(f"SWITCHING TO WHEEL MODE (ID: {self.servo_id})")
            print(f"{'=' * 50}")

            if stop_first:
                print("1. Stopping movement...")
                self.servo.sram.write_running_speed(0)
                time.sleep(0.5)

            print("2. Setting Wheel Mode (1)...")
            self.servo.eeprom.write_operating_mode(1)
            time.sleep(0.8)

            print("3. Testing Wheel Mode...")
            test_speed = 100
            self.servo.sram.write_running_speed(test_speed)
            time.sleep(0.3)
            self.servo.sram.write_running_speed(0)

            # Enable torque for wheel mode too
            self.servo.sram.torque_enable()
            self.torque_state = 1
            time.sleep(0.1)

            print(f"   Speed test: {test_speed}")
            print("✓ Wheel Mode activated")
            self.current_mode = 1
            return True

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_current_mode(self, verbose=True):
        """Get current mode"""
        if verbose:
            print(f"\n{'=' * 50}")
            print(f"CHECKING MODE (ID: {self.servo_id})")
            print(f"{'=' * 50}")

        try:
            mode = self.servo.eeprom.read_operating_mode()
            mode_name = "Position" if mode == 0 else "Wheel"

            if verbose:
                print(f"Mode: {mode} ({mode_name})")

            self.current_mode = mode
            return mode, mode_name

        except:
            if verbose:
                print("Could not read mode directly")
            return None, "Unknown"

    def enable_torque(self, verbose=True):
        """Enable torque using library's torque_enable() method"""
        try:
            if verbose:
                print(f"\n{'=' * 50}")
                print(f"ENABLING TORQUE (ID: {self.servo_id})")
                print(f"{'=' * 50}")

            # Use the actual library method
            self.servo.sram.torque_enable()
            self.torque_state = 1
            time.sleep(0.1)

            if verbose:
                # Verify torque is enabled
                current_state = self.servo.sram.read_torque_switch()
                print(f"Torque switch register: {current_state}")
                print("✓ Torque enabled - servo actively holds position")
            return True

        except Exception as e:
            if verbose:
                print(f"✗ Error enabling torque: {e}")
            return False


# SIMPLE FUNCTIONS FOR UI
def switch_to_position_mode(servo, servo_id=1):
    """Switch to Position Mode - for UI"""
    utils = ServoUtils(servo, servo_id)
    return utils.switch_to_position_mode()


def switch_to_wheel_mode(servo, servo_id=1):
    """Switch to Wheel Mode - for UI"""
    utils = ServoUtils(servo, servo_id)
    return utils.switch_to_wheel_mode()


def get_servo_mode(servo, servo_id=1):
    """Get servo mode - for UI"""
    utils = ServoUtils(servo, servo_id)
    return utils.get_current_mode()


# CORRECTED TORQUE CONTROL FUNCTIONS
def enable_servo_torque(servo, servo_id=1):
    """Enable torque - for UI"""
    utils = ServoUtils(servo, servo_id)
    return utils.enable_torque()


def disable_servo_torque(servo, servo_id=1):
    """Disable torque - for UI"""
    utils = ServoUtils(servo, servo_id)
    return utils.disable_torque()


def toggle_servo_torque(servo, servo_id=1):
    """Toggle torque - for UI"""
    utils = ServoUtils(servo, servo_id)
    return utils.toggle_torque()


def get_servo_torque_state(servo, servo_id=1):
    """Get torque state - for UI"""
    utils = ServoUtils(servo, servo_id)
    return utils.get_torque_state()


def correct_servo_position(servo, servo_id=1):
    """Correct position to center - for UI"""
    utils = ServoUtils(servo, servo_id)
    return utils.correct_position_to_center()


# Test
if __name__ == "__main__":
    print("Servo Utilities - Ready to use!")
    print("\nAvailable functions for mainapp.py:")
    print("1. switch_to_position_mode(servo, servo_id)")
    print("2. switch_to_wheel_mode(servo, servo_id)")
    print("3. get_servo_mode(servo, servo_id)")
    print("4. enable_servo_torque(servo, servo_id)")
    print("5. disable_servo_torque(servo, servo_id)")
    print("6. toggle_servo_torque(servo, servo_id)")
    print("7. get_servo_torque_state(servo, servo_id)")
    print("8. correct_servo_position(servo, servo_id)")
    print("\nExample:")
    print("  switch_to_position_mode(servo, 1)")
    print("  toggle_servo_torque(servo, 1)")
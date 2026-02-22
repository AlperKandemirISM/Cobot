# servo_utils.py - COMPLETE UPDATED VERSION WITH IMPROVED ID CHANGE
import time
import logging
from python_st3215 import ST3215, ServoNotRespondingError
import config

# Setup logging
logging.getLogger('ST3215').setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format='%(message)s')

logger = logging.getLogger(__name__)


# ============== SERVO SCANNING FUNCTIONS ==============

def scan_for_servos(port=None, start_id=1, end_id=7, verbose=True):
    """
    Scan for servos and return list of found IDs

    Args:
        port: COM port (default from config)
        start_id: First ID to scan (default: 1)
        end_id: Last ID to scan (default: 7)
        verbose: Print detailed output

    Returns:
        List of found servo IDs
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"SERVO SCANNER - Scanning IDs {start_id} to {end_id}")
        print(f"Port: {port}")
        print(f"{'=' * 60}")

    controller = ST3215(port)
    found_servos = []

    try:
        for servo_id in range(start_id, end_id + 1):
            try:
                servo = controller.wrap_servo(servo_id)
                # Try to read position - if it works, servo exists
                pos = servo.sram.read_current_location()

                if pos is not None:
                    # Try to read more data for confirmation
                    temp = servo.sram.read_current_temperature()
                    voltage = servo.sram.read_current_voltage()

                    print(f"\n✅ SERVO FOUND at ID: {servo_id}")
                    print(f"   Position: {pos}")
                    print(f"   Temperature: {temp}°C")
                    print(f"   Voltage: {voltage / 10 if voltage else '--'}V")

                    found_servos.append(servo_id)
                else:
                    if verbose:
                        print(f"❌ ID {servo_id:2d}: No response")

            except Exception as e:
                if verbose:
                    print(f"❌ ID {servo_id:2d}: No response")

            time.sleep(0.1)  # Small delay between scans

    finally:
        controller.close()

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"Scan complete. Found {len(found_servos)} servo(s): {found_servos}")
        print(f"{'=' * 60}")

    return found_servos


def quick_id_check(port=None, ids_to_check=[1, 2, 3, 4, 5, 6, 7]):
    """
    Quick check of specific servo IDs

    Args:
        port: COM port (default from config)
        ids_to_check: List of IDs to check (default: 1-7)

    Returns:
        Dictionary of {id: status}
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    print(f"\n{'=' * 50}")
    print(f"QUICK ID CHECK - Checking IDs: {ids_to_check}")
    print(f"{'=' * 50}")

    controller = ST3215(port)
    results = {}

    try:
        for servo_id in ids_to_check:
            try:
                servo = controller.wrap_servo(servo_id)
                pos = servo.sram.read_current_location()

                if pos is not None:
                    print(f"✅ Servo ID {servo_id} → Position: {pos}")
                    results[servo_id] = {
                        'connected': True,
                        'position': pos
                    }
                else:
                    print(f"❌ Servo ID {servo_id} → No response")
                    results[servo_id] = {'connected': False}

            except Exception as e:
                print(f"❌ Servo ID {servo_id} → Connection failed")
                results[servo_id] = {'connected': False}

            time.sleep(0.1)

    finally:
        controller.close()

    return results


def continuous_scan(port=None, duration=10):
    """
    Continuously scan all possible IDs to catch intermittent connections

    Args:
        port: COM port (default from config)
        duration: How long to scan in seconds
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    print(f"\n{'=' * 60}")
    print(f"CONTINUOUS SCAN - Scanning all IDs 1-253 for {duration} seconds")
    print(f"Press Ctrl+C to stop early")
    print(f"{'=' * 60}")

    controller = ST3215(port)
    found_servos = set()
    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            for servo_id in range(1, 254):  # Full range 1-253
                try:
                    servo = controller.wrap_servo(servo_id)
                    pos = servo.sram.read_current_location()
                    if pos is not None and servo_id not in found_servos:
                        print(f"\r🎯 NEW FIND: ID {servo_id:3d} at position {pos:4d}", end="\n")
                        found_servos.add(servo_id)
                    elif pos is not None:
                        print(f"\rID {servo_id:3d} → Active (pos: {pos:4d})", end=" " * 20)
                    else:
                        print(f"\rID {servo_id:3d} → Scanning...", end=" " * 20)
                except:
                    print(f"\rID {servo_id:3d} → No response   ", end=" " * 20)

                time.sleep(0.02)  # Fast scan

            print()  # New line after each full cycle

    except KeyboardInterrupt:
        print("\n\nScan stopped by user")

    finally:
        controller.close()
        print(f"\n{'=' * 60}")
        print(f"Scan complete. Found {len(found_servos)} servo(s): {sorted(found_servos)}")
        print(f"{'=' * 60}")

    return sorted(found_servos)


def get_servo_info(servo_id, port=None):
    """
    Get detailed information about a specific servo

    Args:
        servo_id: ID of servo to query
        port: COM port (default from config)

    Returns:
        Dictionary with servo information or None if not found
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    print(f"\n{'=' * 50}")
    print(f"SERVO INFO - ID: {servo_id}")
    print(f"{'=' * 50}")

    controller = ST3215(port)

    try:
        servo = controller.wrap_servo(servo_id)

        # Read all available data
        pos = servo.sram.read_current_location()
        if pos is None:
            print(f"❌ Servo ID {servo_id} does not respond")
            return None

        speed = servo.sram.read_current_speed()
        temp = servo.sram.read_current_temperature()
        voltage = servo.sram.read_current_voltage()
        current = servo.sram.read_current_current()
        load = servo.sram.read_current_load()
        moving = servo.sram.is_moving()
        mode = servo.eeprom.read_operating_mode()
        eeprom_id = servo.eeprom.read_id()

        info = {
            'id': servo_id,
            'eeprom_id': eeprom_id,
            'position': pos,
            'angle': (pos / 4096.0) * 360.0,
            'speed': speed,
            'temperature': temp,
            'voltage': voltage / 10 if voltage else None,
            'current': current,
            'load': load,
            'moving': moving,
            'mode': mode,
            'mode_name': 'Position' if mode == 0 else 'Wheel' if mode == 1 else f'Mode {mode}'
        }

        # Print formatted info
        print(f"✅ Servo ID {servo_id} connected successfully")
        print(f"\n📊 TELEMETRY:")
        print(f"   EEPROM ID: {eeprom_id}")
        print(f"   Position: {pos} ({info['angle']:.1f}°)")
        print(f"   Speed: {speed}")
        print(f"   Temperature: {temp}°C")
        print(f"   Voltage: {info['voltage']:.1f}V")
        print(f"   Current: {current}mA")
        print(f"   Load: {load}%")
        print(f"   Moving: {'YES' if moving else 'NO'}")
        print(f"   Operating Mode: {mode} ({info['mode_name']})")

        if eeprom_id != servo_id:
            print(f"\n⚠️  WARNING: EEPROM ID ({eeprom_id}) doesn't match current ID ({servo_id})")
            print("   The ID may revert after power cycle")

        return info

    except Exception as e:
        print(f"❌ Error reading servo {servo_id}: {e}")
        return None

    finally:
        controller.close()


# ============== IMPROVED ID CHANGE FUNCTIONS ==============

# Add this function to your servo_utils.py

def change_servo_id_correct(old_id, new_id, port=None):
    """
    Change a servo's ID using the correct library procedure:
    1. Unlock EEPROM (write 0 to STS_LOCK)
    2. Write new ID to STS_ID
    3. Lock EEPROM (write 1 to STS_LOCK)

    Args:
        old_id: Current servo ID
        new_id: New servo ID (1-253)
        port: COM port (default from config)

    Returns:
        True if successful, False otherwise
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    if new_id < 1 or new_id > 253:
        print("❌ New ID must be between 1 and 253")
        return False

    print(f"\n{'=' * 60}")
    print(f"CHANGE SERVO ID: {old_id} → {new_id}")
    print(f"{'=' * 60}")
    print("⚠️  WARNING: This changes the servo's permanent ID!\n")

    confirm = input(f"Change servo ID from {old_id} to {new_id}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled")
        return False

    from python_st3215 import ST3215
    from python_st3215.values import STS_ID, STS_LOCK, COMM_SUCCESS

    controller = ST3215(port)

    try:
        # Step 1: Verify servo exists
        if not controller.PingServo(old_id):
            print(f"❌ Could not find servo with ID {old_id}")
            return False

        print(f"✓ Found servo at ID {old_id}")

        # Read current position for verification
        pos = controller.ReadPosition(old_id)
        print(f"Current position: {pos}")

        # Step 2: Unlock EEPROM
        print("\n🔓 Unlocking EEPROM...")
        unlock_result = controller.write1ByteTxOnly(old_id, STS_LOCK, 0)
        if unlock_result != COMM_SUCCESS:
            print(f"❌ Failed to unlock EEPROM")
            return False
        print("✓ EEPROM unlocked")
        time.sleep(0.1)

        # Step 3: Write new ID
        print(f"\n📝 Writing new ID {new_id} to EEPROM...")
        write_result = controller.write1ByteTxOnly(old_id, STS_ID, new_id)
        if write_result != COMM_SUCCESS:
            print(f"❌ Failed to write new ID")
            # Try to lock anyway
            controller.write1ByteTxOnly(old_id, STS_LOCK, 1)
            return False
        print("✓ New ID written")
        time.sleep(0.2)

        # Step 4: Lock EEPROM
        print("\n🔒 Locking EEPROM...")
        lock_result = controller.write1ByteTxOnly(old_id, STS_LOCK, 1)
        if lock_result != COMM_SUCCESS:
            print(f"⚠ Warning: Failed to lock EEPROM")
        else:
            print("✓ EEPROM locked")

        time.sleep(0.5)

        # Step 5: Verify with new ID
        print(f"\n🔍 Verifying new ID {new_id}...")

        if controller.PingServo(new_id):
            new_pos = controller.ReadPosition(new_id)
            print(f"✅ SUCCESS! Servo now responds at ID {new_id}")
            print(f"   Position: {new_pos}")
            return True
        else:
            print(f"❌ Cannot communicate with new ID {new_id}")
            print("   Checking if still responds at old ID...")
            if controller.PingServo(old_id):
                print("   Servo still responds at old ID - change failed")
            else:
                print("   Servo not responding - may need power cycle")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    finally:
        controller.close()


def test_eeprom_write(servo_id, port=None):
    """
    Test if EEPROM writing works by trying to change a safe value
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    print(f"\n{'=' * 60}")
    print(f"EEPROM WRITE TEST - Servo ID: {servo_id}")
    print(f"{'=' * 60}")

    controller = ST3215(port)

    try:
        # Step 1: Check servo
        if not controller.PingServo(servo_id):
            print(f"❌ Could not find servo with ID {servo_id}")
            return False

        # Step 2: Read current baudrate (safe value to test)
        current_baud, comm, error = controller.read1ByteTxRx(servo_id, STS_BAUD_RATE)
        if comm != COMM_SUCCESS:
            print(f"❌ Failed to read current baudrate")
            return False
        print(f"📊 Current baudrate value: {current_baud}")

        # Step 3: Try to write a different value and read back
        test_value = 3  # Different baudrate value
        print(f"\n📝 Testing EEPROM write with baudrate {test_value}...")

        # Unlock EEPROM
        print("🔓 Unlocking EEPROM...")
        unlock_result = controller.write1ByteTxOnly(servo_id, STS_LOCK, 0)
        if unlock_result != COMM_SUCCESS:
            print(f"❌ Failed to unlock EEPROM")
            return False

        time.sleep(0.1)

        # Write test value
        write_result = controller.write1ByteTxOnly(servo_id, STS_BAUD_RATE, test_value)
        if write_result != COMM_SUCCESS:
            print(f"❌ Failed to write test value")
            controller.write1ByteTxOnly(servo_id, STS_LOCK, 1)
            return False

        time.sleep(0.3)

        # Read back
        read_back, comm, error = controller.read1ByteTxRx(servo_id, STS_BAUD_RATE)

        # Lock EEPROM
        print("🔒 Locking EEPROM...")
        controller.write1ByteTxOnly(servo_id, STS_LOCK, 1)

        if comm == COMM_SUCCESS and read_back == test_value:
            print(f"✅ Write successful! Read back: {read_back}")

            # Restore original value
            print(f"\n🔄 Restoring original baudrate {current_baud}...")
            controller.write1ByteTxOnly(servo_id, STS_LOCK, 0)
            time.sleep(0.1)
            controller.write1ByteTxOnly(servo_id, STS_BAUD_RATE, current_baud)
            time.sleep(0.3)
            controller.write1ByteTxOnly(servo_id, STS_LOCK, 1)
            print("✓ Original value restored")

            return True
        else:
            print(f"❌ Write verification failed. Read back: {read_back}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    finally:
        controller.close()

def force_change_servo_id(old_id, new_id, port=None):
    """
    More aggressive method to change servo ID with multiple verification steps
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    print(f"\n{'=' * 60}")
    print(f"FORCE CHANGE SERVO ID: {old_id} → {new_id}")
    print(f"{'=' * 60}")

    controller = ST3215(port)

    try:
        # Step 1: Connect with old ID
        servo = controller.wrap_servo(old_id)

        # Read current data
        pos = servo.sram.read_current_location()
        if pos is None:
            print(f"❌ Cannot connect to servo at ID {old_id}")
            return False

        print(f"✓ Connected to servo at ID {old_id}")
        print(f"  Current position: {pos}")
        print(f"  Temperature: {servo.sram.read_current_temperature()}°C")

        # Step 2: Disable torque for safety
        print("\n🔧 Disabling torque...")
        servo.sram.torque_disable()
        time.sleep(0.3)

        # Step 3: Write to EEPROM with verification
        print(f"\n📝 Writing ID {new_id} to EEPROM...")

        # Write multiple times to ensure it sticks
        for attempt in range(3):
            print(f"  Attempt {attempt + 1}/3...")
            servo.eeprom.write_id(new_id)
            time.sleep(0.5)

            # Read back
            read_id = servo.eeprom.read_id()
            print(f"    Read back: {read_id}")

            if read_id == new_id:
                print(f"  ✅ Write confirmed on attempt {attempt + 1}")
                break
        else:
            print("❌ Failed to write ID after 3 attempts")
            return False

        # Step 4: Try to communicate with new ID
        print(f"\n🔍 Testing new ID {new_id}...")
        time.sleep(1)  # Give servo time to reset

        try:
            # Create new connection with new ID
            new_servo = controller.wrap_servo(new_id)
            new_pos = new_servo.sram.read_current_location()

            if new_pos is not None:
                print(f"✅ Success! Servo now responds at ID {new_id}")
                print(f"   Position: {new_pos}")

                # Re-enable torque
                new_servo.sram.torque_enable()

                print(f"\n{'=' * 60}")
                print(f"✅ ID CHANGE COMPLETE!")
                print(f"   Old ID: {old_id} → New ID: {new_id}")
                print(f"{'=' * 60}")
                return True
            else:
                print(f"❌ Cannot read from new ID {new_id}")
                return False

        except Exception as e:
            print(f"❌ Cannot connect to new ID {new_id}")
            print("   The servo may need a power cycle")

            # Offer to try power cycle detection
            print("\n🔄 After power cycling the servo, run:")
            print(f"   from servo_utils import scan_for_servos")
            print(f"   scan_for_servos()  # Should show ID {new_id}")
            return False

    finally:
        controller.close()


def verify_servo_id(servo_id, port=None):
    """
    Verify a servo exists at given ID and check if ID is saved in EEPROM
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    controller = ST3215(port)

    try:
        servo = controller.wrap_servo(servo_id)

        # Try to read from SRAM (volatile memory)
        pos = servo.sram.read_current_location()
        if pos is None:
            print(f"❌ No servo responding at ID {servo_id}")
            return False

        # Read from EEPROM (permanent memory)
        eeprom_id = servo.eeprom.read_id()

        print(f"\n{'=' * 50}")
        print(f"SERVO ID VERIFICATION - ID: {servo_id}")
        print(f"{'=' * 50}")
        print(f"✅ Servo responds at ID {servo_id}")
        print(f"📝 EEPROM stored ID: {eeprom_id}")
        print(f"Position: {pos}")
        print(f"Temperature: {servo.sram.read_current_temperature()}°C")

        if eeprom_id == servo_id:
            print(f"\n✓ ID is correctly saved in EEPROM")
            return True
        else:
            print(f"\n⚠️  WARNING: EEPROM ID ({eeprom_id}) doesn't match current ID ({servo_id})")
            print("   The ID may revert after power cycle")
            return False

    except Exception as e:
        print(f"❌ Error verifying ID {servo_id}: {e}")
        return False

    finally:
        controller.close()


def batch_change_servo_ids(id_mappings, port=None):
    """
    Change multiple servo IDs in sequence

    Args:
        id_mappings: List of tuples [(old_id, new_id), ...]
        port: COM port (default from config)

    Returns:
        Dictionary with results for each change
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    print(f"\n{'=' * 60}")
    print(f"BATCH ID CHANGE - {len(id_mappings)} servos")
    print(f"{'=' * 60}")

    results = {}

    for i, (old_id, new_id) in enumerate(id_mappings):
        print(f"\n--- Servo {i + 1}/{len(id_mappings)}: {old_id} → {new_id} ---")
        success = change_servo_id(old_id, new_id, port, verify=True)
        results[(old_id, new_id)] = success
        time.sleep(1)  # Wait between changes

    print(f"\n{'=' * 60}")
    print("BATCH ID CHANGE RESULTS")
    print(f"{'=' * 60}")
    for (old, new), success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} ID {old} → {new}")

    return results


# ============== EXISTING SERVO UTILITIES ==============

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

    def disable_torque(self, verbose=True):
        """Disable torque"""
        return disable_torque(self, verbose)

    def toggle_torque(self, verbose=True):
        """Toggle torque"""
        return toggle_torque(self, verbose)

    def get_torque_state(self, verbose=True):
        """Get torque state"""
        return get_torque_state(self, verbose)

    def correct_position_to_center(self, verbose=True):
        """Correct position to center"""
        return correct_position_to_center(self, verbose)


# ============== SIMPLE FUNCTIONS FOR UI ==============

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


def get_servo_info(servo_id, port=None):
    """
    Get detailed information about a specific servo

    Args:
        servo_id: ID of servo to query
        port: COM port (default from config)

    Returns:
        Dictionary with servo information or None if not found
    """
    if port is None:
        port = config.SERIAL_CONFIG['port']

    print(f"\n{'=' * 50}")
    print(f"SERVO INFO - ID: {servo_id}")
    print(f"{'=' * 50}")

    controller = ST3215(port)

    try:
        servo = controller.wrap_servo(servo_id)

        # Read all available data
        pos = servo.sram.read_current_location()
        if pos is None:
            print(f"❌ Servo ID {servo_id} does not respond")
            return None

        speed = servo.sram.read_current_speed()
        temp = servo.sram.read_current_temperature()
        voltage = servo.sram.read_current_voltage()
        current = servo.sram.read_current_current()
        load = servo.sram.read_current_load()
        moving = servo.sram.is_moving()
        mode = servo.eeprom.read_operating_mode()
        eeprom_id = servo.eeprom.read_id()  # Read the EEPROM stored ID

        info = {
            'id': servo_id,
            'eeprom_id': eeprom_id,  # Add this to the dictionary
            'position': pos,
            'angle': (pos / 4096.0) * 360.0,
            'speed': speed,
            'temperature': temp,
            'voltage': voltage / 10 if voltage else None,
            'current': current,
            'load': load,
            'moving': moving,
            'mode': mode,
            'mode_name': 'Position' if mode == 0 else 'Wheel' if mode == 1 else f'Mode {mode}'
        }

        # Print formatted info including EEPROM ID
        print(f"✅ Servo ID {servo_id} connected successfully")
        print(f"\n📊 TELEMETRY:")
        print(f"   📝 EEPROM ID: {eeprom_id}")  # Show the EEPROM ID
        print(f"   Position: {pos} ({info['angle']:.1f}°)")
        print(f"   Speed: {speed}")
        print(f"   Temperature: {temp}°C")
        print(f"   Voltage: {info['voltage']:.1f}V")
        print(f"   Current: {current}mA")
        print(f"   Load: {load}%")
        print(f"   Moving: {'YES' if moving else 'NO'}")
        print(f"   Operating Mode: {mode} ({info['mode_name']})")

        # Add warning if IDs don't match
        if eeprom_id != servo_id:
            print(f"\n⚠️  WARNING: EEPROM ID ({eeprom_id}) doesn't match current ID ({servo_id})")
            print("   The ID may revert after power cycle")

        return info

    except Exception as e:
        print(f"❌ Error reading servo {servo_id}: {e}")
        return None

    finally:
        controller.close()


def correct_servo_position(servo, servo_id=1):
    """Correct position to center - for UI"""
    utils = ServoUtils(servo, servo_id)
    return utils.correct_position_to_center()


# ============== TEST / MAIN ==============

if __name__ == "__main__":
    print("Servo Utilities - Testing Mode")
    print("=" * 60)
    print("\nAvailable functions:")
    print("1. scan_for_servos() - Scan for servos")
    print("2. quick_id_check() - Quick check of IDs 1-7")
    print("3. continuous_scan() - Continuous scanning")
    print("4. get_servo_info(id) - Get detailed servo info")
    print("5. change_servo_id(old, new) - Change servo ID")
    print("6. force_change_servo_id(old, new) - Force change ID")
    print("7. verify_servo_id(id) - Verify ID is saved in EEPROM")
    print("8. batch_change_servo_ids([(1,2), (3,4)]) - Change multiple IDs")
    print("\nExample usage:")
    print("  from servo_utils import scan_for_servos")
    print("  found = scan_for_servos()")
    print("  info = get_servo_info(1)")

    # Quick demo - scan for servos
    print("\n" + "=" * 60)
    print("QUICK SCAN DEMO")
    print("=" * 60)

    # Use config for port
    port = config.SERIAL_CONFIG['port']
    print(f"Using port: {port}")

    # Quick scan of IDs 1-7
    quick_id_check(port, ids_to_check=[1, 2, 3, 4, 5, 6, 7])
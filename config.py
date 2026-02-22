# config.py - Configuration for ST3215 Servo Control
import os
from pathlib import Path
from datetime import datetime

# ========== PROJECT PATHS ==========
PROJECT_ROOT = Path(__file__).parent
LOG_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"

# Create directories if they don't exist
for directory in [LOG_DIR, DATA_DIR]:
    directory.mkdir(exist_ok=True)

# ========== SERIAL CONFIGURATION ==========
SERIAL_CONFIG = {
    'port': 'COM4',           # Change this to your COM port
    'baud_rate': 115200,      # From ST3215 manual
    'timeout': 1.0,           # Serial timeout in seconds
    'bytesize': 8,            # 8 data bits
    'parity': 'N',            # No parity
    'stopbits': 1,            # 1 stop bit
}

# ========== SERVO CONFIGURATION ==========
SERVO_CONFIG = {
    'default_id': 1,          # Default servo ID
    'servo_type': 'ST',       # 'ST' or 'SC' (from manual)
    'max_id': 253,            # Maximum servo ID (from manual)
}

# ========== SERVO PARAMETERS (from manual page 19) ==========
SERVO_PARAMS = {
    'ST': {
        'name': 'ST Series',
        'digital_range': 4095,      # 0-4095 positions
        'angle_range': 360.0,       # 360° rotation
        'max_speed': 32766,         # Maximum speed
        'middle_position': 2048,    # Middle position (180°)
        'max_speed_rpm': 53,        # Maximum RPM
        'voltage_range': (6.0, 12.0),  # Voltage range
    },
    'SC': {
        'name': 'SC Series',
        'digital_range': 1023,      # 0-1023 positions
        'angle_range': 210.0,       # 200° rotation (210 in code)
        'max_speed': 1500,          # Maximum speed
        'middle_position': 511,     # Middle position
        'max_speed_rpm': 62,        # Maximum RPM
        'voltage_range': (6.0, 8.4),  # Voltage range
    }
}

# Get current servo parameters
def get_servo_params():
    """Get parameters for current servo type"""
    servo_type = SERVO_CONFIG['servo_type']
    return SERVO_PARAMS.get(servo_type, SERVO_PARAMS['ST'])

# ========== GUI CONFIGURATION ==========
GUI_CONFIG = {
    'window_title': "ST3215 Servo Controller",
    'window_size': "1400x700",
    'refresh_rate': 100,      # GUI refresh rate in ms
    'theme': {
        'bg_color': '#f0f0f0',
        'fg_color': '#333333',
        'button_bg': '#e0e0e0',
        'button_fg': '#000000',
        'accent_cw': '#4169e1',     # Clockwise color
        'accent_ccw': '#ff8c00',    # Counter-clockwise color
        'danger': '#dc143c',        # Stop button
        'success': '#228B22',
        'warning': '#FFD700',
        'error': '#DC143C',
    },
    'update_interval': 200,   # Telemetry update interval in ms
}

# ========== LOGGING CONFIGURATION ==========
LOGGING_CONFIG = {
    'enabled': True,
    'log_level': 'INFO',      # DEBUG, INFO, WARNING, ERROR
    'log_to_file': True,
    'log_to_console': True,
    'max_file_size_mb': 10,   # Maximum log file size
    'backup_count': 5,        # Number of backup files
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
}

# ========== MOVEMENT LIMITS ==========
MOVEMENT_LIMITS = {
    'min_speed_percent': 10,
    'max_speed_percent': 100,
    'default_speed_percent': 30,
    'min_angle': 0,
    'max_angle': 360,
    'default_increment': 10,  # Default angle increment
}

# ========== SAFETY SETTINGS ==========
SAFETY_SETTINGS = {
    'max_temperature': 85,    # °C - Maximum allowed temperature
    'min_voltage': 5.5,       # V - Minimum voltage warning
    'max_current': 2000,      # mA - Maximum current warning
    'emergency_stop_timeout': 5.0,  # seconds
}

# ========== CALIBRATION SETTINGS ==========
CALIBRATION = {
    'auto_calibrate_on_start': False,
    'default_zero_position': 2048,  # For ST series
    'tolerance': 20,          # Position tolerance in steps
}

# ========== ESP-NOW SETTINGS (from manual) ==========
ESPNOW_CONFIG = {
    'enabled': False,
    'default_role': 0,        # 0=Normal, 1=Leader, 2=Follower
    'channel': 1,
    'encryption': False,
}

# ========== WIFI SETTINGS (from manual page 21) ==========
WIFI_CONFIG = {
    'default_mode': 'AP',     # 'AP' or 'STA'
    'ap_ssid': 'ESP32_DEV',
    'ap_password': '12345678',
    'sta_ssid': '',
    'sta_password': '',
}

# ========== EXPORT SETTINGS ==========
def export_settings():
    """Export all settings as a dictionary (for debugging)"""
    return {
        'serial': SERIAL_CONFIG,
        'servo': SERVO_CONFIG,
        'gui': GUI_CONFIG,
        'logging': LOGGING_CONFIG,
        'movement': MOVEMENT_LIMITS,
        'safety': SAFETY_SETTINGS,
    }

# ========== VERSION INFO ==========
VERSION = {
    'major': 1,
    'minor': 0,
    'patch': 0,
    'release_date': '2026-02-08',
}

def get_version_string():
    """Get version as string"""
    return f"{VERSION['major']}.{VERSION['minor']}.{VERSION['patch']}"

# Print config info when imported
if __name__ == "__main__":
    print(f"ST3215 Servo Control Configuration v{get_version_string()}")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Servo type: {SERVO_CONFIG['servo_type']}")
    print(f"COM port: {SERIAL_CONFIG['port']}")
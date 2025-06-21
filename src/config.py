"""
Configuration management for IoT Smart Thermometer
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # MQTT Configuration
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'test.mosquitto.org')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
    MQTT_TOPIC_TEMPERATURE = 'smart_thermometer/temperature'
    MQTT_TOPIC_PRESSURE = 'smart_thermometer/pressure'
    MQTT_TOPIC_ALARMS = 'smart_thermometer/alarms'
    MQTT_TOPIC_CONFIG = 'smart_thermometer/config'
    
    # Web Interface Configuration
    WEB_HOST = os.getenv('WEB_HOST', 'localhost')
    WEB_PORT = int(os.getenv('WEB_PORT', 5000))
    WEB_DEBUG = os.getenv('WEB_DEBUG', 'False').lower() == 'true'
    
    # Mobile App Configuration
    MOBILE_HOST = os.getenv('MOBILE_HOST', 'localhost')
    MOBILE_PORT = int(os.getenv('MOBILE_PORT', 5001))
    
    # Sensor Simulation Configuration
    TEMP_MIN = float(os.getenv('TEMP_MIN', 10.0))  # Celsius
    TEMP_MAX = float(os.getenv('TEMP_MAX', 120.0))  # Celsius
    PRESSURE_MIN = float(os.getenv('PRESSURE_MIN', 0.5))  # atm
    PRESSURE_MAX = float(os.getenv('PRESSURE_MAX', 1.5))  # atm
    
    # Physical Constants
    WATER_BOILING_POINT_1ATM = 100.0  # Celsius at 1 atm
    
    # Alarm Configuration
    DEFAULT_ALARM_TEMPERATURE = 100.0  # Celsius
    DEFAULT_ALARM_TIME = 600  # 10 minutes in seconds
    
    # Blynk Configuration (if using Blynk)
    BLYNK_AUTH_TOKEN = os.getenv('BLYNK_AUTH_TOKEN', '')
    
    # Data Update Intervals (seconds)
    SENSOR_UPDATE_INTERVAL = 2
    MQTT_PUBLISH_INTERVAL = 3
    WEB_UPDATE_INTERVAL = 1

# Water boiling point calculation based on pressure
def calculate_boiling_point(pressure_atm):
    """
    Calculate water boiling point based on atmospheric pressure
    Using Antoine equation approximation for water
    """
    if pressure_atm <= 0:
        return 0
    
    # Simplified calculation for educational purposes
    # Real formula would be more complex
    base_temp = 100.0  # °C at 1 atm
    pressure_factor = 25.0  # Temperature change per atm
    
    return base_temp + pressure_factor * (pressure_atm - 1.0)

# Device identification
DEVICE_ID = os.getenv('DEVICE_ID', 'smart_thermometer_001')
DEVICE_NAME = os.getenv('DEVICE_NAME', 'Smart Food Thermometer')
DEVICE_LOCATION = os.getenv('DEVICE_LOCATION', 'Kitchen')

"""
IoT Smart Thermometer Package
A comprehensive IoT solution for food temperature monitoring
"""

__version__ = "1.0.0"
__author__ = "Smart Thermometer Team"
__description__ = "IoT Smart Thermometer for Food Monitoring"

# Package imports
from .config import Config, DEVICE_ID, DEVICE_NAME
from .simple_temperature_sensor_precision import PrecisionTemperatureSensor
from .pressure_sensor import PressureSensor
from .mqtt_client import MQTTClient
from .smart_alarm_manager import SmartAlarmManager

__all__ = [
    'Config',
    'DEVICE_ID', 
    'DEVICE_NAME',
    'PrecisionTemperatureSensor',
    'PressureSensor', 
    'MQTTClient',
    'SmartAlarmManager'
]

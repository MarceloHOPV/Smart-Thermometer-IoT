"""
IoT Smart Thermometer Package
A comprehensive IoT solution for food temperature monitoring
"""

__version__ = "1.0.0"
__author__ = "Smart Thermometer Team"
__description__ = "IoT Smart Thermometer for Food Monitoring"

# Package imports
from .config import Config, DEVICE_ID, DEVICE_NAME
from .temperature_sensor import TemperatureSensor
from .pressure_sensor import PressureSensor
from .mqtt_client import MQTTClient
from .alarm_manager import AlarmManager, AlarmType, AlarmPriority

__all__ = [
    'Config',
    'DEVICE_ID', 
    'DEVICE_NAME',
    'TemperatureSensor',
    'PressureSensor', 
    'MQTTClient',
    'AlarmManager',
    'AlarmType',
    'AlarmPriority'
]

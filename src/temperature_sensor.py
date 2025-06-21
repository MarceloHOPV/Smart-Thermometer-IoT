"""
Temperature Sensor Simulation Module
Simulates realistic temperature readings for food/water monitoring
"""
import random
import time
import numpy as np
from datetime import datetime
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemperatureSensor:
    def __init__(self, device_id="temp_sensor_001"):
        self.device_id = device_id
        self.current_temperature = 22.0  # Start at room temperature
        self.target_temperature = 100.0  # Default boiling target
        self.heating_rate = 1.2  # degrees per reading when heating
        self.cooling_rate = 0.3  # degrees per reading when cooling
        self.noise_level = 0.1  # Small temperature noise
        self.is_heating = False
        self.is_active = True
        self.system_running = False
        self.last_reading_time = time.time()
        
        # Failure simulation
        self.failure_probability = 0.001  # 0.1% chance of failure per reading
        self.is_failed = False
        
        logger.info(f"Temperature sensor {device_id} initialized")
    
    def start_system(self):
        """Start heating simulation"""
        self.system_running = True
        self.is_heating = True
        logger.info("Temperature sensor system started - heating enabled")
    
    def stop_system(self):
        """Stop heating simulation"""
        self.system_running = False
        self.is_heating = False
        logger.info("Temperature sensor system stopped - heating disabled")
    
    def set_heating(self, heating_state):
        """Control heating element simulation"""
        if self.system_running:
            self.is_heating = heating_state
            logger.info(f"Heating set to: {heating_state}")
    
    def set_target_temperature(self, target_temp):
        """Set target temperature for automatic heating control"""
        self.target_temperature = max(20.0, min(120.0, target_temp))
        logger.info(f"Target temperature set to: {self.target_temperature}°C")
    def simulate_realistic_heating(self, boiling_point=100.0):
        """
        Simulate realistic water heating with stable progression
        """
        if self.is_heating and self.system_running:
            # Gradual heating towards boiling point
            temp_diff = boiling_point - self.current_temperature
            
            if temp_diff > 0.5:
                # Consistent heating rate based on distance from target
                heating_factor = min(1.0, temp_diff / 50.0)  # Normalize heating rate
                increment = self.heating_rate * heating_factor
                self.current_temperature += increment
                
                # Ensure we don't overshoot too much
                if self.current_temperature > boiling_point:
                    self.current_temperature = boiling_point + random.uniform(-0.3, 0.3)
            else:
                # At target temperature - maintain with small fluctuation
                self.current_temperature = boiling_point + random.uniform(-0.5, 0.5)
                
        elif not self.is_heating or not self.system_running:
            # Gradual cooling towards room temperature
            room_temp = 22.0
            if self.current_temperature > room_temp:
                temp_diff = self.current_temperature - room_temp
                cooling_factor = max(0.1, temp_diff / 50.0)
                self.current_temperature -= self.cooling_rate * cooling_factor
                
                # Don't go below room temperature
                if self.current_temperature < room_temp:
                    self.current_temperature = room_temp
    
    def get_temperature(self, pressure_atm=1.0):
        """
        Get current temperature reading with realistic simulation
        """
        if not self.is_active:
            return None
        
        # Debug: Log current state
        logger.info(f"get_temperature called - current_temp: {self.current_temperature:.1f}°C, is_heating: {self.is_heating}, system_running: {self.system_running}")
        
        # Simulate sensor failure
        if random.random() < self.failure_probability:
            self.is_failed = True
            logger.warning(f"Sensor {self.device_id} failure simulated")
            return None
        
        if self.is_failed:
            # Random chance to recover from failure
            if random.random() < 0.1:  # 10% chance to recover
                self.is_failed = False
                logger.info(f"Sensor {self.device_id} recovered from failure")
            else:
                return None
          # Update simulation
        # Calculate boiling point based on pressure
        boiling_point = 100.0 - (1.0 - pressure_atm) * 10.0  # Rough approximation
        self.simulate_realistic_heating(boiling_point)
        
        # Add realistic noise
        noise = random.gauss(0, self.noise_level)
        measured_temp = self.current_temperature + noise
        
        # Ensure temperature is within realistic bounds
        measured_temp = max(Config.TEMP_MIN, min(Config.TEMP_MAX, measured_temp))
        
        return round(measured_temp, 2)
    
    def get_sensor_data(self, pressure_atm=1.0):
        """
        Get complete sensor data package
        """
        temperature = self.get_temperature(pressure_atm)
        
        return {
            'device_id': self.device_id,
            'timestamp': datetime.now().isoformat(),
            'temperature': temperature,
            'temperature_unit': 'celsius',
            'is_heating': self.is_heating,
            'target_temperature': self.target_temperature,
            'sensor_status': 'failed' if self.is_failed else 'active',
            'pressure_atm': pressure_atm
        }
    
    def calibrate(self, known_temp):
        """
        Calibrate sensor against known temperature
        """
        if self.current_temperature > 0:
            calibration_offset = known_temp - self.current_temperature
            self.current_temperature += calibration_offset
            logger.info(f"Sensor {self.device_id} calibrated with offset: {calibration_offset:.2f}°C")
    
    def reset_sensor(self):
        """Reset sensor to initial state"""
        self.current_temperature = 20.0
        self.target_temperature = 20.0
        self.is_heating = False
        self.is_failed = False
        logger.info(f"Sensor {self.device_id} reset to initial state")

# Example usage and testing
if __name__ == "__main__":
    sensor = TemperatureSensor("test_sensor")
    
    print("Starting temperature sensor simulation...")
    sensor.start_system()  # Start the system first
    sensor.set_heating(True)
    sensor.set_target_temperature(100.0)
    
    for i in range(20):
        data = sensor.get_sensor_data()
        print(f"Reading {i+1}: Temperature={data['temperature']}°C, Heating={data['is_heating']}")
        time.sleep(1)

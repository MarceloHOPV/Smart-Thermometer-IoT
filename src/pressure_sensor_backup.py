"""
Pressure Sensor Simulation Module
Simulates atmospheric pressure readings for different altitudes
"""
import random
import time
import numpy as np
from datetime import datetime
import logging
from .config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PressureSensor:
    def __init__(self, device_id="pressure_sensor_001"):
        self.device_id = device_id
        self.current_pressure = 1.0  # Start at sea level (1 atm)
        self.altitude_meters = 0.0  # Sea level
        self.noise_level = 0.005  # pressure noise in atm
        self.is_active = True
        self.last_reading_time = time.time()
        
        # Failure simulation
        self.failure_probability = 0.0005  # 0.05% chance of failure per reading
        self.is_failed = False
        
        # Pressure variation simulation (weather effects)
        self.base_pressure = 1.0
        self.pressure_trend = 0.0  # Trending up or down
        
        logger.info(f"Pressure sensor {device_id} initialized")
    
    def set_altitude(self, altitude_meters):
        """
        Set altitude and calculate corresponding atmospheric pressure
        Using barometric formula: P = P0 * (1 - 0.0065*h/T0)^(g*M/R*0.0065)
        Simplified version for educational purposes
        """
        self.altitude_meters = altitude_meters
        
        # Simplified pressure calculation based on altitude
        # Real formula would be more complex
        if altitude_meters <= 0:
            self.base_pressure = 1.0  # Sea level
        else:
            # Pressure decreases approximately 0.12 atm per 1000m
            pressure_drop = altitude_meters * 0.00012
            self.base_pressure = max(0.3, 1.0 - pressure_drop)
        
        logger.info(f"Altitude set to {altitude_meters}m, base pressure: {self.base_pressure:.3f} atm")
    
    def set_weather_conditions(self, weather_type="normal"):
        """
        Simulate different weather conditions affecting pressure
        """
        weather_effects = {
            "normal": 0.0,
            "high_pressure": 0.03,  # High pressure system
            "low_pressure": -0.03,  # Low pressure system
            "storm": -0.05,         # Storm conditions
            "clear": 0.02           # Clear, stable conditions
        }
        
        self.pressure_trend = weather_effects.get(weather_type, 0.0)
        logger.info(f"Weather conditions set to: {weather_type}")
    
    def simulate_pressure_variations(self):
        """
        Simulate natural pressure variations over time
        """
        current_time = time.time()
        time_delta = current_time - self.last_reading_time
        self.last_reading_time = current_time
        
        # Small random variations (weather micro-changes)
        random_variation = random.gauss(0, 0.001) * time_delta
        
        # Gradual trend changes
        trend_change = self.pressure_trend * 0.001 * time_delta
        
        # Update current pressure
        self.current_pressure = self.base_pressure + trend_change + random_variation
        
        # Ensure pressure stays within realistic bounds
        self.current_pressure = max(Config.PRESSURE_MIN, 
                                  min(Config.PRESSURE_MAX, self.current_pressure))
    
    def get_pressure(self):
        """
        Get current pressure reading with realistic simulation
        """
        if not self.is_active:
            return None
        
        # Simulate sensor failure
        if random.random() < self.failure_probability:
            self.is_failed = True
            logger.warning(f"Pressure sensor {self.device_id} failure simulated")
            return None
        
        if self.is_failed:
            # Random chance to recover from failure
            if random.random() < 0.05:  # 5% chance to recover
                self.is_failed = False
                logger.info(f"Pressure sensor {self.device_id} recovered from failure")
            else:
                return None
        
        # Update simulation
        self.simulate_pressure_variations()
        
        # Add realistic noise
        noise = random.gauss(0, self.noise_level)
        measured_pressure = self.current_pressure + noise
        
        # Ensure pressure is within realistic bounds
        measured_pressure = max(Config.PRESSURE_MIN, 
                              min(Config.PRESSURE_MAX, measured_pressure))
        
        return round(measured_pressure, 4)
    
    def get_sensor_data(self):
        """
        Get complete pressure sensor data package
        """
        pressure = self.get_pressure()
        
        # Calculate equivalent altitude based on current pressure
        if pressure and pressure > 0.3:
            estimated_altitude = (1.0 - pressure) / 0.00012
        else:
            estimated_altitude = None
        
        return {
            'device_id': self.device_id,
            'timestamp': datetime.now().isoformat(),
            'pressure': pressure,
            'pressure_unit': 'atm',
            'altitude_meters': self.altitude_meters,
            'estimated_altitude': round(estimated_altitude, 1) if estimated_altitude else None,
            'sensor_status': 'failed' if self.is_failed else 'active',
            'weather_trend': self.pressure_trend
        }
    
    def calibrate(self, known_pressure):
        """
        Calibrate sensor against known pressure reading
        """
        if self.current_pressure > 0:
            calibration_offset = known_pressure - self.current_pressure
            self.current_pressure += calibration_offset
            self.base_pressure += calibration_offset
            logger.info(f"Pressure sensor {self.device_id} calibrated with offset: {calibration_offset:.4f} atm")
    
    def reset_sensor(self):
        """Reset sensor to initial state"""
        self.current_pressure = 1.0
        self.altitude_meters = 0.0
        self.base_pressure = 1.0
        self.pressure_trend = 0.0
        self.is_failed = False
        logger.info(f"Pressure sensor {self.device_id} reset to initial state")

# Utility functions for pressure calculations
def altitude_to_pressure(altitude_meters):
    """Convert altitude to atmospheric pressure"""
    if altitude_meters <= 0:
        return 1.0
    pressure_drop = altitude_meters * 0.00012
    return max(0.3, 1.0 - pressure_drop)

def pressure_to_altitude(pressure_atm):
    """Convert atmospheric pressure to estimated altitude"""
    if pressure_atm >= 1.0:
        return 0.0
    altitude = (1.0 - pressure_atm) / 0.00012
    return max(0, altitude)

# Predefined altitude presets
ALTITUDE_PRESETS = {
    "sea_level": 0,
    "denver": 1609,      # Denver, CO
    "mexico_city": 2240,  # Mexico City
    "la_paz": 3515,      # La Paz, Bolivia
    "everest_base": 5364 # Everest Base Camp
}

if __name__ == "__main__":
    sensor = PressureSensor("test_pressure_sensor")
    
    print("Starting pressure sensor simulation...")
    
    test_altitudes = [0, 1000, 2000, 3000]
    
    for altitude in test_altitudes:
        sensor.set_altitude(altitude)
        sensor.set_weather_conditions("normal")
        
        print(f"\nTesting at {altitude}m altitude:")
        for i in range(5):
            data = sensor.get_sensor_data()
            print(f"  Reading {i+1}: {data}")
            time.sleep(0.5)

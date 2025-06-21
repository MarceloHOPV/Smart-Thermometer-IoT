"""
Simple Temperature Sensor for Web Dashboard
Versão simplificada e estável para uso na web - UPDATED FOR BOILING POINT
"""
import random
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTemperatureSensor:
    def __init__(self, device_id="simple_temp_sensor"):
        self.device_id = device_id
        self.current_temperature = 22.0  # Start at room temperature
        self.is_heating = False
        self.system_running = False
        self.heating_rate = 2.0  # Increased for faster heating to boiling point
        self.cooling_rate = 0.2  # degrees per reading when cooling
        self.noise_level = 0.01  # Minimal noise for precision
        self.last_update = time.time()
        self.target_temperature = 100.0  # Dynamic target based on pressure
        
        logger.info(f"Simple temperature sensor {device_id} initialized")
    
    def start_system(self):
        """Start heating simulation"""
        self.system_running = True
        logger.info("Simple temperature sensor system started")
    
    def stop_system(self):
        """Stop heating simulation"""
        self.system_running = False
        self.is_heating = False
        logger.info("Simple temperature sensor system stopped")
    
    def set_heating(self, heating_state):
        """Control heating element simulation"""
        if self.system_running:
            self.is_heating = heating_state
            logger.info(f"Simple sensor heating set to: {heating_state}")
    
    def set_target_temperature(self, target_temp):
        """Set target temperature based on calculated boiling point"""
        self.target_temperature = target_temp
        logger.info(f"Simple sensor target temperature updated to: {target_temp:.2f}°C")
    
    def update_temperature(self):
        """Update temperature based on current state - PRECISION VERSION"""
        current_time = time.time()
        time_diff = current_time - self.last_update
        
        # Only update if enough time has passed
        if time_diff < 0.3:  # Minimum 0.3 second between updates
            return
        
        if self.is_heating and self.system_running:
            # Heat towards dynamic target (boiling point)
            temp_diff = self.target_temperature - self.current_temperature
            
            if temp_diff > 0.1:  # If we're not at target yet
                # Gradual heating with precision near target
                if temp_diff > 5.0:
                    # Fast heating when far from target
                    increment = self.heating_rate * time_diff
                else:
                    # Slow precise heating near target
                    increment = 0.3 * time_diff
                    
                self.current_temperature += increment
                
                # Precision: Don't overshoot target by more than 0.05°C
                if self.current_temperature > self.target_temperature:
                    self.current_temperature = self.target_temperature + random.uniform(-0.02, 0.02)
            
        elif not self.is_heating or not self.system_running:
            # Gradual cooling towards room temperature
            room_temp = 22.0
            if self.current_temperature > room_temp:
                temp_diff = self.current_temperature - room_temp
                cooling_increment = self.cooling_rate * time_diff
                self.current_temperature -= cooling_increment
                
                # Don't go below room temperature
                if self.current_temperature < room_temp:
                    self.current_temperature = room_temp
        
        self.last_update = current_time
    
    def get_temperature(self):
        """Get current temperature reading with high precision"""
        # Update temperature first
        self.update_temperature()
        
        # Add minimal noise for realism
        noise = random.gauss(0, self.noise_level)
        measured_temp = self.current_temperature + noise
        
        # Ensure reasonable bounds
        measured_temp = max(15.0, min(125.0, measured_temp))
        
        return round(measured_temp, 2)
    
    def get_sensor_data(self, pressure_atm=1.0):
        """Get complete sensor data package"""
        temperature = self.get_temperature()
        
        return {
            'sensor_id': f"web_temp_sensor",
            'timestamp': datetime.now().isoformat(),
            'temperature': temperature,
            'unit': 'celsius',
            'is_heating': self.is_heating,
            'target_temperature': self.target_temperature,
            'sensor_status': 'active'
        }

# Test the precision sensor
if __name__ == "__main__":
    sensor = SimpleTemperatureSensor("test_precision")
    sensor.start_system()
    sensor.set_target_temperature(99.85)  # Test with specific boiling point
    sensor.set_heating(True)
    
    print("🎯 Precision sensor test - heating to exact boiling point:")
    for i in range(25):
        temp = sensor.get_temperature()
        target = sensor.target_temperature
        diff = abs(temp - target)
        status = "🎯 AT TARGET!" if diff < 0.1 else f"→ {target:.2f}°C"
        print(f"Reading {i+1:2d}: {temp:6.2f}°C {status} (diff: {diff:.2f}°C)")
        time.sleep(1)
        
        # Simulate reaching target
        if i > 15 and temp >= target - 0.5:
            print("🔥 Target reached! Testing precision...")

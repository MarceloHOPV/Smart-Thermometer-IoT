"""
Main Application Entry Point for IoT Smart Thermometer
Coordinates all system components and provides CLI interface
"""
import sys
import time
import threading
import argparse
import signal
import logging
from datetime import datetime

# Import all modules
from src.config import Config, DEVICE_ID, DEVICE_NAME
from src.temperature_sensor import TemperatureSensor
from src.pressure_sensor import PressureSensor, ALTITUDE_PRESETS
from src.mqtt_client import MQTTClient
from src.alarm_manager import AlarmManager, AlarmType
from src.web_app import app as web_app, initialize_systems, start_data_collection, stop_data_collection
from src.mobile_app import mobile_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_thermometer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartThermometerSystem:
    def __init__(self):
        self.temperature_sensor = None
        self.pressure_sensor = None
        self.mqtt_client = None
        self.alarm_manager = None
        self.running = False
        self.simulation_thread = None
        
        # System status
        self.start_time = datetime.now()
        self.data_points_collected = 0
        
        logger.info(f"Smart Thermometer System initialized - Device: {DEVICE_NAME} ({DEVICE_ID})")
    
    def initialize(self):
        """Initialize all system components"""
        try:
            # Initialize sensors
            logger.info("Initializing sensors...")
            self.temperature_sensor = TemperatureSensor(f"{DEVICE_ID}_temp")
            self.pressure_sensor = PressureSensor(f"{DEVICE_ID}_pressure")
            
            # Initialize MQTT client
            logger.info("Initializing MQTT client...")
            self.mqtt_client = MQTTClient(f"{DEVICE_ID}_main")
            if not self.mqtt_client.connect():
                logger.warning("MQTT connection failed, continuing without MQTT")
                self.mqtt_client = None
            
            # Initialize alarm manager
            logger.info("Initializing alarm manager...")
            self.alarm_manager = AlarmManager(self.mqtt_client)
            
            # Set up default alarm configurations
            self.alarm_manager.set_temperature_alarm(Config.DEFAULT_ALARM_TEMPERATURE)
            self.alarm_manager.set_boiling_point_alarm(True)
            
            logger.info("All systems initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize systems: {e}")
            return False
    
    def start(self):
        """Start the thermometer system"""
        if not self.initialize():
            logger.error("Failed to initialize system")
            return False
        
        self.running = True
        
        # Start alarm monitoring
        self.alarm_manager.start_monitoring()
        
        # Start simulation thread
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
        
        logger.info("Smart Thermometer System started")
        return True
    
    def stop(self):
        """Stop the thermometer system"""
        logger.info("Shutting down Smart Thermometer System...")
        
        self.running = False
        
        # Stop alarm monitoring
        if self.alarm_manager:
            self.alarm_manager.stop_monitoring()
        
        # Disconnect MQTT
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        
        # Wait for simulation thread to finish
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=5)
        
        logger.info("System shutdown complete")
    
    def _simulation_loop(self):
        """Main simulation loop"""
        logger.info("Starting sensor simulation loop")
        
        while self.running:
            try:
                # Get current pressure for temperature calculation
                pressure_data = self.pressure_sensor.get_sensor_data()
                current_pressure = pressure_data['pressure'] if pressure_data['pressure'] else 1.0
                
                # Get temperature reading
                temp_data = self.temperature_sensor.get_sensor_data(current_pressure)
                current_temp = temp_data['temperature']
                
                # Check alarms
                if current_temp is not None:
                    self.alarm_manager.check_temperature_alarms(current_temp, current_pressure)
                else:
                    self.alarm_manager.check_temperature_alarms(None)  # Sensor failure
                
                # Publish to MQTT if connected
                if self.mqtt_client and self.mqtt_client.is_connected:
                    self.mqtt_client.publish_temperature_data(temp_data)
                    self.mqtt_client.publish_pressure_data(pressure_data)
                
                self.data_points_collected += 1
                
                # Log status periodically
                if self.data_points_collected % 20 == 0:  # Every 20 readings
                    self._log_status(temp_data, pressure_data)
                
                time.sleep(Config.SENSOR_UPDATE_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _log_status(self, temp_data, pressure_data):
        """Log current system status"""
        uptime = datetime.now() - self.start_time
        
        temp_str = f"{temp_data['temperature']:.1f}°C" if temp_data['temperature'] else "ERROR"
        pressure_str = f"{pressure_data['pressure']:.3f} atm" if pressure_data['pressure'] else "ERROR"
        heating_str = "ON" if temp_data.get('is_heating', False) else "OFF"
        
        alarm_status = self.alarm_manager.get_alarm_status()
        active_alarms = alarm_status['active_alarms_count']
        
        logger.info(f"STATUS: Temp={temp_str} | Pressure={pressure_str} | Heating={heating_str} | "
                   f"Alarms={active_alarms} | Uptime={uptime} | Data points={self.data_points_collected}")
    
    def get_system_status(self):
        """Get comprehensive system status"""
        if not self.running:
            return {"status": "stopped"}
        
        uptime = datetime.now() - self.start_time
        
        # Get current sensor readings
        pressure_data = self.pressure_sensor.get_sensor_data() if self.pressure_sensor else {}
        current_pressure = pressure_data.get('pressure', 1.0) if pressure_data else 1.0
        temp_data = self.temperature_sensor.get_sensor_data(current_pressure) if self.temperature_sensor else {}
        
        # Get alarm status
        alarm_status = self.alarm_manager.get_alarm_status() if self.alarm_manager else {}
        
        # Get MQTT status
        mqtt_status = self.mqtt_client.get_connection_status() if self.mqtt_client else {'connected': False}
        
        return {
            'status': 'running',
            'device_id': DEVICE_ID,
            'device_name': DEVICE_NAME,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_str': str(uptime).split('.')[0],  # Remove microseconds
            'data_points_collected': self.data_points_collected,
            'temperature': temp_data,
            'pressure': pressure_data,
            'alarms': alarm_status,
            'mqtt': mqtt_status,
            'start_time': self.start_time.isoformat()
        }

# Global system instance
system = SmartThermometerSystem()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    system.stop()
    sys.exit(0)

def run_cli_interface():
    """Run interactive CLI interface"""
    print(f"\n{DEVICE_NAME} - Interactive CLI")
    print("=" * 50)
    print("Commands:")
    print("  status       - Show system status")
    print("  heating on   - Turn heating on")
    print("  heating off  - Turn heating off")
    print("  temp <value> - Set target temperature")
    print("  altitude <m> - Set altitude in meters")
    print("  alarms       - Show active alarms")
    print("  reset        - Reset sensors")
    print("  quit         - Exit")
    print()
    
    while system.running:
        try:
            command = input("thermometer> ").strip().lower()
            
            if command == "quit" or command == "exit":
                break
            elif command == "status":
                status = system.get_system_status()
                print(f"\nDevice: {status['device_name']} ({status['device_id']})")
                print(f"Status: {status['status']}")
                print(f"Uptime: {status['uptime_str']}")
                print(f"Data points: {status['data_points_collected']}")
                
                if status.get('temperature'):
                    temp = status['temperature']
                    print(f"Temperature: {temp.get('temperature', 'N/A')}°C (Target: {temp.get('target_temperature', 'N/A')}°C)")
                    print(f"Heating: {'ON' if temp.get('is_heating', False) else 'OFF'}")
                
                if status.get('pressure'):
                    pressure = status['pressure']
                    print(f"Pressure: {pressure.get('pressure', 'N/A')} atm")
                    print(f"Altitude: {pressure.get('altitude_meters', 'N/A')} m")
                
                if status.get('alarms'):
                    alarms = status['alarms']
                    print(f"Active alarms: {alarms.get('active_alarms_count', 0)}")
                
                mqtt = status.get('mqtt', {})
                print(f"MQTT: {'Connected' if mqtt.get('connected', False) else 'Disconnected'}")
                
            elif command.startswith("heating "):
                state = command.split()[1]
                if state == "on":
                    system.temperature_sensor.set_heating(True)
                    print("Heating turned ON")
                elif state == "off":
                    system.temperature_sensor.set_heating(False)
                    print("Heating turned OFF")
                else:
                    print("Usage: heating on|off")
                    
            elif command.startswith("temp "):
                try:
                    temp_value = float(command.split()[1])
                    system.temperature_sensor.set_target_temperature(temp_value)
                    print(f"Target temperature set to {temp_value}°C")
                except ValueError:
                    print("Usage: temp <temperature_value>")
                    
            elif command.startswith("altitude "):
                try:
                    altitude_value = float(command.split()[1])
                    system.pressure_sensor.set_altitude(altitude_value)
                    print(f"Altitude set to {altitude_value}m")
                except ValueError:
                    print("Usage: altitude <meters>")
                    
            elif command == "alarms":
                alarm_status = system.alarm_manager.get_alarm_status()
                active_alarms = alarm_status.get('active_alarms', [])
                
                if active_alarms:
                    print(f"\nActive alarms ({len(active_alarms)}):")
                    for alarm in active_alarms:
                        print(f"  - {alarm['type']}: {alarm['message']}")
                        print(f"    Time: {alarm['datetime']}")
                else:
                    print("No active alarms")
                    
            elif command == "reset":
                system.temperature_sensor.reset_sensor()
                system.pressure_sensor.reset_sensor()
                system.alarm_manager.clear_all_alarms()
                print("All sensors and alarms reset")
                
            elif command == "help":
                print("Available commands: status, heating on/off, temp <value>, altitude <value>, alarms, reset, quit")
                
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='IoT Smart Thermometer System')
    parser.add_argument('--mode', choices=['web', 'mobile', 'cli', 'simulation'], 
                       default='web', help='Run mode (default: web)')
    parser.add_argument('--host', default=Config.WEB_HOST, help='Host to bind to')
    parser.add_argument('--port', type=int, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-mqtt', action='store_true', help='Disable MQTT connection')
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"Starting {DEVICE_NAME} in {args.mode} mode...")
    
    try:
        if args.mode == 'web':
            # Run web interface
            initialize_systems()
            start_data_collection()
            
            port = args.port or Config.WEB_PORT
            print(f"Web interface available at http://{args.host}:{port}")
            web_app.run(host=args.host, port=port, debug=args.debug)
            
        elif args.mode == 'mobile':
            # Run mobile interface
            port = args.port or Config.MOBILE_PORT
            print(f"Mobile interface available at http://{args.host}:{port}")
            mobile_app.run(host=args.host, port=port, debug=args.debug)
            
        elif args.mode == 'cli':
            # Run CLI interface
            if system.start():
                run_cli_interface()
            else:
                logger.error("Failed to start system")
                return 1
                
        elif args.mode == 'simulation':
            # Run simulation only
            if system.start():
                print("Simulation running... Press Ctrl+C to stop")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            else:
                logger.error("Failed to start system")
                return 1
                
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
    finally:
        # Cleanup
        system.stop()
        stop_data_collection()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

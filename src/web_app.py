"""
Web Dashboard for IoT Smart Thermometer
Flask-based web interface for monitoring and controlling the thermometer
"""
from flask import Flask, request, jsonify, redirect, url_for
from flask_cors import CORS
import json
import time
import threading
import logging
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.utils
from config import Config, calculate_boiling_point, DEVICE_ID, DEVICE_NAME
try:
    from temperature_sensor import TemperatureSensor
    from pressure_sensor import PressureSensor, ALTITUDE_PRESETS
    from mqtt_client import MQTTClient
    from smart_alarm_manager import SmartAlarmManager
except ImportError:
    # Try absolute imports if relative imports fail
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from temperature_sensor import TemperatureSensor
    from pressure_sensor import PressureSensor, ALTITUDE_PRESETS
    from mqtt_client import MQTTClient
    from smart_alarm_manager import SmartAlarmManager

# Import simple sensor as backup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from simple_temperature_sensor_precision import PrecisionTemperatureSensor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Flask with correct static and template directories
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
app.secret_key = 'smart_thermometer_secret_key'

# Enable CORS for frontend communication
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", 
                   "http://localhost:8080", "http://127.0.0.1:8080",
                   "http://localhost:8081", "http://127.0.0.1:8081", 
                   "http://localhost:8082", "http://127.0.0.1:8082", 
                   "file://"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Global variables for sensors and systems
temperature_sensor = None
pressure_sensor = None
mqtt_client = None
alarm_manager = None
data_history = {
    'timestamps': [],
    'temperatures': [],
    'pressures': [],
    'boiling_points': []
}

# Data collection thread control
data_collection_active = False
data_collection_thread = None

def initialize_systems():
    """Initialize all system components"""
    global temperature_sensor, pressure_sensor, mqtt_client, alarm_manager
    
    # Use simple temperature sensor for better stability
    temperature_sensor = PrecisionTemperatureSensor()
    pressure_sensor = PressureSensor("web_pressure_sensor")
    
    # Initialize MQTT client
    mqtt_client = MQTTClient("web_dashboard")
    if not mqtt_client.connect():
        print("Warning: MQTT connection failed, continuing without MQTT")
        mqtt_client = None
    
    # Initialize alarm manager
    alarm_manager = SmartAlarmManager(mqtt_client)
    alarm_manager.start_monitoring()
    
    print("All systems initialized")

def collect_sensor_data():
    """Background thread for collecting sensor data"""
    global data_collection_active
    
    while data_collection_active:
        try:
            # Get current pressure
            pressure_data = pressure_sensor.get_sensor_data()
            current_pressure = pressure_data.get('pressure', 1.0) if pressure_data else 1.0
            
            # Get temperature reading
            temp_data = temperature_sensor.get_data(current_pressure)
            current_temp = temp_data.get('temperature') if temp_data else None
            
            # Calculate boiling point
            boiling_point = calculate_boiling_point(current_pressure)
            
            # Update temperature sensor target to match calculated boiling point
            temperature_sensor.set_target_temperature(boiling_point)
            
            if current_temp is not None:
                # Store in history
                timestamp = datetime.now()
                data_history['timestamps'].append(timestamp.isoformat())
                data_history['temperatures'].append(current_temp)
                data_history['pressures'].append(current_pressure)
                data_history['boiling_points'].append(boiling_point)
                
                # Limit history to last 200 points
                if len(data_history['timestamps']) > 200:
                    for key in data_history:
                        data_history[key] = data_history[key][-200:]
                
                # Check alarms
                if alarm_manager and alarm_manager.is_monitoring:
                    alarm_manager.check_alarms(temp_data, pressure_data, boiling_point)
                
                # Publish to MQTT (with better error handling)
                if mqtt_client:
                    try:
                        if mqtt_client.is_connected:
                            mqtt_client.publish_temperature_data(temp_data)
                            mqtt_client.publish_pressure_data(pressure_data)
                    except Exception as mqtt_error:
                        logger.warning(f"MQTT publish error: {mqtt_error}")
            
            time.sleep(3)  # Collect data every 3 seconds
            
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            time.sleep(5)  # Wait longer on error

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return app.send_static_file('index.html')

@app.route('/api/sensor_data')
def get_sensor_data():
    """API endpoint for current sensor readings"""
    try:
        # Get real sensor data
        if not temperature_sensor or not pressure_sensor:
            return jsonify({'error': 'Sensors not initialized'}), 500
            
        # Get current pressure reading
        pressure_data = pressure_sensor.get_sensor_data()
        current_pressure = pressure_data.get('pressure', 1.0) if pressure_data else 1.0
          # Get temperature reading
        temp_data = temperature_sensor.get_data(current_pressure)
        
        # Calculate boiling point based on pressure
        boiling_point = calculate_boiling_point(current_pressure)
        
        return jsonify({
            'temperature': {
                'temperature': temp_data.get('temperature', 22.0),
                'unit': temp_data.get('temperature_unit', 'celsius'),
                'sensor_id': temp_data.get('device_id', 'unknown'),
                'timestamp': temp_data.get('timestamp', datetime.now().isoformat()),
                'is_heating': temp_data.get('is_heating', False),
                'target_temperature': temp_data.get('target_temperature', 100.0),
                'sensor_status': temp_data.get('sensor_status', 'active')
            },
            'pressure': {
                'pressure': pressure_data.get('pressure', 1.0) if pressure_data else 1.0,
                'unit': pressure_data.get('unit', 'atm') if pressure_data else 'atm',
                'sensor_id': pressure_data.get('device_id', 'unknown') if pressure_data else 'unknown',
                'timestamp': pressure_data.get('timestamp', datetime.now().isoformat()) if pressure_data else datetime.now().isoformat()
            },
            'boiling_point': boiling_point,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical_data')
def get_historical_data():
    """API endpoint for historical sensor data"""
    try:
        # Convert timestamps to strings for JSON serialization
        timestamps_str = [ts.isoformat() for ts in data_history['timestamps']]
        
        return jsonify({
            'timestamps': timestamps_str,
            'temperatures': data_history['temperatures'],
            'pressures': data_history['pressures'],
            'boiling_points': data_history['boiling_points']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart_data')
def get_chart_data():
    """API endpoint for chart data"""
    try:
        import random
        import time
        from datetime import datetime, timedelta
        
        # Generate some sample historical data
        timestamps = []
        temperatures = []
        pressures = []
        boiling_points = []
        
        base_time = datetime.now() - timedelta(minutes=30)
        
        for i in range(30):
            timestamp = base_time + timedelta(minutes=i)
            temp = 25.0 + random.random() * 30  # 25-55°C
            pressure = 0.95 + random.random() * 0.1  # 0.95-1.05 bar
            boiling = 100.0 - (1.0 - pressure) * 10
            
            timestamps.append(timestamp.isoformat())
            temperatures.append(temp)
            pressures.append(pressure)
            boiling_points.append(boiling)
        
        return jsonify({
            'timestamps': timestamps,
            'temperatures': temperatures,
            'pressures': pressures,
            'boiling_points': boiling_points
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/control/heating', methods=['POST'])
def control_heating():
    """API endpoint for controlling heating element"""
    try:
        data = request.get_json()
        heating_state = data.get('heating', False)
        
        temperature_sensor.set_heating(heating_state)
        
        return jsonify({
            'success': True,
            'heating': heating_state,
            'message': f"Heating {'enabled' if heating_state else 'disabled'}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/control/target_temperature', methods=['POST'])
def set_target_temperature():
    """API endpoint for setting target temperature"""
    try:
        data = request.get_json()
        target_temp = float(data.get('temperature', 100.0))
        
        temperature_sensor.set_target_temperature(target_temp)
        
        return jsonify({
            'success': True,
            'target_temperature': target_temp,
            'message': f"Target temperature set to {target_temp}°C"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/control/altitude', methods=['POST'])
def set_altitude():
    """API endpoint for setting altitude/location"""
    try:
        data = request.get_json()
        altitude = data.get('altitude')
        preset = data.get('preset')
        
        if preset and preset in ALTITUDE_PRESETS:
            altitude = ALTITUDE_PRESETS[preset]
        
        if altitude is not None:
            pressure_sensor.set_altitude(float(altitude))
            
            return jsonify({
                'success': True,
                'altitude': altitude,
                'preset': preset,
                'message': f"Altitude set to {altitude}m"
            })
        else:
            return jsonify({'error': 'No altitude specified'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alarms')
def get_alarms():
    """API endpoint for alarm status"""
    try:
        # Use new SmartAlarmManager status method
        status = alarm_manager.get_status()
        return jsonify(status)
    except Exception as e:
        # Return a safe error response
        return jsonify({
            'error': str(e),
            'alarm_mode': None,
            'is_active': False,
            'active_alarms_count': 0,
            'active_alarms': []
        }), 500

@app.route('/api/alarms/configure', methods=['POST'])
def configure_alarms():
    """API endpoint for configuring alarms with NEW EXCLUSIVE LOGIC"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
          # Validate and configure alarm mode (EXCLUSIVE)
        alarm_mode = data.get('mode')
        if not alarm_mode:
            return jsonify({'error': 'Alarm mode is required'}), 400
          # NÃO limpar alarmes aqui - deixa o alarm manager decidir
        # baseado na lógica inteligente de configure_alarm()
        
        # Configure new alarm based on mode
        if alarm_mode == 'temperature_only':
            threshold = data.get('threshold', 95.0)
            success = alarm_manager.configure_alarm('temperature_only', threshold=threshold)
            
        elif alarm_mode == 'time_only':
            duration = data.get('duration', 300)
            success = alarm_manager.configure_alarm('time_only', duration=duration)
            
        elif alarm_mode == 'boiling_only':
            offset = data.get('offset', 0.0)
            success = alarm_manager.configure_alarm('boiling_only', offset=offset)
            
        elif alarm_mode == 'boiling_then_time':
            offset = data.get('offset', 0.0)
            duration = data.get('duration', 300)
            success = alarm_manager.configure_alarm('boiling_then_time', offset=offset, duration=duration)
            
        else:
            return jsonify({'error': f'Invalid alarm mode: {alarm_mode}'}), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Alarm configured: {alarm_mode}',
                'status': alarm_manager.get_status()
            })
        else:
            return jsonify({'error': 'Failed to configure alarm'}), 500
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Alarm acknowledgment removed - new system uses automatic alarms

@app.route('/api/alarms/clear', methods=['POST'])
def clear_alarms():
    """API endpoint for clearing all alarms"""
    try:
        alarm_manager.clear_all_alarms()
        return jsonify({
            'success': True,
            'message': 'All alarms cleared',
            'status': alarm_manager.get_status()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/status')
def system_status():
    """API endpoint for system status"""
    try:
        mqtt_status = mqtt_client.get_connection_status() if mqtt_client else {'connected': False}
          return jsonify({
            'sensors': {
                'temperature': {
                    'active': hasattr(temperature_sensor, 'running') and temperature_sensor.running,
                    'failed': False,
                    'heating': temperature_sensor.is_heating,
                    'target_temp': temperature_sensor.get_target_temperature()
                },
                'pressure': {
                    'active': pressure_sensor.is_active,
                    'failed': pressure_sensor.is_failed,
                    'altitude': pressure_sensor.altitude_meters
                }
            },
            'mqtt': mqtt_status,
            'data_collection': data_collection_active,
            'data_points': len(data_history['timestamps'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DEBUG: Simple alarm test route
@app.route('/api/debug/alarms')
def debug_alarms():
    """Simple debug route for alarm testing"""
    try:
        return jsonify({
            'message': 'Debug alarm route working',
            'timestamp': time.time(),
            'alarm_manager_exists': alarm_manager is not None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alarms/status')
def get_alarm_status():
    """API endpoint for alarm status - specific endpoint"""
    try:
        status = alarm_manager.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'alarm_mode': None,
            'is_active': False,
            'active_alarms_count': 0,
            'active_alarms': []
        }), 500

@app.route('/api/system/start', methods=['POST'])
def start_system():
    """API endpoint to start the system"""
    global data_collection_active
    try:
        data_collection_active = True
        
        # Iniciar o sistema do sensor primeiro
        if temperature_sensor:
            temperature_sensor.start_system()  # IMPORTANTE: Iniciar o sistema primeiro
            temperature_sensor.set_heating(True)
            temperature_sensor.set_target_temperature(100.0)  # Aquecer até ferver
            print("🔥 Sistema e aquecimento ativados - simulando cozimento")
        
        print("🚀 Sistema iniciado via API")
        
        return jsonify({
            'status': 'success',
            'message': 'Sistema iniciado - aquecimento ativo',
            'data_collection': data_collection_active,
            'heating': True
        })
    except Exception as e:
        print(f"Erro ao iniciar sistema: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    """API endpoint to stop the system"""
    global data_collection_active
    try:
        data_collection_active = False
        
        # Parar aquecimento
        if temperature_sensor:
            temperature_sensor.set_heating(False)
            print("❄️ Aquecimento desativado")
        
        print("⏹️ Sistema parado via API")
        
        return jsonify({
            'status': 'success',
            'message': 'Sistema parado - aquecimento desativado',
            'data_collection': data_collection_active,
            'heating': False
        })
    except Exception as e:
        print(f"Erro ao parar sistema: {e}")
        return jsonify({'error': str(e)}), 500

def start_data_collection():
    """Start the background data collection"""
    global data_collection_active, data_collection_thread
    
    if not data_collection_active:
        data_collection_active = True
        data_collection_thread = threading.Thread(target=collect_sensor_data, daemon=True)
        data_collection_thread.start()
        print("Data collection started")

def stop_data_collection():
    """Stop the background data collection"""
    global data_collection_active
    
    data_collection_active = False
    if data_collection_thread:
        data_collection_thread.join(timeout=5)
    print("Data collection stopped")

@app.route('/api/debug/force_alarm_check', methods=['POST'])
def force_alarm_check():
    """Force manual alarm check for debugging"""
    try:        # Get current sensor data
        pressure_data = pressure_sensor.get_sensor_data()
        current_pressure = pressure_data.get('pressure', 1.0) if pressure_data else 1.0
        temp_data = temperature_sensor.get_data(current_pressure)
        boiling_point = calculate_boiling_point(current_pressure)
        
        # Force alarm check
        triggered_alarms = alarm_manager.check_alarms(temp_data, pressure_data, boiling_point)
        
        return jsonify({
            'success': True,
            'message': 'Manual alarm check completed',
            'temperature': temp_data.get('temperature') if temp_data else None,
            'boiling_point': boiling_point,
            'triggered_alarms': len(triggered_alarms),
            'alarm_config': alarm_manager.current_alarm_config,
            'data_collection_active': data_collection_active
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Force module reload for development
import importlib
def reload_sensor_module():
    """Force reload of sensor modules for development"""
    global temperature_sensor
    try:
        # Reimport the module
        from importlib import reload
        import sys
        if 'simple_temperature_sensor_precision' in sys.modules:
            reload(sys.modules['simple_temperature_sensor_precision'])
        
        # Recreate sensor instance
        from simple_temperature_sensor_precision import PrecisionTemperatureSensor
        temperature_sensor = PrecisionTemperatureSensor()
        logger.info("Sensor module reloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reload sensor module: {e}")
        return False

@app.route('/api/system/reload_sensor')
def reload_sensor():
    """Reload sensor module endpoint"""
    try:
        if reload_sensor_module():
            return jsonify({'success': True, 'message': 'Sensor module reloaded'})
        else:
            return jsonify({'success': False, 'message': 'Failed to reload sensor module'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    try:
        # Initialize systems
        initialize_systems()
        
        # Start data collection
        start_data_collection()
        
        # Run Flask app
        print(f"Starting web dashboard on {Config.WEB_HOST}:{Config.WEB_PORT}")
        app.run(host=Config.WEB_HOST, port=Config.WEB_PORT, debug=Config.WEB_DEBUG)
        
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Cleanup
        stop_data_collection()
        if alarm_manager:
            alarm_manager.stop_monitoring()
        if mqtt_client:
            mqtt_client.disconnect()

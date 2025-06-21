"""
Mobile App Simulation for IoT Smart Thermometer
Flask-based mobile interface with simplified UI optimized for mobile devices
"""
from flask import Flask, render_template, request, jsonify
import json
import time
import requests
from datetime import datetime
from .config import Config, calculate_boiling_point, DEVICE_ID, DEVICE_NAME

mobile_app = Flask(__name__)
mobile_app.secret_key = 'smart_thermometer_mobile_secret'

# Configuration for connecting to main web app
MAIN_APP_URL = f"http://{Config.WEB_HOST}:{Config.WEB_PORT}"

class MobileAppClient:
    def __init__(self, main_app_url):
        self.main_app_url = main_app_url
        self.last_data = {}
        self.connection_status = False
    
    def get_sensor_data(self):
        """Get sensor data from main app"""
        try:
            response = requests.get(f"{self.main_app_url}/api/sensor_data", timeout=5)
            if response.status_code == 200:
                self.last_data = response.json()
                self.connection_status = True
                return self.last_data
            else:
                self.connection_status = False
                return None
        except Exception as e:
            print(f"Error getting sensor data: {e}")
            self.connection_status = False
            return None
    
    def get_alarms(self):
        """Get alarm status from main app"""
        try:
            response = requests.get(f"{self.main_app_url}/api/alarms", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting alarms: {e}")
            return None
    
    def control_heating(self, heating_state):
        """Control heating element"""
        try:
            response = requests.post(
                f"{self.main_app_url}/api/control/heating",
                json={'heating': heating_state},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error controlling heating: {e}")
            return False
    
    def set_target_temperature(self, temperature):
        """Set target temperature"""
        try:
            response = requests.post(
                f"{self.main_app_url}/api/control/target_temperature",
                json={'temperature': temperature},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error setting temperature: {e}")
            return False
      # acknowledge_alarm removed - new system uses automatic alarms

# Initialize mobile client
mobile_client = MobileAppClient(MAIN_APP_URL)

@mobile_app.route('/')
def mobile_dashboard():
    """Mobile dashboard page"""
    return render_template('mobile_dashboard.html', 
                         device_name=DEVICE_NAME,
                         device_id=DEVICE_ID)

@mobile_app.route('/api/mobile/sensor_data')
def mobile_get_sensor_data():
    """API endpoint for mobile sensor data"""
    data = mobile_client.get_sensor_data()
    if data:
        # Add mobile-specific formatting
        mobile_data = {
            'temperature': data.get('temperature', {}).get('temperature'),
            'temperature_unit': 'C',
            'pressure': data.get('pressure', {}).get('pressure'),
            'pressure_unit': 'atm',
            'boiling_point': data.get('boiling_point'),
            'is_heating': data.get('temperature', {}).get('is_heating', False),
            'target_temperature': data.get('temperature', {}).get('target_temperature'),
            'altitude': data.get('pressure', {}).get('altitude_meters', 0),
            'connection_status': mobile_client.connection_status,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(mobile_data)
    else:
        return jsonify({'error': 'Unable to connect to thermometer'}), 503

@mobile_app.route('/api/mobile/alarms')
def mobile_get_alarms():
    """API endpoint for mobile alarms"""
    alarms = mobile_client.get_alarms()
    if alarms:
        # Simplify alarm data for mobile
        mobile_alarms = {
            'active_count': alarms.get('active_alarms_count', 0),
            'active_alarms': [
                {
                    'id': alarm['id'],
                    'type': alarm['type'].replace('_', ' ').title(),
                    'message': alarm['message'],
                    'time': datetime.fromisoformat(alarm['datetime']).strftime('%H:%M:%S'),
                    'priority': alarm['priority'].name if hasattr(alarm['priority'], 'name') else alarm['priority']
                }
                for alarm in alarms.get('active_alarms', [])
            ]
        }
        return jsonify(mobile_alarms)
    else:
        return jsonify({'error': 'Unable to get alarm data'}), 503

@mobile_app.route('/api/mobile/control/heating', methods=['POST'])
def mobile_control_heating():
    """Mobile heating control"""
    try:
        data = request.get_json()
        heating_state = data.get('heating', False)
        
        success = mobile_client.control_heating(heating_state)
        
        return jsonify({
            'success': success,
            'heating': heating_state,
            'message': f"Heating {'enabled' if heating_state else 'disabled'}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mobile_app.route('/api/mobile/control/temperature', methods=['POST'])
def mobile_set_temperature():
    """Mobile temperature control"""
    try:
        data = request.get_json()
        temperature = float(data.get('temperature', 100.0))
        
        success = mobile_client.set_target_temperature(temperature)
        
        return jsonify({
            'success': success,
            'temperature': temperature,
            'message': f"Target temperature set to {temperature}°C"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mobile_app.route('/api/mobile/alarms/acknowledge/<alarm_id>', methods=['POST'])
def mobile_acknowledge_alarm(alarm_id):
    """Mobile alarm acknowledgment"""
    try:
        success = mobile_client.acknowledge_alarm(alarm_id)
        
        return jsonify({
            'success': success,
            'message': 'Alarm acknowledged' if success else 'Failed to acknowledge alarm'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mobile_app.route('/settings')
def mobile_settings():
    """Mobile settings page"""
    return render_template('mobile_settings.html',
                         device_name=DEVICE_NAME,
                         device_id=DEVICE_ID)

@mobile_app.route('/alarms')
def mobile_alarms():
    """Mobile alarms page"""
    return render_template('mobile_alarms.html',
                         device_name=DEVICE_NAME,
                         device_id=DEVICE_ID)

# Quick action endpoints for mobile widgets
@mobile_app.route('/api/mobile/quick/start_heating', methods=['POST'])
def quick_start_heating():
    """Quick action: Start heating"""
    success = mobile_client.control_heating(True)
    return jsonify({'success': success})

@mobile_app.route('/api/mobile/quick/stop_heating', methods=['POST'])
def quick_stop_heating():
    """Quick action: Stop heating"""
    success = mobile_client.control_heating(False)
    return jsonify({'success': success})

@mobile_app.route('/api/mobile/quick/boil_water', methods=['POST'])
def quick_boil_water():
    """Quick action: Set to boil water (100°C and start heating)"""
    temp_success = mobile_client.set_target_temperature(100.0)
    heat_success = mobile_client.control_heating(True)
    return jsonify({'success': temp_success and heat_success})

# Mobile notification simulation
@mobile_app.route('/api/mobile/notifications')
def mobile_notifications():
    """Get mobile notifications"""
    alarms = mobile_client.get_alarms()
    notifications = []
    
    if alarms and alarms.get('active_alarms_count', 0) > 0:
        for alarm in alarms.get('active_alarms', []):
            notifications.append({
                'id': alarm['id'],
                'title': 'Smart Thermometer Alert',
                'message': alarm['message'],
                'type': 'alarm',
                'timestamp': alarm['datetime']
            })
    
    # Add system notifications
    sensor_data = mobile_client.get_sensor_data()
    if sensor_data:
        temp = sensor_data.get('temperature', {}).get('temperature')
        if temp and temp >= 100:
            notifications.append({
                'id': 'boiling_notification',
                'title': 'Water is Boiling!',
                'message': f'Temperature reached {temp:.1f}°C',
                'type': 'info',
                'timestamp': datetime.now().isoformat()
            })
    
    return jsonify({'notifications': notifications})

# PWA Support
@mobile_app.route('/manifest.json')
def mobile_manifest():
    """PWA manifest for mobile app"""
    manifest = {
        "name": "Smart Thermometer",
        "short_name": "Thermometer",
        "description": "IoT Smart Thermometer Mobile App",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#007bff",
        "icons": [
            {
                "src": "/static/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return jsonify(manifest)

@mobile_app.route('/sw.js')
def service_worker():
    """Service worker for PWA functionality"""
    sw_content = """
    const CACHE_NAME = 'smart-thermometer-v1';
    const urlsToCache = [
        '/',
        '/static/css/mobile.css',
        '/static/js/mobile.js'
    ];

    self.addEventListener('install', function(event) {
        event.waitUntil(
            caches.open(CACHE_NAME)
                .then(function(cache) {
                    return cache.addAll(urlsToCache);
                })
        );
    });

    self.addEventListener('fetch', function(event) {
        event.respondWith(
            caches.match(event.request)
                .then(function(response) {
                    if (response) {
                        return response;
                    }
                    return fetch(event.request);
                }
            )
        );
    });
    """
    
    response = mobile_app.response_class(
        sw_content,
        mimetype='application/javascript'
    )
    return response

if __name__ == '__main__':
    print(f"Starting mobile app on {Config.MOBILE_HOST}:{Config.MOBILE_PORT}")
    print(f"Connecting to main app at {MAIN_APP_URL}")
    
    mobile_app.run(
        host=Config.MOBILE_HOST, 
        port=Config.MOBILE_PORT, 
        debug=Config.WEB_DEBUG
    )

"""
MQTT Client for IoT Smart Thermometer
Handles all MQTT communication for sensor data and device control
"""
import json
import time
import threading
import logging
from datetime import datetime
from paho.mqtt.client import Client
from config import Config, DEVICE_ID, DEVICE_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, client_id=None):
        self.client_id = client_id or f"{DEVICE_ID}_{int(time.time())}"
        self.client = Client(self.client_id)
        self.is_connected = False
        self.message_handlers = {}
        self.last_publish_time = {}
        
        # Setup MQTT client callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        
        # Message queue for reliable delivery
        self.message_queue = []
        self.queue_lock = threading.Lock()
        
        logger.info(f"MQTT Client initialized with ID: {self.client_id}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"Connected to MQTT broker at {Config.MQTT_BROKER}:{Config.MQTT_PORT}")
            
            # Subscribe to control topics
            self._subscribe_to_control_topics()
            
            # Publish device online status
            self.publish_device_status("online")
            
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects"""
        self.is_connected = False
        if rc != 0:
            logger.warning("Unexpected MQTT disconnection. Will auto-reconnect")
        else:
            logger.info("MQTT client disconnected")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"Received message on topic {topic}: {payload}")
            
            # Handle different message types
            if topic in self.message_handlers:
                self.message_handlers[topic](payload)
            else:
                self._handle_default_message(topic, payload)
                
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON message on topic {msg.topic}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for when a message is published"""
        logger.debug(f"Message published with ID: {mid}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.is_connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            if not self.is_connected:
                logger.error("Failed to connect to MQTT broker within timeout")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.is_connected:
            self.publish_device_status("offline")
            time.sleep(1)  # Give time for last message to send
        
        self.client.loop_stop()
        self.client.disconnect()
        self.is_connected = False
        logger.info("MQTT client disconnected")
    
    def _subscribe_to_control_topics(self):
        """Subscribe to control and configuration topics"""
        control_topics = [
            f"{Config.MQTT_TOPIC_CONFIG}/{DEVICE_ID}",
            f"smart_thermometer/control/{DEVICE_ID}",
            "smart_thermometer/control/all"
        ]
        
        for topic in control_topics:
            self.client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
    
    def add_message_handler(self, topic, handler_function):
        """Add a custom message handler for specific topics"""
        self.message_handlers[topic] = handler_function
        logger.info(f"Added message handler for topic: {topic}")
    
    def _handle_default_message(self, topic, payload):
        """Handle messages that don't have specific handlers"""
        if "config" in topic:
            self._handle_config_message(payload)
        elif "control" in topic:
            self._handle_control_message(payload)
    
    def _handle_config_message(self, payload):
        """Handle configuration messages"""
        logger.info(f"Configuration message received: {payload}")
        # Configuration handling would be implemented here
        # For example: updating alarm thresholds, sensor calibration, etc.
    
    def _handle_control_message(self, payload):
        """Handle control messages"""
        logger.info(f"Control message received: {payload}")
        # Control handling would be implemented here
        # For example: start/stop heating, reset sensors, etc.
    
    def publish_temperature_data(self, temperature_data):
        """Publish temperature sensor data"""
        topic = f"{Config.MQTT_TOPIC_TEMPERATURE}/{DEVICE_ID}"
        return self._publish_with_retry(topic, temperature_data)
    
    def publish_pressure_data(self, pressure_data):
        """Publish pressure sensor data"""
        topic = f"{Config.MQTT_TOPIC_PRESSURE}/{DEVICE_ID}"
        return self._publish_with_retry(topic, pressure_data)
    
    def publish_alarm_data(self, alarm_data):
        """Publish alarm notifications"""
        topic = f"{Config.MQTT_TOPIC_ALARMS}/{DEVICE_ID}"
        return self._publish_with_retry(topic, alarm_data)
    
    def publish_device_status(self, status):
        """Publish device online/offline status"""
        status_data = {
            'device_id': DEVICE_ID,
            'device_name': DEVICE_NAME,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        topic = f"smart_thermometer/status/{DEVICE_ID}"
        return self._publish_with_retry(topic, status_data)
    
    def _publish_with_retry(self, topic, data, qos=1, retain=False):
        """Publish message with retry logic"""
        if not self.is_connected:
            logger.warning("Not connected to MQTT broker. Adding message to queue.")
            with self.queue_lock:
                self.message_queue.append((topic, data, qos, retain))
            return False
        
        try:
            # Add timestamp if not present
            if isinstance(data, dict) and 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Convert to JSON
            payload = json.dumps(data, default=str)
            
            # Publish message
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == 0:
                logger.debug(f"Published to {topic}: {data}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}. Return code: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def process_queued_messages(self):
        """Process any queued messages when connection is restored"""
        if not self.is_connected:
            return
        
        with self.queue_lock:
            while self.message_queue:
                topic, data, qos, retain = self.message_queue.pop(0)
                if not self._publish_with_retry(topic, data, qos, retain):
                    # If publish fails, put message back at front of queue
                    self.message_queue.insert(0, (topic, data, qos, retain))
                    break
    
    def get_connection_status(self):
        """Get current connection status"""
        return {
            'connected': self.is_connected,
            'client_id': self.client_id,
            'broker': Config.MQTT_BROKER,
            'port': Config.MQTT_PORT,
            'queued_messages': len(self.message_queue)
        }

# Example usage and testing
if __name__ == "__main__":
    mqtt_client = MQTTClient()
    
    if mqtt_client.connect():
        print("MQTT client connected successfully")
        
        # Test publishing some data
        test_temp_data = {
            'temperature': 25.5,
            'device_id': DEVICE_ID,
            'sensor_status': 'active'
        }
        
        test_pressure_data = {
            'pressure': 1.013,
            'device_id': DEVICE_ID,
            'altitude': 0
        }
        
        mqtt_client.publish_temperature_data(test_temp_data)
        mqtt_client.publish_pressure_data(test_pressure_data)
        
        # Keep running for a few seconds
        time.sleep(5)
        
        mqtt_client.disconnect()
    else:
        print("Failed to connect to MQTT broker")

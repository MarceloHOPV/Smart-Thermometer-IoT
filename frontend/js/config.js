// Smart Thermometer Configuration
const CONFIG = {
    // API Configuration
    API_BASE_URL: 'http://localhost:5000/api',
    MOBILE_API_URL: 'http://localhost:5001/api/mobile',
    
    // Update intervals (milliseconds)
    SENSOR_UPDATE_INTERVAL: 2000,    // 2 seconds
    CHART_UPDATE_INTERVAL: 5000,     // 5 seconds
    ALARM_UPDATE_INTERVAL: 3000,     // 3 seconds
    
    // Device Configuration
    DEVICE_ID: 'smart_thermometer_001',
    DEVICE_NAME: 'Smart Food Thermometer',
    
    // Temperature Limits
    TEMP_MIN: 10,
    TEMP_MAX: 120,
    
    // Pressure Limits
    PRESSURE_MIN: 0.5,
    PRESSURE_MAX: 1.5,
    
    // Altitude Presets
    ALTITUDE_PRESETS: {
        'sea_level': {
            name: 'Sea Level',
            altitude: 0,
            pressure: 1.000
        },
        'denver': {
            name: 'Denver, CO',
            altitude: 1609,
            pressure: 0.837
        },
        'mexico_city': {
            name: 'Mexico City',
            altitude: 2240,
            pressure: 0.774
        },
        'la_paz': {
            name: 'La Paz, Bolivia',
            altitude: 3515,
            pressure: 0.658
        },
        'everest_base': {
            name: 'Everest Base Camp',
            altitude: 5364,
            pressure: 0.506
        }
    },
    
    // Chart Configuration
    CHART_CONFIG: {
        MAX_DATA_POINTS: 50,
        TEMPERATURE_COLOR: '#e74c3c',
        PRESSURE_COLOR: '#3498db',
        BOILING_COLOR: '#f39c12',
        BACKGROUND_COLOR: 'rgba(255, 255, 255, 0.1)'
    },
    
    // Alarm Configuration
    ALARM_TYPES: {
        TEMPERATURE_THRESHOLD: 'temperature_threshold',
        TIME_BASED: 'time_based',
        BOILING_POINT: 'boiling_point',
        SENSOR_FAILURE: 'sensor_failure',
        CUSTOM_TIMER: 'custom_timer'
    },
    
    // Notification Settings
    NOTIFICATIONS: {
        ENABLED: true,
        SOUND_ENABLED: true,
        VIBRATION_ENABLED: true,
        TOAST_DURATION: 5000  // 5 seconds
    },
    
    // Simulation Mode (for demo without backend)
    SIMULATION_MODE: false,
    
    // Error Handling
    MAX_RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000,  // 1 second
    
    // Local Storage Keys
    STORAGE_KEYS: {
        SETTINGS: 'thermometer_settings',
        ALARM_CONFIG: 'thermometer_alarms',
        CHART_PREFERENCES: 'thermometer_chart_prefs'
    }
};

// Physics Calculations
const PHYSICS = {
    // Calculate boiling point based on atmospheric pressure
    calculateBoilingPoint(pressureAtm) {
        if (pressureAtm <= 0) return 0;
        
        // Simplified Antoine equation approximation
        const baseTemp = 100.0;  // °C at 1 atm
        const pressureFactor = 25.0;  // Temperature change per atm
        
        return baseTemp + pressureFactor * (pressureAtm - 1.0);
    },
    
    // Convert altitude to pressure
    altitudeToPressure(altitudeMeters) {
        if (altitudeMeters <= 0) return 1.0;
        
        // Simplified barometric formula
        const pressureDrop = altitudeMeters * 0.00012;
        return Math.max(0.3, 1.0 - pressureDrop);
    },
    
    // Convert pressure to altitude
    pressureToAltitude(pressureAtm) {
        if (pressureAtm >= 1.0) return 0.0;
        
        const altitude = (1.0 - pressureAtm) / 0.00012;
        return Math.max(0, altitude);
    },
    
    // Temperature conversion utilities
    celsiusToFahrenheit(celsius) {
        return (celsius * 9/5) + 32;
    },
    
    fahrenheitToCelsius(fahrenheit) {
        return (fahrenheit - 32) * 5/9;
    }
};

// Utility Functions
const UTILS = {
    // Format temperature display
    formatTemperature(temp, unit = 'C') {
        if (temp === null || temp === undefined) return '--';
        return `${temp.toFixed(1)}°${unit}`;
    },
    
    // Format pressure display
    formatPressure(pressure) {
        if (pressure === null || pressure === undefined) return '--';
        return `${pressure.toFixed(3)} atm`;
    },
    
    // Format time display
    formatTime(seconds) {
        if (seconds < 60) return `${seconds}s`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds}s`;
    },
    
    // Validate temperature input
    validateTemperature(temp) {
        const numTemp = parseFloat(temp);
        return !isNaN(numTemp) && 
               numTemp >= CONFIG.TEMP_MIN && 
               numTemp <= CONFIG.TEMP_MAX;
    },
    
    // Validate altitude input
    validateAltitude(altitude) {
        const numAltitude = parseFloat(altitude);
        return !isNaN(numAltitude) && 
               numAltitude >= 0 && 
               numAltitude <= 9000;
    },
    
    // Generate unique ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },
    
    // Debounce function for performance
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Local storage helpers
    saveToStorage(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
            return false;
        }
    },
    
    loadFromStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Failed to load from localStorage:', error);
            return defaultValue;
        }
    },
    
    // Date formatting
    formatDateTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    },
    
    formatTime12Hour(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
};

// Error Messages
const ERROR_MESSAGES = {
    CONNECTION_FAILED: 'Failed to connect to thermometer',
    SENSOR_ERROR: 'Sensor error detected',
    INVALID_TEMPERATURE: 'Please enter a valid temperature (10-120°C)',
    INVALID_ALTITUDE: 'Please enter a valid altitude (0-9000m)',
    SAVE_FAILED: 'Failed to save settings',
    ALARM_FAILED: 'Failed to configure alarm',
    UNKNOWN_ERROR: 'An unknown error occurred'
};

// Success Messages
const SUCCESS_MESSAGES = {
    SETTINGS_SAVED: 'Settings saved successfully',
    HEATING_STARTED: 'Heating started',
    HEATING_STOPPED: 'Heating stopped',
    TEMPERATURE_SET: 'Target temperature set',
    ALTITUDE_SET: 'Altitude set successfully',
    ALARM_CONFIGURED: 'Alarm configured successfully',
    ALARM_CLEARED: 'Alarms cleared',
    SENSORS_RESET: 'Sensors reset successfully'
};

// Export configuration for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CONFIG, PHYSICS, UTILS, ERROR_MESSAGES, SUCCESS_MESSAGES };
}

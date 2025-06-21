// API Communication Module for Smart Thermometer
class ThermometerAPI {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.retryCount = 0;
        this.maxRetries = CONFIG.MAX_RETRY_ATTEMPTS;
        this.retryDelay = CONFIG.RETRY_DELAY;
        this.isConnected = false;
        
        // Initialize connection check
        this.checkConnection();
    }
    
    // Generic API request method with retry logic
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout: 10000  // 10 seconds timeout
        };
        
        const requestOptions = { ...defaultOptions, ...options };
        
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await fetch(url, requestOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                this.isConnected = true;
                this.retryCount = 0;
                return data;
                
            } catch (error) {
                console.warn(`API request failed (attempt ${attempt + 1}/${this.maxRetries + 1}):`, error.message);
                
                if (attempt === this.maxRetries) {
                    this.isConnected = false;
                    throw new Error(`API request failed after ${this.maxRetries + 1} attempts: ${error.message}`);
                }
                
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * (attempt + 1)));
            }
        }
    }
    
    // Check API connection
    async checkConnection() {
        try {
            const response = await fetch(`${this.baseURL}/system/status`, {
                method: 'GET',
                timeout: 5000
            });
            this.isConnected = response.ok;
            return this.isConnected;
        } catch (error) {
            this.isConnected = false;
            return false;
        }
    }
    
    // Get current sensor data
    async getSensorData() {
        try {
            const data = await this.request('/sensor_data');
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                data: this.getSimulatedData() // Fallback to simulation
            };
        }
    }
    
    // Get historical sensor data
    async getHistoricalData() {
        try {
            const data = await this.request('/historical_data');
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                data: this.getSimulatedHistoricalData()
            };
        }
    }
    
    // Get chart data
    async getChartData() {
        try {
            const data = await this.request('/chart_data');
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                data: null
            };
        }
    }
    
    // Control heating element
    async controlHeating(heatingState) {
        try {
            const data = await this.request('/control/heating', {
                method: 'POST',
                body: JSON.stringify({ heating: heatingState })
            });
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    // Set target temperature
    async setTargetTemperature(temperature) {
        try {
            const data = await this.request('/control/target_temperature', {
                method: 'POST',
                body: JSON.stringify({ temperature: temperature })
            });
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    // Set altitude/location
    async setAltitude(altitude, preset = null) {
        try {
            const payload = preset ? { preset: preset } : { altitude: altitude };
            const data = await this.request('/control/altitude', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    // Get alarm status
    async getAlarms() {
        try {
            const data = await this.request('/alarms');
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                data: {
                    active_alarms_count: 0,
                    active_alarms: [],
                    alarm_configs: {}
                }
            };
        }
    }
      // Configure alarms (NEW EXCLUSIVE LOGIC)
    async configureAlarms(alarmConfig) {
        try {
            const data = await this.request('/alarms/configure', {
                method: 'POST',
                body: JSON.stringify(alarmConfig)
            });
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    // Configure specific alarm modes
    async configureTemperatureAlarm(threshold) {
        return this.configureAlarms({
            mode: 'temperature_only',
            threshold: threshold
        });
    }
    
    async configureTimeAlarm(duration) {
        return this.configureAlarms({
            mode: 'time_only',
            duration: duration
        });
    }
    
    async configureBoilingAlarm(offset = 0.0) {
        return this.configureAlarms({
            mode: 'boiling_only',
            offset: offset
        });
    }
    
    async configureBoilingThenTimeAlarm(duration, offset = 0.0) {
        return this.configureAlarms({
            mode: 'boiling_then_time',
            duration: duration,
            offset: offset
        });
    }
    
    // Clear all alarms
    async clearAlarms() {
        try {
            const data = await this.request('/alarms/clear', {
                method: 'POST'
            });
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    // Get system status
    async getSystemStatus() {
        try {
            const data = await this.request('/system/status');
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                data: {
                    sensors: {
                        temperature: { active: false, failed: true },
                        pressure: { active: false, failed: true }
                    },
                    mqtt: { connected: false },
                    data_collection: false
                }
            };
        }
    }
    
    // Get system settings
    async getSettings() {
        try {
            const data = await this.request('/settings');
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                data: {
                    temperature_threshold: 95,
                    time_threshold: 300,
                    update_interval: 2000
                }
            };
        }
    }

    // Update system settings
    async updateSettings(settings) {
        try {
            const data = await this.request('/settings', {
                method: 'POST',
                body: JSON.stringify(settings)
            });
            return {
                success: true,
                data: data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Start system
    async startSystem() {
        try {
            const data = await this.request('/system/start', {
                method: 'POST'
            });
            return {
                success: true,
                status: 'success',
                data: data
            };
        } catch (error) {
            return {
                success: false,
                status: 'error',
                error: error.message
            };
        }
    }

    // Stop system
    async stopSystem() {
        try {
            const data = await this.request('/system/stop', {
                method: 'POST'
            });
            return {
                success: true,
                status: 'success',
                data: data
            };
        } catch (error) {
            return {
                success: false,
                status: 'error',
                error: error.message
            };
        }
    }
    
    // Simulation data for offline mode
    getSimulatedData() {
        const now = new Date();
        const pressure = 1.0 + (Math.random() - 0.5) * 0.1; // 0.95 to 1.05 atm
        const temperature = 20 + Math.random() * 80; // 20 to 100°C
        const boilingPoint = PHYSICS.calculateBoilingPoint(pressure);
        
        return {
            temperature: {
                temperature: temperature,
                temperature_unit: 'celsius',
                is_heating: Math.random() > 0.7,
                target_temperature: 100,
                sensor_status: 'active',
                pressure_atm: pressure,
                device_id: CONFIG.DEVICE_ID,
                timestamp: now.toISOString()
            },
            pressure: {
                pressure: pressure,
                pressure_unit: 'atm',
                altitude_meters: 0,
                estimated_altitude: 0,
                sensor_status: 'active',
                device_id: CONFIG.DEVICE_ID,
                timestamp: now.toISOString()
            },
            boiling_point: boilingPoint,
            timestamp: now.toISOString()
        };
    }
    
    // Simulated historical data
    getSimulatedHistoricalData() {
        const dataPoints = [];
        const now = new Date();
        
        for (let i = 0; i < 20; i++) {
            const timestamp = new Date(now.getTime() - i * 10000); // 10 seconds intervals
            const pressure = 1.0 + (Math.random() - 0.5) * 0.05;
            const temperature = 20 + Math.random() * 80;
            const boilingPoint = PHYSICS.calculateBoilingPoint(pressure);
            
            dataPoints.unshift({
                timestamp: timestamp.toISOString(),
                temperature: temperature,
                pressure: pressure,
                boiling_point: boilingPoint
            });
        }
        
        return {
            timestamps: dataPoints.map(p => p.timestamp),
            temperatures: dataPoints.map(p => p.temperature),
            pressures: dataPoints.map(p => p.pressure),
            boiling_points: dataPoints.map(p => p.boiling_point)
        };
    }
    
    // Get connection status
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            baseURL: this.baseURL,
            retryCount: this.retryCount
        };
    }
}

// Quick Actions API
class QuickActionsAPI {
    constructor(mainAPI) {
        this.api = mainAPI;
    }
    
    // Quick action: Boil water (set to 100°C and start heating)
    async boilWater() {
        try {
            const tempResult = await this.api.setTargetTemperature(100);
            if (!tempResult.success) throw new Error(tempResult.error);
            
            const heatResult = await this.api.controlHeating(true);
            if (!heatResult.success) throw new Error(heatResult.error);
            
            return { success: true, message: 'Started boiling water at 100°C' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Quick action: Warm to specific temperature
    async warmTo(temperature) {
        try {
            const tempResult = await this.api.setTargetTemperature(temperature);
            if (!tempResult.success) throw new Error(tempResult.error);
            
            const heatResult = await this.api.controlHeating(true);
            if (!heatResult.success) throw new Error(heatResult.error);
            
            return { success: true, message: `Started heating to ${temperature}°C` };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Quick action: Emergency stop
    async emergencyStop() {
        try {
            const result = await this.api.controlHeating(false);
            if (!result.success) throw new Error(result.error);
            
            return { success: true, message: 'Emergency stop activated' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Quick action: Reset all systems
    async resetAll() {
        try {
            // Stop heating
            await this.api.controlHeating(false);
            
            // Clear alarms
            await this.api.clearAlarms();
            
            // Reset to room temperature target
            await this.api.setTargetTemperature(20);
            
            return { success: true, message: 'All systems reset' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// Initialize API instances
const thermometerAPI = new ThermometerAPI();
const quickActionsAPI = new QuickActionsAPI(thermometerAPI);

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ThermometerAPI, QuickActionsAPI };
}

// UI Management Module for Smart Thermometer
class ThermometerUI {
    constructor() {
        this.elements = this.initializeElements();
        this.currentData = null;
        this.alarmSound = null;
    }
    
    // Initialize DOM elements
    initializeElements() {
        return {
            // Status elements
            statusDot: document.getElementById('statusDot'),
            statusText: document.getElementById('statusText'),
            deviceId: document.getElementById('deviceId'),
            
            // Sensor cards and values
            temperatureCard: document.getElementById('temperatureCard'),
            temperatureValue: document.getElementById('temperatureValue'),
            targetTemp: document.getElementById('targetTemp'),
            heatingStatus: document.getElementById('heatingStatus'),
            
            pressureValue: document.getElementById('pressureValue'),
            altitudeValue: document.getElementById('altitudeValue'),
            
            boilingCard: document.getElementById('boilingCard'),
            boilingValue: document.getElementById('boilingValue'),
            boilingStatus: document.getElementById('boilingStatus'),
            
            alarmCard: document.getElementById('alarmCard'),
            alarmCount: document.getElementById('alarmCount'),
            alarmsList: document.getElementById('alarmsList'),
            
            // Controls
            targetTempInput: document.getElementById('targetTempInput'),
            heatingBtn: document.getElementById('heatingBtn'),
            locationPreset: document.getElementById('locationPreset'),
            customAltitude: document.getElementById('customAltitude'),
            
            // Alarm configuration
            tempAlarmEnabled: document.getElementById('tempAlarmEnabled'),
            tempAlarmThreshold: document.getElementById('tempAlarmThreshold'),
            timeAlarmEnabled: document.getElementById('timeAlarmEnabled'),
            timeAlarmDuration: document.getElementById('timeAlarmDuration'),
            boilingAlarmEnabled: document.getElementById('boilingAlarmEnabled'),
            
            // Containers
            toastContainer: document.getElementById('toastContainer'),
            loadingOverlay: document.getElementById('loadingOverlay')
        };
    }
    
    // Update connection status
    updateConnectionStatus(isConnected, statusText = '') {
        if (isConnected) {
            this.elements.statusDot.className = 'status-dot online';
            this.elements.statusText.textContent = statusText || 'Connected';
        } else {
            this.elements.statusDot.className = 'status-dot offline';
            this.elements.statusText.textContent = statusText || 'Offline';
        }
    }
    
    // Update sensor data display
    updateSensorData(data) {
        this.currentData = data;
        
        if (data.temperature && data.temperature.temperature !== null) {
            this.updateTemperatureDisplay(data.temperature);
        } else {
            this.showSensorError('temperature');
        }
        
        if (data.pressure && data.pressure.pressure !== null) {
            this.updatePressureDisplay(data.pressure);
        } else {
            this.showSensorError('pressure');
        }
        
        if (data.boiling_point !== null) {
            this.updateBoilingPointDisplay(data.boiling_point, data.temperature);
        }
        
        this.updateDeviceInfo();
    }
    
    // Update temperature display
    updateTemperatureDisplay(tempData) {
        const temp = tempData.temperature;
        const isHeating = tempData.is_heating;
        const targetTemp = tempData.target_temperature;
        
        // Update values
        this.elements.temperatureValue.textContent = UTILS.formatTemperature(temp);
        this.elements.targetTemp.textContent = UTILS.formatTemperature(targetTemp);
        
        // Update heating status
        if (isHeating) {
            this.elements.heatingStatus.textContent = 'Heating';
            this.elements.heatingStatus.className = 'heating-status active';
            this.elements.temperatureCard.classList.add('heating');
            
            this.elements.heatingBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Heating';
            this.elements.heatingBtn.className = 'btn-heating active';
        } else {
            this.elements.heatingStatus.textContent = 'Off';
            this.elements.heatingStatus.className = 'heating-status';
            this.elements.temperatureCard.classList.remove('heating');
            
            this.elements.heatingBtn.innerHTML = '<i class="fas fa-fire"></i> Start Heating';
            this.elements.heatingBtn.className = 'btn-heating';
        }
        
        // Remove error state
        this.elements.temperatureCard.classList.remove('alarm');
    }
    
    // Update pressure display
    updatePressureDisplay(pressureData) {
        const pressure = pressureData.pressure;
        const altitude = pressureData.altitude_meters;
        
        this.elements.pressureValue.textContent = UTILS.formatPressure(pressure);
        this.elements.altitudeValue.textContent = altitude ? `${altitude} m` : '-- m';
    }
    
    // Update boiling point display
    updateBoilingPointDisplay(boilingPoint, tempData) {
        this.elements.boilingValue.textContent = UTILS.formatTemperature(boilingPoint);
        
        if (tempData && tempData.temperature !== null) {
            const currentTemp = tempData.temperature;
            const isBoiling = currentTemp >= (boilingPoint - 1);
            
            if (isBoiling) {
                this.elements.boilingStatus.textContent = 'BOILING!';
                this.elements.boilingStatus.className = 'boiling-status boiling';
                this.elements.boilingCard.classList.add('boiling');
            } else {
                this.elements.boilingStatus.textContent = 'Not Boiling';
                this.elements.boilingStatus.className = 'boiling-status';
                this.elements.boilingCard.classList.remove('boiling');
            }
        }
    }
    
    // Show sensor error
    showSensorError(sensorType) {
        if (sensorType === 'temperature') {
            this.elements.temperatureValue.textContent = 'ERROR';
            this.elements.temperatureCard.classList.add('alarm');
        } else if (sensorType === 'pressure') {
            this.elements.pressureValue.textContent = 'ERROR';
        }
    }
    
    // Update device information
    updateDeviceInfo() {
        this.elements.deviceId.textContent = CONFIG.DEVICE_ID;
    }
    
    // Update alarms display
    updateAlarms(alarmData) {
        const activeAlarms = alarmData.active_alarms || [];
        const alarmCount = alarmData.active_alarms_count || 0;
        
        // Update alarm count
        this.elements.alarmCount.textContent = alarmCount;
        
        // Update alarms list
        if (alarmCount > 0) {
            this.elements.alarmCard.classList.add('alarm');
            this.renderAlarmsList(activeAlarms);
        } else {
            this.elements.alarmCard.classList.remove('alarm');
            this.elements.alarmsList.innerHTML = '<div class="no-alarms">No active alarms</div>';
        }
    }
    
    // Render alarms list
    renderAlarmsList(alarms) {
        const alarmsHTML = alarms.map(alarm => `
            <div class="alarm-notification ${alarm.priority === 'CRITICAL' ? 'critical' : ''}">
                <div class="alarm-info">
                    <h4>${alarm.type.replace('_', ' ').toUpperCase()}</h4>
                    <p>${alarm.message}</p>
                    <small>${UTILS.formatDateTime(alarm.datetime)}</small>
                </div>
                <div class="alarm-actions">
                    <button class="btn-small btn-primary" onclick="acknowledgeAlarm('${alarm.id}')">
                        OK
                    </button>
                </div>
            </div>
        `).join('');
        
        this.elements.alarmsList.innerHTML = alarmsHTML;
    }
    
    // Show toast notification
    showToast(message, type = 'info', duration = CONFIG.NOTIFICATIONS.TOAST_DURATION) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
            </div>
            <div class="toast-content">
                <p>${message}</p>
            </div>
        `;
        
        this.elements.toastContainer.appendChild(toast);
        
        // Auto remove toast
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, duration);
        
        // Play notification sound
        if (CONFIG.NOTIFICATIONS.SOUND_ENABLED && type === 'error') {
            this.playNotificationSound();
        }
    }
    
    // Get toast icon based on type
    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    // Show/hide loading overlay
    showLoading(show = true) {
        if (show) {
            this.elements.loadingOverlay.classList.add('show');
        } else {
            this.elements.loadingOverlay.classList.remove('show');
        }
    }
    
    // Update form values from current settings
    updateFormValues(settings = {}) {
        if (settings.targetTemperature) {
            this.elements.targetTempInput.value = settings.targetTemperature;
        }
        
        if (settings.alarms) {
            if (settings.alarms.temperature_threshold !== undefined) {
                this.elements.tempAlarmThreshold.value = settings.alarms.temperature_threshold;
                this.elements.tempAlarmEnabled.checked = settings.alarms.temperature_enabled || false;
            }
            
            if (settings.alarms.time_duration !== undefined) {
                this.elements.timeAlarmDuration.value = Math.floor(settings.alarms.time_duration / 60);
                this.elements.timeAlarmEnabled.checked = settings.alarms.time_enabled || false;
            }
            
            if (settings.alarms.boiling_enabled !== undefined) {
                this.elements.boilingAlarmEnabled.checked = settings.alarms.boiling_enabled;
            }
        }
    }
    
    // Get form values for settings
    getFormValues() {
        return {
            targetTemperature: parseFloat(this.elements.targetTempInput.value),
            customAltitude: parseFloat(this.elements.customAltitude.value),
            locationPreset: this.elements.locationPreset.value,
            alarms: {
                temperature_threshold: parseFloat(this.elements.tempAlarmThreshold.value),
                temperature_enabled: this.elements.tempAlarmEnabled.checked,
                time_duration: parseInt(this.elements.timeAlarmDuration.value) * 60,
                time_enabled: this.elements.timeAlarmEnabled.checked,
                boiling_enabled: this.elements.boilingAlarmEnabled.checked
            }
        };
    }
    
    // Validate form inputs
    validateInputs() {
        const values = this.getFormValues();
        const errors = [];
        
        if (!UTILS.validateTemperature(values.targetTemperature)) {
            errors.push('Invalid target temperature');
        }
        
        if (!UTILS.validateTemperature(values.alarms.temperature_threshold)) {
            errors.push('Invalid alarm temperature threshold');
        }
        
        if (!UTILS.validateAltitude(values.customAltitude)) {
            errors.push('Invalid altitude value');
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }
    
    // Play notification sound
    playNotificationSound() {
        if (!CONFIG.NOTIFICATIONS.SOUND_ENABLED) return;
        
        try {
            // Create audio context for web audio API
            if (!this.alarmSound) {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = 800; // High pitch beep
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0, audioContext.currentTime);
                gainNode.gain.linearRampToValueAtTime(0.1, audioContext.currentTime + 0.01);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.5);
            }
        } catch (error) {
            console.warn('Could not play notification sound:', error);
        }
    }
    
    // Trigger vibration (mobile devices)
    triggerVibration(pattern = [200, 100, 200]) {
        if (CONFIG.NOTIFICATIONS.VIBRATION_ENABLED && 'vibrate' in navigator) {
            navigator.vibrate(pattern);
        }
    }
    
    // Animation helpers
    highlightElement(element, duration = 2000) {
        element.style.animation = `pulse ${duration}ms ease-in-out`;
        setTimeout(() => {
            element.style.animation = '';
        }, duration);
    }
    
    // Responsive design helpers
    isMobile() {
        return window.innerWidth <= 768;
    }
    
    // Update UI for mobile/desktop
    updateResponsiveLayout() {
        const isMobile = this.isMobile();
        document.body.classList.toggle('mobile-layout', isMobile);
    }
    
    // Initialize UI event listeners
    initializeEventListeners() {
        // Window resize handler
        window.addEventListener('resize', UTILS.debounce(() => {
            this.updateResponsiveLayout();
        }, 250));
        
        // Initial responsive layout
        this.updateResponsiveLayout();
    }
      // Update sensor readings (simplified version for frontend)
    updateSensorReadings(data) {
        // Handle temperature data
        if (data.temperature && data.temperature.temperature !== undefined) {
            this.elements.temperatureValue.textContent = UTILS.formatTemperature(data.temperature.temperature);
        }
        
        // Handle pressure data  
        if (data.pressure && data.pressure.pressure !== undefined) {
            this.elements.pressureValue.textContent = UTILS.formatPressure(data.pressure.pressure);
        }
        
        // Handle boiling point
        if (data.boiling_point !== undefined) {
            this.elements.boilingValue.textContent = UTILS.formatTemperature(data.boiling_point);
        }
        
        // Handle altitude (if present)
        if (data.altitude !== undefined) {
            this.elements.altitudeValue.textContent = `${data.altitude} m`;
        }
    }
    
    // Update system status
    updateSystemStatus(status) {
        const statusElement = document.getElementById('systemStatus');
        if (statusElement) {
            statusElement.textContent = status.toUpperCase();
            statusElement.className = `system-status ${status}`;
        }
        
        // Update start/stop button
        const startStopBtn = document.getElementById('startStopBtn');
        if (startStopBtn) {
            if (status === 'running') {
                startStopBtn.textContent = 'Stop System';
                startStopBtn.className = 'btn-danger';
            } else {
                startStopBtn.textContent = 'Start System';
                startStopBtn.className = 'btn-primary';
            }
        }
    }
    
    // Update alarms display
    updateAlarmsDisplay(alarms) {
        const alarmsList = document.getElementById('alarmsList');
        if (!alarmsList) return;
        
        if (alarms.length === 0) {
            alarmsList.innerHTML = '<div class="no-alarms">No active alarms</div>';
            return;
        }
        
        const alarmsHTML = alarms.map(alarm => `
            <div class="alarm-item ${alarm.type}">
                <div class="alarm-content">
                    <strong>${alarm.type.replace('_', ' ').toUpperCase()}</strong>
                    <p>${alarm.message}</p>
                    <small>${new Date(alarm.timestamp * 1000).toLocaleString()}</small>
                </div>
            </div>
        `).join('');
        
        alarmsList.innerHTML = alarmsHTML;
    }
    
    // Update settings form
    updateSettingsForm(settings) {
        const form = document.getElementById('settingsForm');
        if (!form) return;
        
        Object.keys(settings).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = settings[key];
            }
        });
    }
    
    // Show notification/toast message
    showNotification(message, type = 'info', duration = 5000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to toast container or create one
        let container = this.elements.toastContainer;
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
}

// Initialize UI instance
const thermometerUI = new ThermometerUI();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ThermometerUI };
}

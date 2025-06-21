/**
 * Main Application Logic - Smart Thermometer Dashboard
 */
class SmartThermometerApp {    constructor() {
        // Initialize modules
        this.api = new ThermometerAPI();
        this.ui = new ThermometerUI();
        this.charts = new ChartsManager();
        
        // Application state
        this.isRunning = false;
        this.updateInterval = null;
        this.sensorData = {};
        this.alarms = [];
        this.settings = {
            temperature_threshold: 95,
            time_threshold: 300,
            update_interval: 2000
        };

        this.init();
    }

    async init() {
        console.log('Initializing Smart Thermometer Dashboard...');
        
        // Load initial data
        await this.loadSettings();
        await this.loadAlarms();
        
        // Setup event listeners
        this.setupEventListeners();
          // Update UI with initial state
        this.ui.updateConnectionStatus(false);
        this.ui.updateSystemStatus('stopped');
        this.ui.updateDeviceInfo();
        
        // Start data polling
        this.startPolling();
        
        console.log('Dashboard initialized successfully');
    }    async loadSettings() {
        try {
            const settingsResponse = await this.api.getSettings();
            if (settingsResponse && settingsResponse.success) {
                this.settings = { ...this.settings, ...settingsResponse.data };
                this.ui.updateSettingsForm(this.settings);
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.ui.showNotification('Failed to load settings', 'error');
        }
    }async loadAlarms() {
        try {
            const alarmsResponse = await this.api.getAlarms();
            if (alarmsResponse && alarmsResponse.success) {
                this.alarms = alarmsResponse.data.active_alarms || [];
                this.ui.updateAlarmsDisplay(this.alarms);
            }
        } catch (error) {
            console.error('Failed to load alarms:', error);
        }
    }

    setupEventListeners() {
        // Start/Stop button
        const startStopBtn = document.getElementById('startStopBtn');
        if (startStopBtn) {
            startStopBtn.addEventListener('click', () => this.toggleSystem());
        }

        // Settings form
        const settingsForm = document.getElementById('settingsForm');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }

        // Clear alarms button
        const clearAlarmsBtn = document.getElementById('clearAlarmsBtn');
        if (clearAlarmsBtn) {
            clearAlarmsBtn.addEventListener('click', () => this.clearAlarms());
        }

        // Clear charts button
        const clearChartsBtn = document.getElementById('clearChartsBtn');
        if (clearChartsBtn) {
            clearChartsBtn.addEventListener('click', () => this.clearCharts());
        }

        // Window resize
        window.addEventListener('resize', () => {
            this.charts.resizeCharts();
        });

        // Tab switching
        const tabButtons = document.querySelectorAll('.tab-btn');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabId = e.target.dataset.tab;
                this.switchTab(tabId);
            });
        });
    }

    async toggleSystem() {
        if (this.isRunning) {
            await this.stopSystem();
        } else {
            await this.startSystem();
        }
    }

    async startSystem() {
        try {
            const result = await this.api.startSystem();
            if (result && result.status === 'success') {
                this.isRunning = true;
                this.ui.updateSystemStatus('running');
                this.ui.showNotification('System started successfully', 'success');
                
                // Start more frequent polling when system is running
                this.startPolling(1000);
            } else {
                throw new Error(result?.message || 'Failed to start system');
            }
        } catch (error) {
            console.error('Failed to start system:', error);
            this.ui.showNotification('Failed to start system: ' + error.message, 'error');
        }
    }

    async stopSystem() {
        try {
            const result = await this.api.stopSystem();
            if (result && result.status === 'success') {
                this.isRunning = false;
                this.ui.updateSystemStatus('stopped');
                this.ui.showNotification('System stopped successfully', 'success');
                
                // Slower polling when stopped
                this.startPolling(5000);
            } else {
                throw new Error(result?.message || 'Failed to stop system');
            }
        } catch (error) {
            console.error('Failed to stop system:', error);
            this.ui.showNotification('Failed to stop system: ' + error.message, 'error');
        }
    }

    async saveSettings() {
        try {
            // Get form data
            const formData = new FormData(document.getElementById('settingsForm'));
            const newSettings = {
                temperature_threshold: parseFloat(formData.get('temperature_threshold')) || this.settings.temperature_threshold,
                time_threshold: parseInt(formData.get('time_threshold')) || this.settings.time_threshold,
                update_interval: parseInt(formData.get('update_interval')) || this.settings.update_interval
            };

            const result = await this.api.updateSettings(newSettings);
            if (result && result.status === 'success') {
                this.settings = { ...this.settings, ...newSettings };
                this.ui.showNotification('Settings saved successfully', 'success');
                
                // Update polling interval if changed
                if (newSettings.update_interval !== this.settings.update_interval) {
                    this.startPolling(newSettings.update_interval);
                }
            } else {
                throw new Error(result?.message || 'Failed to save settings');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            this.ui.showNotification('Failed to save settings: ' + error.message, 'error');
        }
    }    async clearAlarms() {
        try {
            const result = await this.api.clearAlarms();
            console.log('Clear alarms result:', result); // Debug log
            
            if (result && result.success) {
                // Update local state
                this.alarms = [];
                this.ui.updateAlarmsDisplay(this.alarms);
                this.ui.showNotification('Alarms cleared successfully', 'success');
                
                // Force refresh alarm status
                await this.loadAlarms();
            } else {
                throw new Error(result?.error || 'Failed to clear alarms');
            }
        } catch (error) {
            console.error('Failed to clear alarms:', error);
            this.ui.showNotification('Failed to clear alarms: ' + error.message, 'error');
        }
    }

    clearCharts() {
        this.charts.clearCharts();
        this.ui.showNotification('Charts cleared', 'info');
    }

    switchTab(tabId) {
        // Hide all tabs
        const tabs = document.querySelectorAll('.tab-content');
        tabs.forEach(tab => tab.style.display = 'none');
        
        // Remove active class from all buttons
        const buttons = document.querySelectorAll('.tab-btn');
        buttons.forEach(btn => btn.classList.remove('active'));
        
        // Show selected tab
        const selectedTab = document.getElementById(tabId + 'Tab');
        if (selectedTab) {
            selectedTab.style.display = 'block';
        }
        
        // Add active class to selected button
        const selectedBtn = document.querySelector(`[data-tab="${tabId}"]`);
        if (selectedBtn) {
            selectedBtn.classList.add('active');
        }

        // Resize charts when switching to dashboard tab
        if (tabId === 'dashboard') {
            setTimeout(() => this.charts.resizeCharts(), 100);
        }
    }

    startPolling(interval = null) {
        // Clear existing interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // Use provided interval or default
        const pollInterval = interval || this.settings.update_interval || 2000;

        // Start new polling
        this.updateInterval = setInterval(() => {
            this.updateData();
        }, pollInterval);

        // Initial update
        this.updateData();
    }    async updateData() {
        try {
            // Get sensor data
            const sensorResponse = await this.api.getSensorData();
            if (sensorResponse && sensorResponse.success) {
                this.sensorData = sensorResponse.data;
                this.ui.updateSensorReadings(sensorResponse.data);
                this.charts.updateCharts(sensorResponse.data);
                this.ui.updateConnectionStatus(true);
            }

            // Get alarms
            const alarmsResponse = await this.api.getAlarms();
            if (alarmsResponse && alarmsResponse.success) {
                const alarms = alarmsResponse.data || [];
                if (alarms.length !== this.alarms.length) {
                    this.alarms = alarms;
                    this.ui.updateAlarmsDisplay(this.alarms);
                    
                    // Show notification for new alarms
                    if (alarms.length > 0) {
                        const latestAlarm = alarms[alarms.length - 1];
                        this.ui.showNotification(`New alarm: ${latestAlarm.message}`, 'warning');
                    }
                }
            }

        } catch (error) {
            console.error('Failed to update data:', error);
            this.ui.updateConnectionStatus(false);
        }
    }

    // Cleanup method
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded. Please include Chart.js in your HTML.');
        return;
    }

    // Initialize the app
    window.app = new SmartThermometerApp();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.app) {
        window.app.destroy();
    }
});

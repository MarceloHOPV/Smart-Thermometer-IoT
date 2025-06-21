/**
 * Utility Functions for Smart Thermometer Dashboard
 */
const UTILS = {
    // Format temperature with appropriate precision and unit
    formatTemperature(temp) {
        if (temp === null || temp === undefined || isNaN(temp)) {
            return '--°C';
        }
        return `${parseFloat(temp).toFixed(1)}°C`;
    },

    // Format pressure with appropriate precision and unit
    formatPressure(pressure) {
        if (pressure === null || pressure === undefined || isNaN(pressure)) {
            return '--atm';
        }
        return `${parseFloat(pressure).toFixed(3)} atm`;
    },

    // Format time duration
    formatDuration(seconds) {
        if (seconds === null || seconds === undefined || isNaN(seconds)) {
            return '--';
        }
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    },

    // Format percentage
    formatPercentage(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '--%';
        }
        return `${parseFloat(value).toFixed(1)}%`;
    },

    // Format altitude
    formatAltitude(altitude) {
        if (altitude === null || altitude === undefined || isNaN(altitude)) {
            return '--m';
        }
        return `${parseInt(altitude)} m`;
    },

    // Get status color class
    getStatusColor(status) {
        const statusColors = {
            'connected': 'success',
            'online': 'success',
            'running': 'success',
            'disconnected': 'danger',
            'offline': 'danger',
            'stopped': 'secondary',
            'error': 'danger',
            'warning': 'warning',
            'boiling': 'warning',
            'heating': 'info',
            'cooling': 'info'
        };
        return statusColors[status] || 'secondary';
    },

    // Get alarm severity class
    getAlarmSeverity(type) {
        const severityMap = {
            'temperature': 'danger',
            'time': 'warning',
            'boiling': 'info',
            'boiling_then_time': 'warning'
        };
        return severityMap[type] || 'secondary';
    },

    // Debounce function
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

    // Throttle function
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Check if value is in range
    isInRange(value, min, max) {
        return value >= min && value <= max;
    },

    // Get temperature status based on thresholds
    getTemperatureStatus(temp, target = null, boilingPoint = null) {
        if (temp === null || temp === undefined) return 'unknown';
        
        if (boilingPoint && temp >= boilingPoint - 1) {
            return 'boiling';
        }
        
        if (target) {
            const diff = Math.abs(temp - target);
            if (diff <= 2) return 'at_target';
            if (temp < target) return 'heating';
            if (temp > target) return 'cooling';
        }
        
        return 'normal';
    },

    // Get boiling status
    getBoilingStatus(temp, boilingPoint) {
        if (!temp || !boilingPoint) return 'unknown';
        
        const diff = boilingPoint - temp;
        if (diff <= 0) return 'boiling';
        if (diff <= 5) return 'near_boiling';
        if (diff <= 20) return 'heating';
        return 'cold';
    },

    // Calculate boiling point from pressure (simplified)
    calculateBoilingPoint(pressure) {
        // Simplified Antoine equation for water
        // More accurate would use: T = 373.15 * (1 - 0.0289 * (1 - P))
        if (!pressure || pressure <= 0) return 100;
        
        const baseTemp = 100; // °C at 1 atm
        const adjustment = (pressure - 1) * 28.9; // Rough approximation
        return baseTemp + adjustment;
    },

    // Calculate pressure from altitude (simplified)
    calculatePressureFromAltitude(altitude) {
        // Barometric formula approximation
        if (!altitude || altitude < 0) return 1.0;
        
        return Math.exp(-altitude / 8400); // Simplified exponential decay
    },

    // Generate timestamp
    getTimestamp() {
        return new Date().toISOString();
    },

    // Format timestamp for display
    formatTimestamp(timestamp, includeDate = false) {
        const date = new Date(timestamp);
        const timeStr = date.toLocaleTimeString();
        
        if (includeDate) {
            const dateStr = date.toLocaleDateString();
            return `${dateStr} ${timeStr}`;
        }
        
        return timeStr;
    },

    // Generate random ID
    generateId() {
        return Math.random().toString(36).substr(2, 9);
    },

    // Copy text to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return true;
        }
    },

    // Validate temperature input
    validateTemperature(temp, min = -50, max = 200) {
        const num = parseFloat(temp);
        return !isNaN(num) && num >= min && num <= max;
    },

    // Validate pressure input
    validatePressure(pressure, min = 0.1, max = 2.0) {
        const num = parseFloat(pressure);
        return !isNaN(num) && num >= min && num <= max;
    },

    // Validate time duration
    validateDuration(duration, min = 1, max = 7200) {
        const num = parseInt(duration);
        return !isNaN(num) && num >= min && num <= max;
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UTILS;
}

/**
 * Charts Module - Real-time temperature and pressure visualization
 */
class ChartsManager {
    constructor() {
        this.temperatureChart = null;
        this.pressureChart = null;
        this.temperatureData = [];
        this.pressureData = [];
        this.maxDataPoints = 50;
        
        this.initCharts();
    }

    initCharts() {
        this.initTemperatureChart();
        this.initPressureChart();
    }

    initTemperatureChart() {
        const ctx = document.getElementById('temperatureChart');
        if (!ctx) return;

        this.temperatureChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: CONFIG.colors.temperature,
                    backgroundColor: CONFIG.colors.temperature + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }, {
                    label: 'Boiling Point (°C)',
                    data: [],
                    borderColor: CONFIG.colors.alarm,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        },
                        min: 0,
                        max: 120
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    }

    initPressureChart() {
        const ctx = document.getElementById('pressureChart');
        if (!ctx) return;

        this.pressureChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Pressure (hPa)',
                    data: [],
                    borderColor: CONFIG.colors.pressure,
                    backgroundColor: CONFIG.colors.pressure + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Pressure (hPa)'
                        },
                        min: 800,
                        max: 1100
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    }

    updateTemperatureChart(temperature, boilingPoint) {
        if (!this.temperatureChart) return;

        const now = new Date().toLocaleTimeString();
        
        // Add new data point
        this.temperatureChart.data.labels.push(now);
        this.temperatureChart.data.datasets[0].data.push(temperature);
        this.temperatureChart.data.datasets[1].data.push(boilingPoint);

        // Keep only last N data points
        if (this.temperatureChart.data.labels.length > this.maxDataPoints) {
            this.temperatureChart.data.labels.shift();
            this.temperatureChart.data.datasets[0].data.shift();
            this.temperatureChart.data.datasets[1].data.shift();
        }

        this.temperatureChart.update('none');
    }

    updatePressureChart(pressure) {
        if (!this.pressureChart) return;

        const now = new Date().toLocaleTimeString();
        
        // Add new data point
        this.pressureChart.data.labels.push(now);
        this.pressureChart.data.datasets[0].data.push(pressure);

        // Keep only last N data points
        if (this.pressureChart.data.labels.length > this.maxDataPoints) {
            this.pressureChart.data.labels.shift();
            this.pressureChart.data.datasets[0].data.shift();
        }

        this.pressureChart.update('none');
    }

    updateCharts(sensorData) {
        if (sensorData.temperature !== undefined && sensorData.boiling_point !== undefined) {
            this.updateTemperatureChart(sensorData.temperature, sensorData.boiling_point);
        }
        
        if (sensorData.pressure !== undefined) {
            this.updatePressureChart(sensorData.pressure);
        }
    }

    clearCharts() {
        if (this.temperatureChart) {
            this.temperatureChart.data.labels = [];
            this.temperatureChart.data.datasets[0].data = [];
            this.temperatureChart.data.datasets[1].data = [];
            this.temperatureChart.update();
        }

        if (this.pressureChart) {
            this.pressureChart.data.labels = [];
            this.pressureChart.data.datasets[0].data = [];
            this.pressureChart.update();
        }
    }

    resizeCharts() {
        if (this.temperatureChart) {
            this.temperatureChart.resize();
        }
        if (this.pressureChart) {
            this.pressureChart.resize();
        }
    }
}

// Export for use in other modules
window.ChartsManager = ChartsManager;

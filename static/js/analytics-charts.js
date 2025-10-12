// static/js/analytics-charts.js

class AnalyticsCharts {
    constructor() {
        this.revenueChart = null;
        this.occupancyChart = null;
        this.init();
    }

    init() {
        this.initializeRevenueChart();
        this.initializeOccupancyChart();
        this.loadChartData();
    }

    initializeRevenueChart() {
        const ctx = document.getElementById('revenueChart').getContext('2d');
        this.revenueChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Daily Revenue (₹)',
                    data: [],
                    borderColor: '#F59E0B',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue Overview - Last 30 Days',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45
                        }
                    }
                }
            }
        });
    }

    initializeOccupancyChart() {
        const ctx = document.getElementById('occupancyChart').getContext('2d');
        this.occupancyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Occupancy Rate (%)',
                    data: [],
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Occupancy Trend - Last 30 Days',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45
                        }
                    }
                }
            }
        });
    }

    async loadChartData() {
        try {
            const response = await fetch('/admin/analytics/chart-data');
            const data = await response.json();
            
            if (data.success) {
                this.updateRevenueChart(data.revenue_data);
                this.updateOccupancyChart(data.occupancy_data);
            }
        } catch (error) {
            console.error('Error loading chart data:', error);
            this.loadSampleData();
        }
    }

    updateRevenueChart(data) {
        this.revenueChart.data.labels = data.labels;
        this.revenueChart.data.datasets[0].data = data.values;
        this.revenueChart.update();
    }

    updateOccupancyChart(data) {
        this.occupancyChart.data.labels = data.labels;
        this.occupancyChart.data.datasets[0].data = data.values;
        this.occupancyChart.update();
    }

    loadSampleData() {
        // Fallback sample data if API fails
        const sampleLabels = this.generateLast30DaysLabels();
        
        const sampleRevenueData = {
            labels: sampleLabels,
            values: sampleLabels.map(() => Math.floor(Math.random() * 50000) + 10000)
        };
        
        const sampleOccupancyData = {
            labels: sampleLabels,
            values: sampleLabels.map(() => Math.floor(Math.random() * 50) + 50)
        };
        
        this.updateRevenueChart(sampleRevenueData);
        this.updateOccupancyChart(sampleOccupancyData);
    }

    generateLast30DaysLabels() {
        const labels = [];
        for (let i = 29; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        }
        return labels;
    }

    // Method to export chart as image
    exportChartAsImage(chartId, filename) {
        const chartCanvas = document.getElementById(chartId);
        const image = chartCanvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.href = image;
        link.download = filename;
        link.click();
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.analyticsCharts = new AnalyticsCharts();
    
    // Add export functionality
    document.getElementById('exportRevenueChart')?.addEventListener('click', function() {
        window.analyticsCharts.exportChartAsImage('revenueChart', 'revenue-chart.png');
    });
    
    document.getElementById('exportOccupancyChart')?.addEventListener('click', function() {
        window.analyticsCharts.exportChartAsImage('occupancyChart', 'occupancy-chart.png');
    });
});
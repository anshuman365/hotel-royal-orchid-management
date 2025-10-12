// Admin dashboard charts and analytics

class AdminCharts {
    constructor() {
        this.charts = {};
        this.init();
    }
    
    init() {
        this.loadRevenueChart();
        this.loadOccupancyChart();
        this.loadBookingTrendsChart();
        this.loadRoomPerformanceChart();
    }
    
    loadRevenueChart() {
        const ctx = document.getElementById('revenue-chart');
        if (!ctx) return;
        
        // Sample data - in real app, this would come from API
        const data = {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Revenue',
                data: [120000, 150000, 180000, 140000, 200000, 220000],
                backgroundColor: 'rgba(217, 119, 6, 0.2)',
                borderColor: 'rgba(217, 119, 6, 1)',
                borderWidth: 2,
                tension: 0.4
            }]
        };
        
        this.charts.revenue = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Monthly Revenue'
                    },
                    legend: {
                        display: false
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
                    }
                }
            }
        });
    }
    
    loadOccupancyChart() {
        const ctx = document.getElementById('occupancy-chart');
        if (!ctx) return;
        
        const data = {
            labels: ['Standard', 'Deluxe', 'Suite', 'Executive'],
            datasets: [{
                data: [75, 85, 60, 90],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(217, 119, 6, 0.8)',
                    'rgba(139, 92, 246, 0.8)'
                ],
                borderWidth: 2
            }]
        };
        
        this.charts.occupancy = new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Occupancy Rate by Room Type'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    loadBookingTrendsChart() {
        const ctx = document.getElementById('booking-trends-chart');
        if (!ctx) return;
        
        const data = {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Bookings',
                data: [12, 19, 8, 15, 22, 18, 25],
                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2
            }, {
                label: 'Check-ins',
                data: [8, 12, 6, 10, 15, 20, 18],
                backgroundColor: 'rgba(34, 197, 94, 0.5)',
                borderColor: 'rgba(34, 197, 94, 1)',
                borderWidth: 2
            }]
        };
        
        this.charts.bookingTrends = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Weekly Booking Trends'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    loadRoomPerformanceChart() {
        const ctx = document.getElementById('room-performance-chart');
        if (!ctx) return;
        
        const data = {
            labels: ['Standard', 'Deluxe', 'Suite', 'Executive'],
            datasets: [{
                label: 'Revenue (₹)',
                data: [450000, 620000, 380000, 550000],
                backgroundColor: 'rgba(217, 119, 6, 0.8)',
                borderColor: 'rgba(217, 119, 6, 1)',
                borderWidth: 2
            }, {
                label: 'Bookings',
                data: [45, 32, 18, 28],
                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2,
                type: 'line',
                yAxisID: 'y1'
            }]
        };
        
        this.charts.roomPerformance = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Room Performance'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + (value / 1000) + 'k';
                            }
                        }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
    
    // Update charts with new data
    updateCharts(timeRange = '30') {
        // In a real application, this would fetch new data from the API
        // based on the selected time range
        
        const endpoints = {
            '7': '/api/analytics/revenue?days=7',
            '30': '/api/analytics/revenue?days=30',
            '90': '/api/analytics/revenue?days=90',
            '365': '/api/analytics/revenue?days=365'
        };
        
        // Simulate API call
        this.simulateDataUpdate(timeRange);
    }
    
    simulateDataUpdate(timeRange) {
        // This is a simulation - in real app, you'd make API calls
        console.log(`Updating charts for ${timeRange} days`);
        
        // Show loading state
        this.showChartLoading();
        
        // Simulate API delay
        setTimeout(() => {
            this.hideChartLoading();
            
            // Update charts with new data
            if (this.charts.revenue) {
                // Update revenue chart data here
            }
            
            if (this.charts.occupancy) {
                // Update occupancy chart data here
            }
            
            showNotification('Charts updated successfully', 'success');
        }, 1000);
    }
    
    showChartLoading() {
        document.querySelectorAll('.chart-container').forEach(container => {
            const overlay = document.createElement('div');
            overlay.className = 'chart-loading-overlay absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center';
            overlay.innerHTML = '<div class="spinner"></div>';
            container.style.position = 'relative';
            container.appendChild(overlay);
        });
    }
    
    hideChartLoading() {
        document.querySelectorAll('.chart-loading-overlay').forEach(overlay => {
            overlay.remove();
        });
    }
    
    // Export chart data
    exportChartData(chartName) {
        const chart = this.charts[chartName];
        if (!chart) return;
        
        const data = chart.data;
        const csvContent = this.convertToCSV(data);
        
        this.downloadCSV(csvContent, `${chartName}-data.csv`);
    }
    
    convertToCSV(chartData) {
        const headers = ['Label', 'Value'];
        const rows = chartData.labels.map((label, index) => {
            return [label, chartData.datasets[0].data[index]].join(',');
        });
        
        return [headers.join(','), ...rows].join('\n');
    }
    
    downloadCSV(content, filename) {
        const blob = new Blob([content], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if Chart.js is available
    if (typeof Chart !== 'undefined') {
        window.adminCharts = new AdminCharts();
    }
    
    // Date range selector
    const dateRangeSelect = document.getElementById('date-range');
    if (dateRangeSelect) {
        dateRangeSelect.addEventListener('change', function() {
            if (window.adminCharts) {
                window.adminCharts.updateCharts(this.value);
            }
        });
    }
    
    // Real-time updates (simulated)
    setInterval(() => {
        // In a real application, this would check for new data
        // and update charts accordingly
    }, 30000); // Update every 30 seconds
});

// Utility functions for admin dashboard
function refreshDashboard() {
    if (window.adminCharts) {
        window.adminCharts.updateCharts();
    }
    
    // Refresh other dashboard components
    location.reload();
}

function exportReport(type) {
    const endpoints = {
        bookings: '/admin/export/bookings',
        revenue: '/admin/export/revenue',
        guests: '/admin/export/guests'
    };
    
    window.location.href = endpoints[type] || endpoints.bookings;
}
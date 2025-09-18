// Chart rendering and management functionality

class ChartManager {
    constructor() {
        this.charts = new Map();
        this.currentModalChart = null;
    }
    
    renderChart(chartData, containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Chart container not found:', containerId);
            return null;
        }
        
        // Create chart wrapper
        const chartWrapper = document.createElement('div');
        chartWrapper.className = 'chart-container';
        chartWrapper.innerHTML = `
            <div class=\"chart-header\">
                <h4 class=\"chart-title\">${chartData.title || 'График'}</h4>
                <button class=\"chart-expand\" onclick=\"openChartModal('${containerId}')\">
                    <i data-lucide=\"expand\"></i>
                </button>
            </div>
            <div class=\"chart-canvas-wrapper\">
                <canvas id=\"chart-${containerId}\" width=\"400\" height=\"200\"></canvas>
            </div>
        `;
        
        container.appendChild(chartWrapper);
        
        // Initialize Lucide icons for the new elements
        if (window.lucide) {
            window.lucide.createIcons();
        }
        
        // Create Chart.js instance
        const canvas = chartWrapper.querySelector('canvas');
        const ctx = canvas.getContext('2d');
        
        const chartConfig = this.prepareChartConfig(chartData);
        const chart = new Chart(ctx, chartConfig);
        
        // Store chart reference
        this.charts.set(containerId, {
            chart,
            data: chartData,
            container: chartWrapper
        });
        
        return chart;
    }
    
    prepareChartConfig(chartData) {
        const baseConfig = {
            type: chartData.type,
            data: chartData.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#2563eb',
                        borderWidth: 1
                    }
                },
                scales: this.getScaleConfig(chartData.type),
                ...chartData.options
            }
        };
        
        // Apply blue theme colors if not provided
        if (baseConfig.data.datasets) {
            baseConfig.data.datasets = baseConfig.data.datasets.map((dataset, index) => {
                return this.applyThemeColors(dataset, chartData.type, index);
            });
        }
        
        return baseConfig;
    }
    
    getScaleConfig(chartType) {
        if (chartType === 'pie' || chartType === 'doughnut') {
            return {};
        }
        
        return {
            y: {
                beginAtZero: true,
                grid: {
                    color: '#e2e8f0'
                },
                ticks: {
                    color: '#64748b'
                }
            },
            x: {
                grid: {
                    color: '#e2e8f0'
                },
                ticks: {
                    color: '#64748b'
                }
            }
        };
    }
    
    applyThemeColors(dataset, chartType, index) {
        const blueColors = [
            '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#dbeafe',
            '#1e40af', '#1d4ed8', '#2563eb', '#3730a3', '#4338ca'
        ];
        
        const lightBlueColors = [
            'rgba(37, 99, 235, 0.1)', 'rgba(59, 130, 246, 0.1)', 
            'rgba(96, 165, 250, 0.1)', 'rgba(147, 197, 253, 0.1)', 
            'rgba(219, 234, 254, 0.1)'
        ];
        
        if (!dataset.backgroundColor) {
            if (chartType === 'pie' || chartType === 'doughnut') {
                dataset.backgroundColor = blueColors;
            } else {
                dataset.backgroundColor = lightBlueColors[index % lightBlueColors.length];
            }
        }
        
        if (!dataset.borderColor) {
            dataset.borderColor = blueColors[index % blueColors.length];
        }
        
        if (!dataset.borderWidth) {
            dataset.borderWidth = 2;
        }
        
        // Specific styling for different chart types
        if (chartType === 'line') {
            dataset.fill = dataset.fill !== undefined ? dataset.fill : true;
            dataset.tension = dataset.tension !== undefined ? dataset.tension : 0.4;
        }
        
        return dataset;
    }
    
    openModalChart(containerId) {
        const chartData = this.charts.get(containerId);
        if (!chartData) {
            console.error('Chart not found:', containerId);
            return;
        }
        
        const modal = document.getElementById('chart-modal');
        const modalCanvas = document.getElementById('chart-canvas');
        
        if (!modal || !modalCanvas) {
            console.error('Chart modal elements not found');
            return;
        }
        
        // Destroy existing modal chart
        if (this.currentModalChart) {
            this.currentModalChart.destroy();
        }
        
        // Create new chart in modal
        const ctx = modalCanvas.getContext('2d');
        const config = this.prepareChartConfig(chartData.data);
        
        // Adjust config for modal display
        config.options.maintainAspectRatio = true;
        config.options.responsive = true;
        
        this.currentModalChart = new Chart(ctx, config);
        
        // Show modal
        modal.classList.remove('hidden');
        
        // Add click outside to close
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.closeModalChart();
            }
        };
    }
    
    closeModalChart() {
        const modal = document.getElementById('chart-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        if (this.currentModalChart) {
            this.currentModalChart.destroy();
            this.currentModalChart = null;
        }
    }
    
    destroyChart(containerId) {
        const chartData = this.charts.get(containerId);
        if (chartData) {
            chartData.chart.destroy();
            if (chartData.container && chartData.container.parentNode) {
                chartData.container.parentNode.removeChild(chartData.container);
            }
            this.charts.delete(containerId);
        }
    }
    
    destroyAllCharts() {
        this.charts.forEach((chartData, containerId) => {
            this.destroyChart(containerId);
        });
    }
    
    updateChart(containerId, newData) {
        const chartData = this.charts.get(containerId);
        if (chartData) {
            chartData.chart.data = newData.data;
            chartData.chart.options = { ...chartData.chart.options, ...newData.options };
            chartData.chart.update();
            chartData.data = newData;
        }
    }
}

// Global chart manager instance
window.chartManager = new ChartManager();

// Global functions for modal interaction
window.openChartModal = function(containerId) {
    window.chartManager.openModalChart(containerId);
};

window.closeChartModal = function() {
    window.chartManager.closeModalChart();
};

// Handle escape key to close modal
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        window.chartManager.closeModalChart();
    }
});"
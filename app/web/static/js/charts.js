// Initialize all weather charts
document.addEventListener('DOMContentLoaded', function() {
    const charts = {};
    const chartData = {};
    const chartConfigs = {};

    // Handle modal show event to initialize chart
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const modalId = this.id;
            const index = modalId.split('-').pop();
            const canvasId = `modal-chart-${index}`;
            const canvas = document.getElementById(canvasId);
            const dataElement = document.getElementById(`modal-chart-data-${index}`);
            const configElement = document.getElementById(`modal-chart-config-${index}`);

            if (!canvas || !dataElement || !configElement) {
                console.error(`Canvas, data or config not found for modal ${modalId}`);
                return;
            }

            // Store original data and config
            if (!chartData[canvasId]) {
                try {
                    chartData[canvasId] = JSON.parse(dataElement.textContent);
                    chartConfigs[canvasId] = JSON.parse(configElement.textContent);
                } catch (e) {
                    console.error(`Error parsing data for ${canvasId}:`, e);
                    return;
                }
            }

            // Only create chart if it doesn't exist yet
            if (!charts[canvasId]) {
                const days = parseInt(document.querySelector(`.days-select[data-chart="${canvasId}"]`).value);

                charts[canvasId] = createWeatherChart(
                    canvas,
                    chartData[canvasId],
                    chartConfigs[canvasId],
                    days
                );
                console.log(`Chart created for ${canvasId}`);
            }
        });
    });

    // Handle model toggle checkboxes
    document.querySelectorAll('.model-toggle').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const chartId = this.dataset.chart;
            const chart = charts[chartId];
            const modelName = this.value;

            if (chart) {
                chart.data.datasets.forEach(dataset => {
                    if (dataset.modelName === modelName) {
                        dataset.hidden = !this.checked;
                    }
                });
                chart.update();
            }
        });
    });

    // Handle days selection
    document.querySelectorAll('.days-select').forEach(select => {
        select.addEventListener('change', function() {
            const chartId = this.dataset.chart;
            const days = parseInt(this.value);
            const canvas = document.getElementById(chartId);

            if (charts[chartId]) {
                charts[chartId].destroy();
            }

            charts[chartId] = createWeatherChart(
                canvas,
                chartData[chartId],
                chartConfigs[chartId],
                days
            );
        });
    });
});

function createWeatherChart(canvas, data, config, days = 3) {
    const ctx = canvas.getContext('2d');
    const models = data.models || {};

    if (Object.keys(models).length === 0) {
        console.error('No models data available');
        return null;
    }

    // Build color map from config
    const colors = {};
    config.models.forEach(model => {
        colors[model.id] = model.colors;
    });

    const datasets = [];

    // Get timestamps from first available model
    const firstModel = Object.values(models)[0];
    const allTimestamps = firstModel?.timestamps || [];

    if (allTimestamps.length === 0) {
        console.error('No timestamps available');
        return null;
    }

    // Filter by days (24 hours per day)
    const maxHours = days * 24;
    const timestamps = allTimestamps.slice(0, maxHours);

    // FIX BUG 3: Use all hourly data instead of sampling every 3rd hour
    const sampledIndices = timestamps.map((_, idx) => idx);
    const sampledTimestamps = sampledIndices.map(i => timestamps[i]);

    // Create datasets for each model
    Object.entries(models).forEach(([modelName, modelData]) => {
        const color = colors[modelName] || colors['gfs_seamless'];

        // Get data for all hours
        const sampledTemp = sampledIndices.map(i => modelData.temperature[i]);
        const sampledPrecip = sampledIndices.map(i => modelData.precipitation[i]);

        // Temperature dataset (line)
        datasets.push({
            label: 'Temperature',
            data: sampledTemp,
            borderColor: color.temp,
            backgroundColor: 'transparent',
            yAxisID: 'temp',
            tension: 0.4,
            modelName: modelName,
            borderWidth: 2,
            pointRadius: 0,  // Hide points for cleaner look
            pointHoverRadius: 4  // Show on hover
        });

        // Precipitation dataset (bar)
        datasets.push({
            label: 'Precipitation',
            data: sampledPrecip,
            backgroundColor: color.precip,
            borderColor: color.precip,
            yAxisID: 'precip',
            type: 'bar',
            modelName: modelName,
            barPercentage: 0.9,
            categoryPercentage: 1.0
        });
    });

    // Build x-axis labels (show every 6 hours for readability)
    const xLabels = sampledTimestamps.map((ts, idx) => {
        const date = new Date(ts);
        // Only show label every 6 hours to avoid clutter
        if (idx % 6 === 0) {
            return date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                hour12: false
            });
        }
        return '';  // Empty string for other hours
    });

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: xLabels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            // Show full timestamp in tooltip
                            const date = new Date(sampledTimestamps[context[0].dataIndex]);
                            return date.toLocaleString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                                hour12: false
                            });
                        },
                        label: function(context) {
                            const modelName = context.dataset.modelName;
                            const modelConfig = config.models.find(m => m.id === modelName);
                            const displayName = modelConfig ? modelConfig.name : modelName;

                            let label = `${displayName} ${context.dataset.label}: `;

                            if (context.parsed.y !== null) {
                                if (context.dataset.label === 'Temperature') {
                                    label += context.parsed.y.toFixed(1) + '°C';
                                } else if (context.dataset.label === 'Precipitation') {
                                    label += context.parsed.y.toFixed(1) + ' mm';
                                }
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkip: false  // Don't auto-skip, we control via empty strings
                    }
                },
                temp: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    }
                },
                precip: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Precipitation (mm)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    }
                }
            }
        }
    });
}

// app/web/static/js/warning-map.js
/**
 * Warning Map for Bootstrap Modal
 */

let warningMap = null;
let currentWarningNumber = null;
let currentDay = 1;
let totalDays = 0;
let allGeojsonData = null;

/**
 * Initialize map when modal is shown
 */
document.addEventListener('DOMContentLoaded', () => {
    const mapModal = document.getElementById('map-modal');

    if (mapModal) {
        mapModal.addEventListener('shown.bs.modal', () => {
            if (!warningMap) {
                initMap();
            } else {
                warningMap.invalidateSize(); // Refresh map size
            }
        });

        mapModal.addEventListener('hidden.bs.modal', () => {
            // Clean up
            currentDay = 1;
        });
    }
});

/**
 * Initialize Leaflet map
 */
function initMap() {
    const mapElement = document.getElementById('warning-map');

    if (!mapElement || warningMap) return;

    // Create map centered on Peru with higher zoom
    warningMap = L.map('warning-map').setView([-9.19, -75.0152], 6);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
    }).addTo(warningMap);

    console.log('✓ Map initialized');
}

/**
 * Load warning geometry
 */
async function loadWarningMap(warningNumber) {
    currentWarningNumber = warningNumber;
    allGeojsonData = null;

    document.getElementById('map-modal-title').textContent = `Warning #${warningNumber}`;
    showStatus('Loading geometries...', 'info');

    try {
        const response = await fetch(`/api/warnings/${currentWarningNumber}/geometry`);

        if (!response.ok) {
            const error = await response.json();

            if (response.status === 404) {
                showStatus('No geometries available for this warning.', 'warning');
                return;
            }

            throw new Error(error.message || 'Error loading geometry');
        }

        const geojson = await response.json();

        if (geojson.type === 'FeatureCollection') {
            const uniqueDays = new Set(
                geojson.features.map(f => f.properties.day_number)
            );
            totalDays = uniqueDays.size;

            // Determine initial day based on current date and warning status
            const firstFeature = geojson.features[0];
            const validFrom = new Date(firstFeature.properties.valid_from);
            const validUntil = new Date(firstFeature.properties.valid_until);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            if (today >= validFrom && today <= validUntil) {
                // Warning is active, calculate current day
                const daysDiff = Math.floor((today - validFrom) / (1000 * 60 * 60 * 24));
                currentDay = Math.max(1, Math.min(daysDiff + 1, totalDays));
            } else {
                // Warning is not active, start at day 1
                currentDay = 1;
            }
        } else {
            totalDays = 1;
            currentDay = 1;
        }

        createTimeline(totalDays);

        await showDay(currentDay);

        hideStatus();

    } catch (error) {
        console.error('Error loading geometry:', error);
        showStatus(error.message, 'danger');
    }
}

/**
 * Show specific day
 */
async function showDay(day) {
    if (day < 1 || day > totalDays) return;

    currentDay = day;
    updateTimelineButtons();

    try {
        if (!allGeojsonData) {
            const response = await fetch(`/api/warnings/${currentWarningNumber}/geometry`);
            const geojson = await response.json();
            allGeojsonData = geojson;
        }

        const dayFeatures = allGeojsonData.features.filter(
            f => f.properties.day_number === day
        );

        const dayGeojson = {
            type: "FeatureCollection",
            features: dayFeatures
        };

        // Clear only warning GeoJSON layers (not department boundaries)
        warningMap.eachLayer((layer) => {
            if (layer instanceof L.GeoJSON && !layer.options.isDepartmentLayer) {
                warningMap.removeLayer(layer);
            }
        });

        // Add GeoJSON for this day
        const geoJsonLayer = L.geoJSON(dayGeojson, {
            style: getFeatureStyle,
            onEachFeature: bindPopup
        }).addTo(warningMap);

        // On first day: add all departments and zoom to current one
        if (day === 1) {
            const departmentMatch = window.location.pathname.match(/\/department\/([^\/]+)/);
            const departmentName = departmentMatch ? departmentMatch[1] : null;

            try {
                // Fetch ALL departments geometry
                const allDeptsResponse = await fetch('/api/departments/all/geometry');
                if (allDeptsResponse.ok) {
                    const allDeptsGeojson = await allDeptsResponse.json();

                    // Add all departments as boundary layer
                    L.geoJSON(allDeptsGeojson, {
                        style: {
                            color: '#000000',
                            weight: 1.5,
                            opacity: 0.6,
                            fill: false
                        },
                        isDepartmentLayer: true  // Mark as department layer
                    }).addTo(warningMap);
                }

                // Zoom to current department only
                if (departmentName) {
                    const deptResponse = await fetch(`/api/departments/${departmentName}/geometry`);
                    if (deptResponse.ok) {
                        const deptGeojson = await deptResponse.json();
                        const deptLayer = L.geoJSON(deptGeojson);
                        warningMap.fitBounds(deptLayer.getBounds(), { padding: [50, 50] });
                    } else {
                        warningMap.fitBounds(geoJsonLayer.getBounds(), { padding: [50, 50] });
                    }
                } else {
                    warningMap.fitBounds(geoJsonLayer.getBounds(), { padding: [50, 50] });
                }
            } catch (error) {
                console.error('Error fetching departments:', error);
                warningMap.fitBounds(geoJsonLayer.getBounds(), { padding: [50, 50] });
            }
        }

        // Update button labels with actual dates
        if (dayFeatures.length > 0) {
            const validFrom = new Date(dayFeatures[0].properties.valid_from);
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

            for (let i = 1; i <= totalDays; i++) {
                const btn = document.getElementById(`timeline-day-${i}`);
                if (btn) {
                    const btnDate = new Date(validFrom);
                    btnDate.setDate(btnDate.getDate() + (i - 1));
                    const dd = String(btnDate.getDate()).padStart(2, '0');
                    const mmm = monthNames[btnDate.getMonth()];
                    btn.textContent = `${dd} ${mmm}`;
                }
            }
        }

    } catch (error) {
        console.error('Error showing day:', error);
        showStatus('Error loading day ' + day, 'danger');
    }
}

/**
 * Create timeline buttons
 */
function createTimeline(days) {
    const timeline = document.getElementById('map-timeline');
    timeline.innerHTML = '';

    for (let day = 1; day <= days; day++) {
        const button = document.createElement('button');
        button.className = 'btn btn-outline-primary';
        button.id = `timeline-day-${day}`;

        // Calculate date for this day
        // This will be populated from the first feature's valid_from date
        button.textContent = `Day ${day}`;
        button.dataset.day = day;

        button.onclick = () => showDay(day);
        timeline.appendChild(button);
    }
}

/**
 * Update timeline button states
 */
function updateTimelineButtons() {
    for (let day = 1; day <= totalDays; day++) {
        const button = document.getElementById(`timeline-day-${day}`);
        if (button) {
            if (day === currentDay) {
                button.classList.remove('btn-outline-primary');
                button.classList.add('btn-primary');
            } else {
                button.classList.remove('btn-primary');
                button.classList.add('btn-outline-primary');
            }
        }
    }
}

/**
 * Get style based on severity
 */
function getFeatureStyle(feature) {
    const nivel = feature.properties?.nivel || 0;

    // Map nivel to CSS classes (1-4 scale)
    const classMap = {
        1: 'warning-nivel-1',
        2: 'warning-nivel-2',
        3: 'warning-nivel-3',
        4: 'warning-nivel-4'
    };

    return {
        className: classMap[nivel] || 'warning-nivel-default'
    };
}

/**
 * Bind popup to feature
 */
function bindPopup(feature, layer) {
    if (!feature.properties) return;

    const props = feature.properties;

    // Map nivel to color name (corrected)
    const nivelNames = {
        1: 'Transparente',
        2: 'Amarillo',
        3: 'Naranja',
        4: 'Rojo'
    };

    const popup = `
        <div>
            <h6 class="mb-2">Warning #${props.warning_number}</h6>
            <p class="mb-1"><strong>Day:</strong> ${props.day_number}</p>
            <p class="mb-1"><strong>Level:</strong> Nivel ${props.nivel} (${nivelNames[props.nivel] || 'N/A'})</p>
            <p class="mb-1"><strong>Severity:</strong> <span class="badge" style="background-color: ${getSeverityColor(props.severity)}">${props.severity?.toUpperCase()}</span></p>
            <p class="mb-0"><strong>Department:</strong> ${props.department}</p>
        </div>
    `;

    layer.bindPopup(popup);
}
/**
 * Get severity color
 */
function getSeverityColor(severity) {
    const colors = {
        'verde': '#198754',
        'amarillo': '#ffc107',
        'naranja': '#fd7e14',
        'rojo': '#dc3545'
    };
    return colors[severity] || '#ffc107';
}

/**
 * Show status message
 */
function showStatus(message, type = 'info') {
    const status = document.getElementById('map-status');
    status.className = `alert alert-${type} mt-3`;
    status.textContent = message;
    status.style.display = 'block';
}

/**
 * Hide status message
 */
function hideStatus() {
    const status = document.getElementById('map-status');
    status.style.display = 'none';
}

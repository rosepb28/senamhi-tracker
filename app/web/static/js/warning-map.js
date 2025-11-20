/**
 * Warning Map for Bootstrap Modal
 */

let warningMap = null;
let currentWarningNumber = null;
let currentDay = 1;
let totalDays = 0;
let allGeojsonData = null;
let departmentBoundariesAdded = false;

// OPTIMIZATION 1: Cache geometries by warning number
let geometryCache = {};

// OPTIMIZATION 2: Cache department boundaries
let allDepartmentsGeojson = null;
let targetDepartmentGeometry = null;

// OPTIMIZATION 3: Precalculated timeline dates
let timelineDates = [];

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
                warningMap.invalidateSize();
            }
        });

        mapModal.addEventListener('hidden.bs.modal', () => {
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

    warningMap = L.map('warning-map').setView([-9.19, -75.0152], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
    }).addTo(warningMap);

    console.log('✓ Map initialized');
}

/**
 * Load warning geometry with caching
 */
async function loadWarningMap(warningNumber) {
    currentWarningNumber = warningNumber;
    departmentBoundariesAdded = false;
    targetDepartmentGeometry = null;  // Reset department cache

    document.getElementById('map-modal-title').textContent = `Warning #${warningNumber}`;
    showStatus('Loading geometries...', 'info');

    try {
        // OPTIMIZATION 1: Check cache first
        if (geometryCache[warningNumber]) {
            console.log(`✓ Using cached geometry for warning #${warningNumber}`);
            allGeojsonData = geometryCache[warningNumber];
        } else {
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
            allGeojsonData = geojson;
            geometryCache[warningNumber] = geojson;  // Cache it
            console.log(`✓ Cached geometry for warning #${warningNumber}`);
        }

        if (allGeojsonData.type === 'FeatureCollection') {
            const uniqueDays = new Set(
                allGeojsonData.features.map(f => f.properties.day_number)
            );
            totalDays = uniqueDays.size;

            const firstFeature = allGeojsonData.features[0];
            const validFrom = new Date(firstFeature.properties.valid_from);
            const validUntil = new Date(firstFeature.properties.valid_until);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            if (today >= validFrom && today <= validUntil) {
                const daysDiff = Math.floor((today - validFrom) / (1000 * 60 * 60 * 24));
                currentDay = Math.max(1, Math.min(daysDiff + 1, totalDays));
            } else {
                currentDay = 1;
            }
        } else {
            totalDays = 1;
            currentDay = 1;
        }

        createTimeline(totalDays, allGeojsonData.features);

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
        const dayFeatures = allGeojsonData.features.filter(
            f => f.properties.day_number === day
        );

        const dayGeojson = {
            type: "FeatureCollection",
            features: dayFeatures
        };

        // Clear only warning GeoJSON layers
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

        // OPTIMIZATION: Only load departments once on first day
        if (day === 1 && !departmentBoundariesAdded) {
            await loadDepartmentBoundaries(geoJsonLayer);
        }

    } catch (error) {
        console.error('Error showing day:', error);
        showStatus('Error loading day ' + day, 'danger');
    }
}

/**
 * Load department boundaries with caching
 * OPTIMIZATION 2: Cache department geometries
 */
async function loadDepartmentBoundaries(geoJsonLayer) {
    const departmentMatch = window.location.pathname.match(/\/department\/([^\/]+)/);
    const departmentName = departmentMatch ? departmentMatch[1] : null;

    try {
        // Fetch all departments if not cached
        if (!allDepartmentsGeojson) {
            console.log('Fetching all departments geometry...');
            const allDeptsResponse = await fetch('/api/departments/all/geometry');
            if (allDeptsResponse.ok) {
                allDepartmentsGeojson = await allDeptsResponse.json();
                console.log('✓ Cached all departments geometry');
            }
        }

        // Add cached department boundaries
        if (allDepartmentsGeojson) {
            L.geoJSON(allDepartmentsGeojson, {
                style: {
                    color: '#000000',
                    weight: 1.5,
                    opacity: 0.6,
                    fill: false
                },
                isDepartmentLayer: true
            }).addTo(warningMap);

            departmentBoundariesAdded = true;
        }

        // Zoom to current department
        if (departmentName) {
            if (!targetDepartmentGeometry) {
                console.log(`Fetching ${departmentName} geometry for zoom...`);
                const deptResponse = await fetch(`/api/departments/${departmentName}/geometry`);
                if (deptResponse.ok) {
                    targetDepartmentGeometry = await deptResponse.json();
                    console.log(`✓ Cached ${departmentName} geometry`);
                }
            }

            if (targetDepartmentGeometry) {
                const deptLayer = L.geoJSON(targetDepartmentGeometry);
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

/**
 * Create timeline buttons with actual dates
 * OPTIMIZATION 3: Precalculate and cache dates
 */
function createTimeline(days, features) {
    const timeline = document.getElementById('map-timeline');
    timeline.innerHTML = '';
    timelineDates = [];  // Reset cache

    if (!features || features.length === 0) {
        // Fallback to Day X if no features
        for (let day = 1; day <= days; day++) {
            const button = document.createElement('button');
            button.className = 'btn btn-outline-primary';
            button.id = `timeline-day-${day}`;
            button.textContent = `Day ${day}`;
            button.dataset.day = day;
            button.onclick = () => showDay(day);
            timeline.appendChild(button);
        }
        return;
    }

    // Get valid_from from first feature
    const firstFeature = features[0];
    const baseDate = new Date(firstFeature.properties.valid_from);
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    for (let day = 1; day <= days; day++) {
        const button = document.createElement('button');
        button.className = 'btn btn-outline-primary';
        button.id = `timeline-day-${day}`;

        // Calculate and cache date for this day
        const dayDate = new Date(baseDate);
        dayDate.setDate(dayDate.getDate() + (day - 1));
        timelineDates.push(dayDate);  // Cache for later use

        const dd = String(dayDate.getDate()).padStart(2, '0');
        const mmm = monthNames[dayDate.getMonth()];
        button.textContent = `${dd} ${mmm}`;

        button.dataset.day = day;
        button.onclick = () => showDay(day);
        timeline.appendChild(button);
    }

    console.log(`✓ Timeline created with ${days} days`);
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

    const popup = `
        <div>
            <h6 class="mb-2">Warning #${props.warning_number}</h6>
            <p class="mb-1"><strong>Day:</strong> ${props.day_number}</p>
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

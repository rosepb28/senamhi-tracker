// app/web/static/js/warning-map.js
let warningMap = null;
let currentWarningNumber = null;
let currentDay = 1;
let totalDays = 0;
let allGeojsonData = null;
let hasGeometry = false;

// Cache
let geometryCache = {};
let warningDetailsCache = {};
let currentWarningDetails = null;
let allDepartmentsGeojson = null;
let targetDepartmentGeometry = null;
let departmentBoundariesAdded = false;

/**
 * Initialize map when modal is shown
 */
document.addEventListener('DOMContentLoaded', () => {
    const mapModal = document.getElementById('map-modal');

    if (mapModal) {
        mapModal.addEventListener('shown.bs.modal', () => {
            if (hasGeometry && !warningMap) {
                initMap();
            } else if (hasGeometry && warningMap) {
                warningMap.invalidateSize();
            }
        });

        mapModal.addEventListener('hidden.bs.modal', () => {
            currentDay = 1;
            currentWarningDetails = null;
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
 * Load warning details with caching
 */
async function loadWarningDetails(warningNumber, department) {
    const cacheKey = `${warningNumber}-${department}`;

    if (warningDetailsCache[cacheKey]) {
        return warningDetailsCache[cacheKey];
    }

    try {
        const response = await fetch(`/api/warnings/${warningNumber}/details/${department}`);
        if (!response.ok) return null;

        const data = await response.json();
        warningDetailsCache[cacheKey] = data;
        return data;
    } catch (error) {
        console.error('Error loading warning details:', error);
        return null;
    }
}

/**
 * Display warning details in modal
 */
function displayWarningDetails(details, dayNumber) {
    console.log('=== DEBUG ===');
    console.log('Details:', JSON.stringify(details, null, 2));
    console.log('Looking for day_number:', dayNumber);
    console.log('Available days:', details?.days?.map(d => d.day_number));

    const container = document.getElementById('warning-details-container');
    if (!container) {
        console.log('ERROR: Container not found!');
        return;
    }

    if (!details) {
        console.log('ERROR: No details provided');
        container.innerHTML = '';
        return;
    }

    const dayDetails = details.days.find(d => d.day_number === dayNumber);
    console.log('Found dayDetails:', dayDetails);

    if (!dayDetails) {
        console.log('ERROR: No details for day', dayNumber);
        container.innerHTML = '<p class="text-muted">No details available for this day.</p>';
        return;
    }

    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <strong>Day ${dayNumber} Details</strong>
                ${dayDetails.date ? `<span class="text-muted ms-2">(${dayDetails.date})</span>` : ''}
            </div>
            <div class="card-body">
                <p class="mb-3">${dayDetails.description}</p>

                ${dayDetails.affected_provinces && dayDetails.affected_provinces.length > 0 ? `
                    <div class="mt-3">
                        <strong class="d-block mb-2">Affected Provinces (${dayDetails.affected_provinces.length}):</strong>
                        <div class="d-flex flex-wrap gap-1">
                            ${dayDetails.affected_provinces.map(p =>
                                `<span class="badge bg-secondary">${p}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Main function to load warning (with or without geometry)
 */
async function loadWarningMap(warningNumber, hasGeo) {
    currentWarningNumber = warningNumber;
    hasGeometry = hasGeo;
    departmentBoundariesAdded = false;

    // Load warning info for title
    const infoResponse = await fetch(`/api/warnings/${warningNumber}/info`);
    if (infoResponse.ok) {
        const info = await infoResponse.json();
        document.getElementById('map-modal-title').textContent =
            `Warning #${warningNumber} - ${info.title}`;
    } else {
        document.getElementById('map-modal-title').textContent = `Warning #${warningNumber}`;
    }

    const mapWrapper = document.getElementById('map-container-wrapper');
    const footerText = document.getElementById('modal-footer-text');

    // Get department from URL
    const departmentMatch = window.location.pathname.match(/\/department\/([^\/]+)/);
    const departmentName = departmentMatch ? departmentMatch[1] : null;

    if (!departmentName) {
        showStatus('Department not found', 'danger');
        return;
    }

    // Load warning details first
    currentWarningDetails = await loadWarningDetails(warningNumber, departmentName);

    if (!currentWarningDetails) {
        showStatus('Failed to load warning details', 'danger');
        return;
    }

    totalDays = currentWarningDetails.days.length;

    // Use the first available day_number (not always 1!)
    if (currentWarningDetails.days.length > 0) {
        currentDay = currentWarningDetails.days[0].day_number;
    } else {
        currentDay = 1;
    }

    // Create timeline
    createTimelineFromDetails(currentWarningDetails);

    // Handle geometry
    if (hasGeometry) {
        mapWrapper.style.display = 'block';
        footerText.textContent = 'Geometries from SENAMHI GeoServer';

        showStatus('Loading geometries...', 'info');

        try {
            if (geometryCache[warningNumber]) {
                allGeojsonData = geometryCache[warningNumber];
            } else {
                const response = await fetch(`/api/warnings/${warningNumber}/geometry`);
                if (!response.ok) throw new Error('Failed to load geometry');

                allGeojsonData = await response.json();
                geometryCache[warningNumber] = allGeojsonData;
            }

            initMap();
            await showDay(currentDay);
            hideStatus();

        } catch (error) {
            console.error('Error loading geometry:', error);
            showStatus('Error loading map data', 'danger');
        }
    } else {
        // No geometry - hide map, show only details
        mapWrapper.style.display = 'none';
        footerText.textContent = 'Warning details from SENAMHI API';
        displayWarningDetails(currentWarningDetails, currentDay);
        hideStatus();
    }
}

/**
 * Show specific day
 */
async function showDay(day) {
    if (!currentWarningDetails) return;

    // Validate that this day exists in the details
    const dayExists = currentWarningDetails.days.some(d => d.day_number === day);
    if (!dayExists) return;

    currentDay = day;
    updateTimelineButtons();

    if (hasGeometry && allGeojsonData) {
        try {
            const dayFeatures = allGeojsonData.features.filter(
                f => f.properties.day_number === day
            );

            const dayGeojson = {
                type: "FeatureCollection",
                features: dayFeatures
            };

            warningMap.eachLayer((layer) => {
                if (layer instanceof L.GeoJSON && !layer.options.isDepartmentLayer) {
                    warningMap.removeLayer(layer);
                }
            });

            const geoJsonLayer = L.geoJSON(dayGeojson, {
                style: getFeatureStyle,
                onEachFeature: bindPopup
            }).addTo(warningMap);

            if (day === 1 && !departmentBoundariesAdded) {
                await loadDepartmentBoundaries(geoJsonLayer);
            }

        } catch (error) {
            console.error('Error showing day:', error);
            showStatus('Error loading day ' + day, 'danger');
        }
    }

    // Always update details
    if (currentWarningDetails) {
        displayWarningDetails(currentWarningDetails, day);
    }
}

/**
 * Create timeline from warning details
 */
function createTimelineFromDetails(details) {
    const timeline = document.getElementById('map-timeline');
    timeline.innerHTML = '';

    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    details.days.forEach(day => {
        const button = document.createElement('button');
        button.className = 'btn btn-outline-primary';
        button.id = `timeline-day-${day.day_number}`;

        if (day.date) {
            const date = new Date(day.date + 'T00:00:00'); // Force local timezone
            const dd = String(date.getDate()).padStart(2, '0');
            const mmm = monthNames[date.getMonth()];
            button.textContent = `${dd} ${mmm}`;
        } else {
            button.textContent = `Day ${day.day_number}`;
        }

        button.dataset.day = day.day_number;
        button.onclick = () => showDay(day.day_number);
        timeline.appendChild(button);
    });

    updateTimelineButtons();
}
/**
 * Update timeline button states
 */
function updateTimelineButtons() {
    if (!currentWarningDetails) return;

    currentWarningDetails.days.forEach(day => {
        const button = document.getElementById(`timeline-day-${day.day_number}`);
        if (button) {
            if (day.day_number === currentDay) {
                button.classList.remove('btn-outline-primary');
                button.classList.add('btn-primary');
            } else {
                button.classList.remove('btn-primary');
                button.classList.add('btn-outline-primary');
            }
        }
    });
}
/**
 * Load department boundaries
 */
async function loadDepartmentBoundaries(geoJsonLayer) {
    const departmentMatch = window.location.pathname.match(/\/department\/([^\/]+)/);
    const departmentName = departmentMatch ? departmentMatch[1] : null;

    try {
        if (!allDepartmentsGeojson) {
            const allDeptsResponse = await fetch('/api/departments/all/geometry');
            if (allDeptsResponse.ok) {
                allDepartmentsGeojson = await allDeptsResponse.json();
            }
        }

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

        if (departmentName) {
            if (!targetDepartmentGeometry) {
                const deptResponse = await fetch(`/api/departments/${departmentName}/geometry`);
                if (deptResponse.ok) {
                    targetDepartmentGeometry = await deptResponse.json();
                }
            }

            if (targetDepartmentGeometry) {
                const deptLayer = L.geoJSON(targetDepartmentGeometry);
                warningMap.fitBounds(deptLayer.getBounds(), { padding: [30, 30] });
            } else {
                warningMap.fitBounds(geoJsonLayer.getBounds(), { padding: [30, 30] });
            }
        } else {
            warningMap.fitBounds(geoJsonLayer.getBounds(), { padding: [30, 30] });
        }
    } catch (error) {
        console.error('Error fetching departments:', error);
        warningMap.fitBounds(geoJsonLayer.getBounds(), { padding: [30, 30] });
    }
}

function getFeatureStyle(feature) {
    const nivel = feature.properties?.nivel || 0;
    const classMap = {
        1: 'warning-nivel-1',
        2: 'warning-nivel-2',
        3: 'warning-nivel-3',
        4: 'warning-nivel-4'
    };
    return { className: classMap[nivel] || 'warning-nivel-default' };
}

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

function getSeverityColor(severity) {
    const colors = {
        'verde': '#198754',
        'amarillo': '#ffc107',
        'naranja': '#fd7e14',
        'rojo': '#dc3545'
    };
    return colors[severity] || '#ffc107';
}

function showStatus(message, type = 'info') {
    const status = document.getElementById('map-status');
    status.className = `alert alert-${type} mt-3`;
    status.textContent = message;
    status.style.display = 'block';
}

function hideStatus() {
    const status = document.getElementById('map-status');
    status.style.display = 'none';
}

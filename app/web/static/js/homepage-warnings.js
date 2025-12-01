let homepageWarningMap = null;
let currentWarningNumber = null;
let currentDay = 1;
let hasGeometry = false;

// Cache
let warningDetailsCache = {};
let currentWarningDetails = null;
let allDepartmentsGeojson = null;
let departmentBoundariesAdded = false;
let departmentBoundariesLayer = null; // ← Store layer reference

/**
 * Read map configuration from CSS variables
 * @returns {object} { lat, lng, zoom }
 */
function getMapConfig() {
    const styles = getComputedStyle(document.documentElement);

    return {
        lat: parseFloat(styles.getPropertyValue('--homepage-map-center-lat') || '-9.19'),
        lng: parseFloat(styles.getPropertyValue('--homepage-map-center-lng') || '-75.0152'),
        zoom: parseFloat(styles.getPropertyValue('--homepage-map-zoom') || '5')
    };
}

/**
 * Load department boundaries (Peru outline)
 */
async function loadDepartmentBoundaries() {
    if (departmentBoundariesAdded || !homepageWarningMap) return;

    try {
        if (!allDepartmentsGeojson) {
            console.log('Fetching department boundaries...');
            const response = await fetch('/api/departments/all/geometry');
            if (response.ok) {
                allDepartmentsGeojson = await response.json();
                console.log('✓ Department boundaries loaded');
            }
        }

        if (allDepartmentsGeojson) {
            departmentBoundariesLayer = L.geoJSON(allDepartmentsGeojson, {
                style: {
                    color: '#000000',
                    weight: 1.5,
                    opacity: 0.6,
                    fill: false
                },
                isDepartmentLayer: true
            }).addTo(homepageWarningMap);

            departmentBoundariesAdded = true;
            console.log('✓ Department boundaries added to map');
        }
    } catch (error) {
        console.error('Error loading department boundaries:', error);
    }
}

async function loadWarningDetails(warningNumber, hasGeo) {
    currentWarningNumber = warningNumber;
    hasGeometry = hasGeo;

    // Reset boundaries flag for new warning
    departmentBoundariesAdded = false;
    if (departmentBoundariesLayer && homepageWarningMap) {
        homepageWarningMap.removeLayer(departmentBoundariesLayer);
        departmentBoundariesLayer = null;
    }

    // Load warning info first for title
    const info = await loadWarningInfo(warningNumber);

    if (info) {
        document.getElementById('warning-modal-title').textContent =
            `Warning #${warningNumber} - ${info.title}`;
    } else {
        document.getElementById('warning-modal-title').textContent = `Warning #${warningNumber}`;
    }

    // Adjust layout based on geometry availability
    const mapColumn = document.getElementById('map-column');
    const detailsColumn = document.getElementById('details-column');

    if (hasGeometry) {
        mapColumn.style.display = 'block';
        detailsColumn.classList.remove('col-lg-12');
        document.getElementById('modal-footer-text').textContent = 'Geometries from SENAMHI GeoServer';

        initializeHomepageMap();

        setTimeout(async () => {
            await loadWarningGeometry(warningNumber);
        }, 500);
    } else {
        mapColumn.style.display = 'none';
        detailsColumn.classList.add('col-lg-12');
        document.getElementById('modal-footer-text').textContent = 'Warning details from SENAMHI API';
    }

    // Load and display details
    await loadAndDisplayDetails(warningNumber);
}

function initializeHomepageMap() {
    const mapElement = document.getElementById('homepage-warning-map');
    const config = getMapConfig();

    if (!mapElement) {
        console.error('Map element not found!');
        return;
    }

    if (!homepageWarningMap) {
        setTimeout(() => {
            homepageWarningMap = L.map('homepage-warning-map')
                .setView([config.lat, config.lng], config.zoom);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(homepageWarningMap);

            console.log('✓ Homepage map initialized with zoom:', config.zoom);
        }, 300);
    } else {
        setTimeout(() => {
            homepageWarningMap.invalidateSize();
        }, 300);
    }
}

async function loadWarningGeometry(warningNumber) {
    try {
        const response = await fetch(`/api/warnings/${warningNumber}/geometry`);
        if (!response.ok) throw new Error('Failed to load geometry');

        const geojson = await response.json();

        // Extract unique days and get first day
        const days = [...new Set(geojson.features.map(f => f.properties.day_number))].sort();
        currentDay = days[0] || 1;

        // Create timeline with dates
        await createTimeline(geojson, warningNumber);

        // Load first day
        await showDay(currentDay, warningNumber);

    } catch (error) {
        console.error('Error loading geometry:', error);
    }
}

async function createTimeline(geojson, warningNumber) {
    const timeline = document.getElementById('homepage-map-timeline');
    timeline.innerHTML = '';

    // Get unique days
    const days = [...new Set(geojson.features.map(f => f.properties.day_number))].sort();

    // Get dates from first feature of each day
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    days.forEach(dayNum => {
        const dayFeature = geojson.features.find(f => f.properties.day_number === dayNum);
        const btn = document.createElement('button');
        btn.className = dayNum === currentDay ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-outline-primary';
        btn.id = `homepage-day-${dayNum}`;

        // Format date from valid_from
        if (dayFeature && dayFeature.properties.valid_from) {
            const validFrom = new Date(dayFeature.properties.valid_from);
            validFrom.setDate(validFrom.getDate() + (dayNum - 1));
            const dd = String(validFrom.getDate()).padStart(2, '0');
            const mmm = monthNames[validFrom.getMonth()];
            btn.textContent = `${dd} ${mmm}`;
        } else {
            btn.textContent = `Day ${dayNum}`;
        }

        btn.onclick = () => showDay(dayNum, warningNumber);
        timeline.appendChild(btn);
    });
}

async function showDay(day, warningNumber) {
    console.log('=== showDay ===');
    console.log('Day:', day);
    console.log('Warning:', warningNumber);
    console.log('Map exists:', !!homepageWarningMap);

    currentDay = day;

    // Update button states
    document.querySelectorAll('#homepage-map-timeline button').forEach(btn => {
        if (btn.id === `homepage-day-${day}`) {
            btn.className = 'btn btn-sm btn-primary';
        } else {
            btn.className = 'btn btn-sm btn-outline-primary';
        }
    });

    // Load geometry for this day
    try {
        const response = await fetch(`/api/warnings/${warningNumber}/geometry/${day}`);
        if (!response.ok) throw new Error('Failed to load day geometry');

        const geojson = await response.json();

        // Clear existing GeoJSON layers EXCEPT department boundaries
        homepageWarningMap.eachLayer(layer => {
            if (layer instanceof L.GeoJSON && !layer.options.isDepartmentLayer) {
                homepageWarningMap.removeLayer(layer);
            }
        });

        // Add new geometry with CSS classes (same as department map)
        L.geoJSON(geojson, {
            style: (feature) => {
                const nivel = feature.properties?.nivel || 0;
                const classMap = {
                    1: 'warning-nivel-1',
                    2: 'warning-nivel-2',
                    3: 'warning-nivel-3',
                    4: 'warning-nivel-4'
                };
                return { className: classMap[nivel] || 'warning-nivel-default' };
            },
            onEachFeature: (feature, layer) => {
                if (feature.properties) {
                    const props = feature.properties;
                    layer.bindPopup(`
                        <div>
                            <h6 class="mb-2">Warning #${props.warning_number}</h6>
                            <p class="mb-1"><strong>Day:</strong> ${props.day_number}</p>
                            <p class="mb-1"><strong>Department:</strong> ${props.department}</p>
                            <p class="mb-1"><strong>Severity:</strong> ${props.severity?.toUpperCase()}</p>
                            <p class="mb-0"><strong>Nivel:</strong> ${props.nivel}</p>
                        </div>
                    `);
                }
            }
        }).addTo(homepageWarningMap);

        // Load boundaries only once
        await loadDepartmentBoundaries();

        // Keep Peru-wide view
        const config = getMapConfig();
        homepageWarningMap.setView([config.lat, config.lng], config.zoom);

        // Update details for this day
        if (currentWarningDetails) {
            displayDailyDetail(day);
        }

    } catch (error) {
        console.error('Error loading day geometry:', error);
    }
}

async function loadWarningInfo(warningNumber) {
    try {
        const response = await fetch(`/api/warnings/${warningNumber}/info`);
        if (!response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error('Error loading warning info:', error);
        return null;
    }
}

async function loadAndDisplayDetails(warningNumber) {
    const container = document.getElementById('homepage-warning-details');

    try {
        // Load warning info
        const info = await loadWarningInfo(warningNumber);

        // Load daily details
        const detailsResponse = await fetch(`/api/warnings/${warningNumber}/details`);
        const details = await detailsResponse.json();

        currentWarningDetails = details;

        // Render main info
        container.innerHTML = `
            <div class="card mb-3">
                <div class="card-body">
                    <p class="mb-3">${info.description}</p>

                    <div class="mb-2">
                        <strong>Severity:</strong>
                        <span class="badge" style="background-color: ${getSeverityColor(info.severity)};">
                            ${info.severity.toUpperCase()}
                        </span>
                    </div>

                    <div class="mb-2">
                        <strong>Status:</strong>
                        <span class="badge bg-${info.status === 'emitido' ? 'primary' : 'danger'}">
                            ${info.status.toUpperCase()}
                        </span>
                    </div>

                    <div class="mb-2">
                        <strong>Valid:</strong> ${new Date(info.valid_from).toLocaleString('en-GB', {
                            year: 'numeric', month: '2-digit', day: '2-digit',
                            hour: '2-digit', minute: '2-digit'
                        })} - ${new Date(info.valid_until).toLocaleString('en-GB', {
                            year: 'numeric', month: '2-digit', day: '2-digit',
                            hour: '2-digit', minute: '2-digit'
                        })}
                    </div>
                </div>
            </div>

            <div id="daily-detail-container"></div>
        `;

        // Display first day's details
        displayDailyDetail(currentDay);

    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">Error loading warning details</div>`;
        console.error('Error loading details:', error);
    }
}

function displayDailyDetail(dayNumber) {
    const container = document.getElementById('daily-detail-container');
    if (!container || !currentWarningDetails) return;

    // Get unique day details (same across departments)
    const dayDetail = currentWarningDetails.departments
        .flatMap(dept => dept.days)
        .find(d => d.day_number === dayNumber);

    if (!dayDetail) {
        container.innerHTML = '<p class="text-muted">No details for this day.</p>';
        return;
    }

    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <strong>Day ${dayNumber} Details</strong>
            </div>
            <div class="card-body">
                <p>${dayDetail.description || 'No description available'}</p>
            </div>
        </div>
    `;
}

function getSeverityColor(severity) {
    const colors = {
        'rojo': '#dc3545',
        'naranja': '#fd7e14',
        'amarillo': '#ffc107',
        'verde': '#198754'
    };
    return colors[severity] || '#6c757d';
}

// Reset boundaries when modal closes
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('warning-modal');
    if (modal) {
        modal.addEventListener('hidden.bs.modal', () => {
            departmentBoundariesAdded = false;
            if (departmentBoundariesLayer && homepageWarningMap) {
                homepageWarningMap.removeLayer(departmentBoundariesLayer);
                departmentBoundariesLayer = null;
            }
        });
    }
});

// ── Config ────────────────────────────────────────────────────────────────────

// Base URL for FastAPI backend
const API_BASE = "http://localhost:8000";

// Cesium Ion access token (used for terrain, imagery, etc.)
Cesium.Ion.defaultAccessToken = "YOUR_TOKEN_HERE";

// Color mapping per constellation
const CONSTELLATION_COLORS = {
    "stations": Cesium.Color.CYAN,
    "starlink": Cesium.Color.WHITE,
    "gps-ops":  Cesium.Color.YELLOW,
    "noaa":     Cesium.Color.GREEN,
};

// Fallback color if constellation not listed
const DEFAULT_COLOR = Cesium.Color.ORANGE;


// ── Cesium Viewer Setup ───────────────────────────────────────────────────────

// Initialize Cesium viewer with most UI controls disabled
const viewer = new Cesium.Viewer("cesiumContainer", {
    terrain: Cesium.Terrain.fromWorldTerrain(),
    timeline: false,
    animation: false,
    baseLayerPicker: false,
    navigationHelpButton: false,
    homeButton: false,
    sceneModePicker: false,
    geocoder: false,
});

// Set initial camera position (zoomed out view of Earth)
viewer.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(0, 0, 30000000)
});

// Enable day/night lighting effect on globe
viewer.scene.globe.enableLighting = true;


// ── State ─────────────────────────────────────────────────────────────────────

// Raw TLE data from API
let tleRecords = [];

// Cesium entities (one per satellite)
let entities = [];


// ── API Calls ─────────────────────────────────────────────────────────────────

// Fetch satellites (optionally filtered by constellation)
async function loadSatellites(constellation = "") {
    const url = constellation
        ? `${API_BASE}/satellites?constellation=${constellation}`
        : `${API_BASE}/satellites`;

    const res = await fetch(url);
    tleRecords = await res.json();

    // Update UI stats
    document.getElementById("satCount").textContent = tleRecords.length;
    document.getElementById("statConstellation").textContent = constellation || "All";

    rebuildEntities();
}

// Fetch available constellations and populate dropdown
async function loadConstellations() {
    const res = await fetch(`${API_BASE}/constellations`);
    const groups = await res.json();
    const select = document.getElementById("constellationFilter");

    groups.forEach(g => {
        const opt = document.createElement("option");
        opt.value = g;
        opt.textContent = g;
        select.appendChild(opt);
    });
}


// ── Satellite Math / Conversion ───────────────────────────────────────────────

// Convert TLE document into satellite.js satrec object
function buildSatrec(doc) {
    return satellite.twoline2satrec(
        doc.TLE_LINE1,
        doc.TLE_LINE2
    );
}

// Propagate satellite to current time and convert to Cesium position
function propagate(satrec) {
    const now = new Date();

    // Get ECI position/velocity
    const posVel = satellite.propagate(satrec, now);
    if (!posVel.position) return null;

    // Convert to geodetic coordinates (lat/lon/alt)
    const gmst = satellite.gstime(now);
    const geo = satellite.eciToGeodetic(posVel.position, gmst);

    const lat = satellite.degreesLat(geo.latitude);
    const lon = satellite.degreesLong(geo.longitude);
    const alt = geo.height * 1000; // km → meters (Cesium expects meters)

    return Cesium.Cartesian3.fromDegrees(lon, lat, alt);
}


// ── Entity Management ─────────────────────────────────────────────────────────

// Build (or rebuild) all satellite entities in the scene
function rebuildEntities() {
    // Remove old entities
    entities.forEach(e => viewer.entities.remove(e));
    entities = [];

    tleRecords.forEach(doc => {
        const satrec = satellite.twoline2satrec(doc.TLE_LINE1, doc.TLE_LINE2);

        let lastPosition = null; // fallback if propagation fails
        const color = CONSTELLATION_COLORS[doc.constellation] ?? DEFAULT_COLOR;

        const entity = viewer.entities.add({
            // Dynamic position updated every frame
            position: new Cesium.CallbackProperty(() => {
                const pos = propagate(satrec);
                if (pos) lastPosition = pos;
                return lastPosition;
            }, false),

            // Visual point representing satellite
            point: {
                pixelSize: 6,
                color: color.withAlpha(0.9),
                outlineColor: Cesium.Color.WHITE.withAlpha(0.3),
                outlineWidth: 1,
            },

            // Label shown near satellite (with distance-based visibility)
            label: {
                text: doc.OBJECT_NAME,
                font: "11px sans-serif",
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                pixelOffset: new Cesium.Cartesian2(10, 0),
                distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 8000000),
            },

            // Attach original data for later use (click handler)
            properties: doc,
        });

        entities.push(entity);
    });
}


// ── Interaction (Click Handling) ──────────────────────────────────────────────

// Handle clicks on satellites
viewer.screenSpaceEventHandler.setInputAction(click => {
    const picked = viewer.scene.pick(click.position);

    // Ignore if nothing selected
    if (!Cesium.defined(picked) || !picked.id) return;

    const doc = picked.id.properties;
    if (!doc) return;

    // Show satellite info panel
    document.getElementById("selectedInfo").style.display = "block";
    document.getElementById("selName").textContent  = doc.OBJECT_NAME?.getValue() ?? "—";
    document.getElementById("selNorad").textContent = doc.NORAD_CAT_ID?.getValue() ?? "—";
    document.getElementById("selInc").textContent   = doc.INCLINATION?.getValue()?.toFixed(2) ?? "—";

    // Compute current altitude dynamically
    const satrec = satellite.twoline2satrec(
        doc.TLE_LINE1?.getValue(),
        doc.TLE_LINE2?.getValue()
    );

    const posVel = satellite.propagate(satrec, new Date());
    if (posVel.position) {
        const gmst = satellite.gstime(new Date());
        const geo  = satellite.eciToGeodetic(posVel.position, gmst);
        document.getElementById("selAlt").textContent = geo.height.toFixed(1);
    }

}, Cesium.ScreenSpaceEventType.LEFT_CLICK);


// ── Initialization ────────────────────────────────────────────────────────────

// Run once DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    // Reload satellites when filter changes
    document.getElementById("constellationFilter").addEventListener("change", e => {
        loadSatellites(e.target.value);
    });

    // Initial data load
    loadConstellations();
    loadSatellites();
});
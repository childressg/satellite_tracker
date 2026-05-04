// ── Config ────────────────────────────────────────────────────────────────────

// Base URL for FastAPI backend
const API_BASE = "http://localhost:8000";

// Cesium Ion access token (used for terrain, imagery, etc.)
Cesium.Ion.defaultAccessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI4NzZmOTM2MC1hODI5LTRjOGYtYTRjZS04MjRlOGM0ZGNkMWMiLCJpZCI6NDE4Nzc2LCJpYXQiOjE3NzYyOTE3NTJ9.t1pp4TfMnjZ12dm2K8jTeI_9wtSQ1ZQysbHKRbaoar0";

// Color mapping per constellation
const CONSTELLATION_COLORS = {
    "stations": Cesium.Color.CYAN,
    "visual": Cesium.Color.LIGHTCYAN,
    "analyst": Cesium.Color.MAGENTA,

    "fengyun-1c-debris": Cesium.Color.DARKGRAY,
    "iridium-33-debris": Cesium.Color.GRAY,
    "cosmos-2251-debris": Cesium.Color.DIMGRAY,

    "weather": Cesium.Color.BLUE,
    "resource": Cesium.Color.GREEN,
    "sarsat": Cesium.Color.YELLOWGREEN,
    "dmc": Cesium.Color.DARKGREEN,
    "tdrss": Cesium.Color.DARKBLUE,
    "argos": Cesium.Color.TEAL,

    "planet": Cesium.Color.PERU,
    "spire": Cesium.Color.CHOCOLATE,

    "geo": Cesium.Color.GOLD,
    "intelsat": Cesium.Color.KHAKI,
    "ses": Cesium.Color.BEIGE,
    "eutelsat": Cesium.Color.WHEAT,
    "telesat": Cesium.Color.TAN,

    "starlink": Cesium.Color.WHITE,
    "oneweb": Cesium.Color.HOTPINK,
    "qianfan": Cesium.Color.fromCssColorString("#ff7f50"),   // coral
    "hulianwang": Cesium.Color.fromCssColorString("#ff1493"), // deep pink
    "kuiper": Cesium.Color.fromCssColorString("#8a2be2"),     // blue violet

    "iridium-NEXT": Cesium.Color.SILVER,
    "orbcomm": Cesium.Color.DARKORANGE,
    "globalstar": Cesium.Color.ORANGERED,

    "amateur": Cesium.Color.MEDIUMSPRINGGREEN,
    "satnogs": Cesium.Color.SPRINGGREEN,

    "x-comm": Cesium.Color.CRIMSON,
    "other-comm": Cesium.Color.FIREBRICK,

    "gnss": Cesium.Color.YELLOW,
    "gps-ops": Cesium.Color.GOLDENROD,
    "glo-ops": Cesium.Color.ORANGE,
    "galileo": Cesium.Color.DODGERBLUE,
    "beidou": Cesium.Color.RED,
    "sbas": Cesium.Color.LIGHTYELLOW,

    "science": Cesium.Color.PURPLE,
    "geodetic": Cesium.Color.INDIGO,
    "engineering": Cesium.Color.SLATEBLUE,
    "education": Cesium.Color.LAVENDER,
    "military": Cesium.Color.DARKRED,
    "radar": Cesium.Color.MAROON,

    "cubesat": Cesium.Color.AQUAMARINE
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
    const posVel = satellite.propagate(satrec, now);

    if (!posVel || !posVel.position) return null;

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
    if (!Cesium.defined(picked) || !picked.id) return;

    const doc = picked.id.properties;
    if (!doc) return;

    // Constants
    const MU  = 3.986004418e14;
    const R_E = 6371.0;

    // Parse orbital elements directly from TLE Line 2
    const tl2  = doc.TLE_LINE2?.getValue() ?? "";
    const tl1  = doc.TLE_LINE1?.getValue() ?? "";
    const inc  = tl2 ? parseFloat(tl2.substring(8,  16)) : 0;
    const raan = tl2 ? parseFloat(tl2.substring(17, 25)) : 0;
    const ecc  = tl2 ? parseFloat("0." + tl2.substring(26, 33)) : 0;
    const mm   = tl2 ? parseFloat(tl2.substring(52, 63)) : null;
    const constellation = doc.constellation?.getValue() ?? "—";

    // Live altitude from propagation
    let alt = null;
    const satrec = satellite.twoline2satrec(tl1, tl2);
    const posVel = satellite.propagate(satrec, new Date());
    if (posVel && posVel.position) {
        const gmst = satellite.gstime(new Date());
        const geo  = satellite.eciToGeodetic(posVel.position, gmst);
        alt = geo.height.toFixed(1);
    }

    // Derived orbital parameters from mean motion
    let period = null, apogee = null, perigee = null;
    if (mm) {
        const n  = mm * 2 * Math.PI / 86400;
        const a  = Math.pow(MU / (n * n), 1/3) / 1000;
        period  = (1440 / mm).toFixed(1);
        apogee  = (a * (1 + ecc) - R_E).toFixed(1);
        perigee = (a * (1 - ecc) - R_E).toFixed(1);
    }

    // Update UI
    document.getElementById("selectedInfo").style.display   = "block";
    document.getElementById("selName").textContent          = doc.OBJECT_NAME?.getValue() ?? "—";
    document.getElementById("selNorad").textContent         = doc.NORAD_CAT_ID?.getValue() ?? "—";
    document.getElementById("selConstellation").textContent = constellation;
    document.getElementById("selAlt").textContent           = alt ?? "—";
    document.getElementById("selPeriod").textContent        = period ?? "—";
    document.getElementById("selInc").textContent           = inc ? inc.toFixed(2) : "—";
    document.getElementById("selEcc").textContent           = ecc ? ecc.toFixed(6) : "—";
    document.getElementById("selApogee").textContent        = apogee ?? "—";
    document.getElementById("selPerigee").textContent       = perigee ?? "—";
    document.getElementById("selRaan").textContent          = raan ? raan.toFixed(2) : "—";

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
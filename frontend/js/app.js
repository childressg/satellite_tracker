// Config
const API_BASE = "http://localhost:8000";
Cesium.Ion.defaultAccessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI4NzZmOTM2MC1hODI5LTRjOGYtYTRjZS04MjRlOGM0ZGNkMWMiLCJpZCI6NDE4Nzc2LCJpYXQiOjE3NzYyOTE3NTJ9.t1pp4TfMnjZ12dm2K8jTeI_9wtSQ1ZQysbHKRbaoar0";

const CONSTELLATION_COLORS = {
    "stations": Cesium.Color.CYAN,
    "starlink":  Cesium.Color.WHITE,
    "gps-ops":  Cesium.Color.YELLOW,
    "noaa":     Cesium.Color.GREEN,
};

const DEFAULT_COLOR = Cesium.Color.ORANGE;

// Cesium viewer setup
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

viewer.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(0, 0, 30000000) // longitude, latitude, height in meters
});

viewer.scene.globe.enableLighting = true;

// State
let tleRecords = []; // raw TLE docs from API
let entities = []; // Cesium entities, one per satellite

// Fetch TLEs from FastAPI
async function loadSatellites(constellation = "") {
    const url = constellation
        ? `${API_BASE}/satellites?constellation=${constellation}`
        : `${API_BASE}/satellites`;

    const res = await fetch(url);
    tleRecords = await res.json();

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

// Build a satrec from a TLE document
function buildSatrec(doc) {
    // satellite.js expects classic TLE line strings, but CelesTrak JSON
    // gives the fields directly
    return satellite.twoline2satrec(
        doc.TLE_LINE1,
        doc.TLE_LINE2
    );
}

// Propagate a satrec to current time > Cesium Cartesian3
function propagate(satrec) {
    const now = new Date();
    const posVel = satellite.propagate(satrec, now);
    if (!posVel.position) return null;

    const gmst = satellite.gstime(now);
    const geo = satellite.eciToGeodetic(posVel.position, gmst);

    const lat = satellite.degreesLat(geo.latitude);
    const lon = satellite.degreesLong(geo.longitude);
    const alt = geo.height * 1000; // km > meters for Cesium

    return Cesium.Cartesian3.fromDegrees(lon, lat, alt);
}

// Create / recreate all Cesium point entities
function rebuildEntities() {
    // remove old entities
    entities.forEach(e => viewer.entities.remove(e))
    entities = [];

    tleRecords.forEach(doc => {
        const satrec = satellite.twoline2satrec(doc.TLE_LINE1, doc.TLE_LINE2);
        let lastPosition = null;
        const color = CONSTELLATION_COLORS[doc.constellation] ?? DEFAULT_COLOR;

        const entity = viewer.entities.add({
            position: new Cesium.CallbackProperty(() => {
                const pos = propagate(satrec);
                if (pos) lastPosition = pos;
                return lastPosition;
            }, false),
            point: {
                pixelSize: 6,
                color: color.withAlpha(0.9),
                outlineColor: Cesium.Color.WHITE.withAlpha(0.3),
                outlineWidth: 1,
                // disableDepthTestDistance: Number.POSITIVE_INFINITY,
            },
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
            properties: doc,
        });

        entities.push(entity);
    });
}

// Click handler (show selected satellite info)
viewer.screenSpaceEventHandler.setInputAction(click => {
    const picked = viewer.scene.pick(click.position);
    if (!Cesium.defined(picked) || !picked.id) return;

    const doc = picked.id.properties;
    if (!doc) return;

    document.getElementById("selectedInfo").style.display = "block";
    document.getElementById("selName").textContent  = doc.OBJECT_NAME?.getValue() ?? "—";
    document.getElementById("selNorad").textContent = doc.NORAD_CAT_ID?.getValue() ?? "—";
    document.getElementById("selInc").textContent   = doc.INCLINATION?.getValue()?.toFixed(2) ?? "—";

    // compute current altitude for display
    const satrec = satellite.twoline2satrec(
        doc.TLE_LINE1?.getValue(),
        doc.TLE_LINE2?.getValue()
    );
    const posVel = satellite.propagate(satrec, new Date());
    if (posVel.position) {
        const gmst = satellite.gstime(new Date());
        const geo  = satellite.eciToGeodetic(posVel.position, gmst);
        document.getElementById("selAlt").textContent = (geo.height).toFixed(1);
    }

}, Cesium.ScreenSpaceEventType.LEFT_CLICK);

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("constellationFilter").addEventListener("change", e => {
        loadSatellites(e.target.value);
    });

    loadConstellations();
    loadSatellites();
});
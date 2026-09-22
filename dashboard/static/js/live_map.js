(function () {
    "use strict";

    const INDIA_CENTER = [20.59, 78.96];
    const ZOOM = 6;
    const REFRESH_MS = 5000;

    let map = null;
    let clusterGroup = null;
    const markers = {};

    function initMap() {
        const el = document.getElementById("map");
        if (!el) return;

        map = L.map("map", {
            center: INDIA_CENTER,
            zoom: ZOOM,
            zoomControl: true,
            preferCanvas: true,
        });

        map.setView(INDIA_CENTER, ZOOM);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19,
        }).addTo(map);

        if (typeof L.markerClusterGroup === "function") {
            clusterGroup = L.markerClusterGroup({
                maxClusterRadius: 45,
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: false,
                zoomToBoundsOnClick: true,
            });
            map.addLayer(clusterGroup);
        }
    }

    function emojiFor(asset_type) {
        return {
            "TRUCK": "🚛",
            "WAREHOUSE": "🏭",
            "VEHICLE_GATEWAY": "📡",
            "SENSOR": "🌡️",
            "API_GATEWAY": "☁️",
            "APPLICATION": "📱",
            "AUTH_SYSTEM": "🔐",
            "DATABASE": "💾",
            "SUPPLIER": "📦",
        }[asset_type] || "📍";
    }

    function riskClass(score) {
        if (score >= 75) return "danger";
        if (score >= 50) return "warn";
        if (score >= 25) return "info";
        return "safe";
    }

    function makeIcon(asset) {
        const emoji = emojiFor(asset.asset_type);
        const cls = riskClass(asset.risk_score);
        return L.divIcon({
            className: "map-marker " + cls,
            html: `<div class="marker-inner">${emoji}</div>`,
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -16],
        });
    }

    function popupHtml(a) {
        return `
            <div class="map-popup">
                <div class="map-popup-id">${a.asset_id}</div>
                <div class="map-popup-name">${a.name}</div>
                <div class="map-popup-row">
                    <span class="pill">${a.asset_type}</span>
                    <span class="badge state-${a.state}">${a.state}</span>
                    <span class="badge ${riskClass(a.risk_score)}">risk ${Number(a.risk_score).toFixed(1)}</span>
                </div>
                <div class="map-popup-coords">${Number(a.lat).toFixed(4)}, ${Number(a.lon).toFixed(4)}</div>
            </div>
        `;
    }

    function isInIndia(lat, lon) {
        return lat >= 6.0 && lat <= 37.0 && lon >= 68.0 && lon <= 98.0;
    }

    const trails = {};
    let lastSessionId = null;

    function updateTrail(asset) {
        if (!map || !isInIndia(asset.lat, asset.lon)) return;
        if (!trails[asset.asset_id]) {
            trails[asset.asset_id] = L.polyline([], {
                color: "#1f6feb",
                weight: 2,
                opacity: 0.6,
            }).addTo(map);
        }

        const latlngs = trails[asset.asset_id].getLatLngs();
        const last = latlngs[latlngs.length - 1];
        const next = [asset.lat, asset.lon];

        // If last point is more than 1 degree away, RESET the trail
        if (last && (Math.abs(last.lat - next[0]) > 1.0 ||
                     Math.abs(last.lng - next[1]) > 1.0)) {
            trails[asset.asset_id].setLatLngs([next]);
            return;
        }

        // Skip if no meaningful change
        if (last && last.lat === next[0] && last.lng === next[1]) return;

        trails[asset.asset_id].addLatLng(next);

        // Cap trail length to last 200 points
        const pts = trails[asset.asset_id].getLatLngs();
        if (pts.length > 200) {
            pts.splice(0, pts.length - 200);
            trails[asset.asset_id].setLatLngs(pts);
        }
    }

    async function refreshMap() {
        if (!map) return;
        let data;
        try {
            data = await fetch("/live/map-data").then(r => r.json());
        } catch (e) {
            console.warn("Map data fetch failed", e);
            return;
        }

        // Detect backend restart
        if (data.session_id && data.session_id !== lastSessionId) {
            if (lastSessionId !== null) {
                console.log("Backend restarted — clearing all trails");
                Object.values(trails).forEach(t => t.setLatLngs([]));
            }
            lastSessionId = data.session_id;
        }

        // Filter out invalid coordinates
        const validAssets = (data.assets || []).filter(a => isInIndia(a.lat, a.lon));

        const seen = new Set();

        validAssets.forEach(asset => {
            seen.add(asset.asset_id);
            const latlng = [asset.lat, asset.lon];

            if (asset.asset_type === "TRUCK") {
                updateTrail(asset);
            }

            if (markers[asset.asset_id]) {
                const m = markers[asset.asset_id];
                const oldLatLng = m.getLatLng();
                if (Math.abs(oldLatLng.lat - asset.lat) > 0.0001 || Math.abs(oldLatLng.lng - asset.lon) > 0.0001) {
                    m.setLatLng(latlng);
                    if (clusterGroup && typeof clusterGroup.refreshClusters === "function") {
                        try {
                            clusterGroup.refreshClusters(m);
                        } catch (e) {
                            // cluster refresh safeguard
                        }
                    }
                }
                m.setIcon(makeIcon(asset));
                m.setPopupContent(popupHtml(asset));
            } else {
                const m = L.marker(latlng, { icon: makeIcon(asset) })
                    .bindPopup(popupHtml(asset));
                markers[asset.asset_id] = m;
                if (clusterGroup) {
                    clusterGroup.addLayer(m);
                } else {
                    m.addTo(map);
                }
            }
        });

        // Remove markers for assets no longer present or outside India
        Object.keys(markers).forEach(aid => {
            if (!seen.has(aid)) {
                if (clusterGroup) {
                    clusterGroup.removeLayer(markers[aid]);
                } else {
                    map.removeLayer(markers[aid]);
                }
                delete markers[aid];
            }
        });
    }

    function boot() {
        initMap();
        refreshMap();
        setInterval(refreshMap, REFRESH_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();

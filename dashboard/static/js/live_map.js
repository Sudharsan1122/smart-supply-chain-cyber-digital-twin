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

    async function refreshMap() {
        if (!map) return;
        let data;
        try {
            data = await fetch("/live/map-data").then(r => r.json());
        } catch (e) {
            console.warn("Map data fetch failed", e);
            return;
        }

        const seen = new Set();

        (data.assets || []).forEach(asset => {
            seen.add(asset.asset_id);
            const latlng = [asset.lat, asset.lon];

            if (markers[asset.asset_id]) {
                const m = markers[asset.asset_id];
                const oldLatLng = m.getLatLng();
                if (Math.abs(oldLatLng.lat - asset.lat) > 0.0001 || Math.abs(oldLatLng.lng - asset.lon) > 0.0001) {
                    m.setLatLng(latlng);
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

        // Remove markers for assets no longer present
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

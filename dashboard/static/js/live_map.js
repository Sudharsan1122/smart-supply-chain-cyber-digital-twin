(function () {
    "use strict";

    const INDIA_CENTER = [20.5937, 78.9629];
    const ZOOM = 5;
    const REFRESH_MS = 5000;

    let map = null;
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

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19,
        }).addTo(map);
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
                markers[asset.asset_id].setLatLng(latlng);
                markers[asset.asset_id].setIcon(makeIcon(asset));
                markers[asset.asset_id].setPopupContent(popupHtml(asset));
            } else {
                markers[asset.asset_id] = L.marker(latlng, { icon: makeIcon(asset) })
                    .addTo(map)
                    .bindPopup(popupHtml(asset));
            }
        });

        // Remove markers for assets no longer present
        Object.keys(markers).forEach(aid => {
            if (!seen.has(aid)) {
                map.removeLayer(markers[aid]);
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

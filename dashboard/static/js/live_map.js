(function () {
    "use strict";

    const INDIA_CENTER = [21.0, 79.0];
    const ZOOM = 5;
    const REFRESH_MS = 5000;

    let map = null;
    let clusterGroup = null;
    const markers = {};
    const markerLayer = {}; // tracks whether marker is in 'map' or 'cluster'
    const lastAssetsById = {};

    // Weather overlay state
    let weatherData = {};
    let showWeather = true;

    // Geofence state
    let geofenceDefs = {};
    const geofences = {};

    // Timeline playback state
    let playbackData = null;
    let playbackTimer = null;
    let currentIndex = 0;
    let isPlayingBack = false;

    function initMap() {
        const el = document.getElementById("map");
        if (!el) return;

        map = L.map("map", {
            center: INDIA_CENTER,
            zoom: ZOOM,
            zoomControl: true,
            preferCanvas: false,
        });

        map.setView(INDIA_CENTER, ZOOM);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19,
        }).addTo(map);

        if (typeof L.markerClusterGroup === "function") {
            clusterGroup = L.markerClusterGroup({
                maxClusterRadius: 35,
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: false,
                zoomToBoundsOnClick: true,
            });
            map.addLayer(clusterGroup);
        }

        // Weather toggle control in top-right corner
        const weatherControl = L.control({ position: "topright" });
        weatherControl.onAdd = function () {
            const div = L.DomUtil.create("div", "weather-toggle");
            div.innerHTML = `<label><input type="checkbox" id="weather-toggle" checked> 🌤️ Weather</label>`;
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        weatherControl.addTo(map);

        document.addEventListener("change", (e) => {
            if (e.target && e.target.id === "weather-toggle") {
                showWeather = e.target.checked;
                refreshWeatherIcons();
            }
        });
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

    function haversineKm(lat1, lon1, lat2, lon2) {
        const R = 6371.0;
        const toRad = d => (d * Math.PI) / 180.0;
        const phi1 = toRad(lat1);
        const phi2 = toRad(lat2);
        const dphi = toRad(lat2 - lat1);
        const dlam = toRad(lon2 - lon1);
        const a = Math.sin(dphi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dlam / 2) ** 2;
        return 2 * R * Math.asin(Math.sqrt(a));
    }

    function geofenceFor(assetId) {
        return geofenceDefs[assetId] || null;
    }

    function geofenceStatus(asset) {
        if (asset.asset_type !== "TRUCK") return { state: "ok", distanceKm: 0 };
        const zone = geofenceFor(asset.asset_id);
        if (!zone || !zone.center) return { state: "ok", distanceKm: 0 };
        const dist = haversineKm(asset.lat, asset.lon, zone.center[0], zone.center[1]);
        if (dist > zone.radius_km) {
            return { state: "breach", distanceKm: dist, allowedKm: zone.radius_km };
        }
        if (dist > zone.radius_km - (zone.buffer_km || 0)) {
            return { state: "warning", distanceKm: dist, allowedKm: zone.radius_km };
        }
        return { state: "ok", distanceKm: dist, allowedKm: zone.radius_km };
    }

    async function fetchGeofences() {
        try {
            const res = await fetch("/live/geofences");
            if (!res.ok) return;
            geofenceDefs = await res.json();
        } catch (e) {
            console.warn("Geofences fetch failed:", e);
        }
    }

    function drawGeofences(data) {
        (data.assets || []).forEach(asset => {
            if (asset.asset_type !== "TRUCK") return;
            const zone = geofenceFor(asset.asset_id);
            if (!zone) return;

            if (!geofences[asset.asset_id]) {
                geofences[asset.asset_id] = L.circle(
                    [zone.center[0], zone.center[1]],
                    {
                        radius: zone.radius_km * 1000,
                        color: "#1f6feb",
                        fillColor: "#58a6ff",
                        weight: 2,
                        opacity: 0.55,
                        fillOpacity: 0.05,
                        dashArray: "6 6",
                        interactive: false,
                    }
                ).addTo(map);
            }
        });
    }

    function weatherIcon(condition) {
        const iconMap = {
            "Clear": "☀️",
            "Clouds": "⛅",
            "Rain": "🌧️",
            "Drizzle": "🌦️",
            "Thunderstorm": "⛈️",
            "Snow": "🌨️",
            "Mist": "🌫️",
            "Fog": "🌫️",
            "Haze": "🌫️",
            "Smoke": "🌫️",
        };
        return iconMap[condition] || "🌡️";
    }

    function weatherClass(w) {
        if (!w) return "";
        const temp = w.temp != null ? w.temp : w.temperature_c;
        if (temp >= 40 || temp <= -10) return "danger";
        if (temp >= 35 || w.condition === "Thunderstorm") return "warn";
        return "safe";
    }

    function windDirection(deg) {
        if (deg == null) return "";
        const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
        return dirs[Math.round(deg / 45) % 8];
    }

    function makeIcon(asset) {
        const emoji = emojiFor(asset.asset_type);
        const gf = geofenceStatus(asset);
        let cls = riskClass(asset.risk_score);
        if (gf.state === "breach") {
            cls = "danger";
        } else if (gf.state === "warning" && cls !== "danger") {
            cls = "warn";
        }
        const w = weatherData[asset.asset_id];
        const temp = w ? (w.temp != null ? w.temp : w.temperature_c) : null;
        let weatherHtml = "";
        if (showWeather && w && temp != null) {
            const wIcon = weatherIcon(w.condition);
            const wCls = weatherClass(w);
            weatherHtml = `<div class="weather-badge ${wCls}">${wIcon} ${Math.round(temp)}°</div>`;
        }
        return L.divIcon({
            className: "map-marker " + cls,
            html: `<div class="marker-inner">${emoji}</div>${weatherHtml}`,
            iconSize: [32, 48],
            iconAnchor: [16, 16],
            popupAnchor: [0, -16],
        });
    }

    function popupHtml(a) {
        const w = weatherData[a.asset_id];
        const temp = w ? (w.temp != null ? w.temp : w.temperature_c) : null;
        const hum = w ? (w.humidity != null ? w.humidity : w.humidity_pct) : null;
        let weatherSection = "";
        if (w && temp != null) {
            const wIcon = weatherIcon(w.condition);
            const windKmh = w.wind_speed_ms != null ? Math.round(w.wind_speed_ms * 3.6) : "—";
            const windDir = windDirection(w.wind_deg);
            weatherSection = `
                <div class="map-popup-weather">
                    <div><strong>Weather:</strong> ${wIcon} ${Number(temp).toFixed(1)}°C, ${hum}% humidity${w.city ? ", " + w.city : ""}</div>
                    <div><strong>Wind:</strong> ${windKmh} km/h ${windDir ? "from " + windDir : ""}</div>
                </div>
            `;
        }

        const gf = geofenceStatus(a);
        let geofenceSection = "";
        if (gf.state === "breach") {
            geofenceSection = `<div class="map-popup-weather" style="color:#f85149;"><strong>🚨 Geofence Breach:</strong> ${Math.round(gf.distanceKm)} km from center (allowed ${gf.allowedKm} km)</div>`;
        } else if (gf.state === "warning") {
            geofenceSection = `<div class="map-popup-weather" style="color:#d29922;"><strong>⚠️ Geofence Buffer:</strong> ${Math.round(gf.distanceKm)} km from center (limit ${gf.allowedKm} km)</div>`;
        }

        return `
            <div class="map-popup">
                <div class="map-popup-id">${a.asset_id}</div>
                <div class="map-popup-name">${a.name}</div>
                <div class="map-popup-row">
                    <span class="pill">${a.asset_type}</span>
                    <span class="badge state-${a.state}">${a.state}</span>
                    <span class="badge ${riskClass(a.risk_score)}">risk ${Number(a.risk_score).toFixed(1)}</span>
                </div>
                ${geofenceSection}
                ${weatherSection}
                <div class="map-popup-coords">${Number(a.lat).toFixed(4)}, ${Number(a.lon).toFixed(4)}</div>
            </div>
        `;
    }

    function refreshWeatherIcons() {
        Object.keys(markers).forEach(aid => {
            const asset = lastAssetsById[aid];
            const m = markers[aid];
            if (asset && m) {
                m.setIcon(makeIcon(asset));
                m.setPopupContent(popupHtml(asset));
            }
        });
    }

    async function fetchWeather() {
        try {
            const res = await fetch("/live/weather-batch");
            if (!res.ok) return;
            weatherData = await res.json();
            refreshWeatherIcons();
        } catch (e) {
            console.warn("Weather fetch failed:", e);
        }
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
        if (!map || isPlayingBack) return;
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

        drawGeofences({ assets: validAssets });

        const seen = new Set();

        validAssets.forEach(asset => {
            seen.add(asset.asset_id);
            lastAssetsById[asset.asset_id] = asset;
            const latlng = [asset.lat, asset.lon];

            if (asset.asset_type === "TRUCK") {
                updateTrail(asset);
            }

            const unclustered = asset.asset_type === "TRUCK" || asset.asset_type === "WAREHOUSE";

            if (markers[asset.asset_id]) {
                const m = markers[asset.asset_id];
                const oldLatLng = m.getLatLng();
                if (Math.abs(oldLatLng.lat - asset.lat) > 0.0001 || Math.abs(oldLatLng.lng - asset.lon) > 0.0001) {
                    m.setLatLng(latlng);
                    if (!unclustered && clusterGroup && typeof clusterGroup.refreshClusters === "function") {
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
                if (!unclustered && clusterGroup) {
                    clusterGroup.addLayer(m);
                    markerLayer[asset.asset_id] = "cluster";
                } else {
                    m.addTo(map);
                    markerLayer[asset.asset_id] = "map";
                }
            }
        });

        // Remove markers for assets no longer present or outside India
        Object.keys(markers).forEach(aid => {
            if (!seen.has(aid)) {
                if (markerLayer[aid] === "cluster" && clusterGroup) {
                    clusterGroup.removeLayer(markers[aid]);
                } else {
                    map.removeLayer(markers[aid]);
                }
                delete markers[aid];
                delete markerLayer[aid];
                delete lastAssetsById[aid];
            }
        });
    }

    // ------------------------------------------------------------------
    // Timeline Playback
    // ------------------------------------------------------------------
    async function loadPlayback(minutes = 30) {
        try {
            const clampedMins = Math.min(120, Math.max(1, parseInt(minutes, 10) || 30));
            const res = await fetch(`/live/playback?minutes=${clampedMins}&step=10`);
            if (!res.ok) return;
            playbackData = await res.json();
            const slider = document.getElementById("time-slider");
            if (slider && playbackData.timestamps) {
                slider.max = Math.max(0, playbackData.timestamps.length - 1);
                slider.value = 0;
            }
            currentIndex = 0;
        } catch (e) {
            console.warn("Playback load failed:", e);
        }
    }

    function applyPlaybackFrame(idx) {
        if (!playbackData || !playbackData.timestamps || !playbackData.timestamps.length) return;
        const ts = playbackData.timestamps[idx];
        if (!ts) return;

        const d = new Date(ts);
        const label = document.getElementById("time-label");
        if (label) {
            label.textContent = d.toLocaleTimeString() + " (replay)";
        }

        // Move each truck to its position at this timestamp
        Object.entries(playbackData.trucks || {}).forEach(([truckId, positions]) => {
            const pos = positions[idx];
            if (pos && markers[truckId] && isInIndia(pos.lat, pos.lon)) {
                markers[truckId].setLatLng([pos.lat, pos.lon]);
                if (lastAssetsById[truckId]) {
                    lastAssetsById[truckId] = {
                        ...lastAssetsById[truckId],
                        lat: pos.lat,
                        lon: pos.lon,
                    };
                    markers[truckId].setIcon(makeIcon(lastAssetsById[truckId]));
                }
            }
            if (trails[truckId]) {
                const slicePts = [];
                for (let i = 0; i <= idx; i++) {
                    const p = positions[i];
                    if (!p || !isInIndia(p.lat, p.lon)) continue;
                    const prev = slicePts[slicePts.length - 1];
                    if (prev && (Math.abs(prev[0] - p.lat) > 1.0 || Math.abs(prev[1] - p.lon) > 1.0)) {
                        slicePts.length = 0;
                    }
                    slicePts.push([p.lat, p.lon]);
                }
                trails[truckId].setLatLngs(slicePts);
            }
        });

        checkEventsAtTime(ts);
    }

    function checkEventsAtTime(ts) {
        if (!playbackData || !playbackData.events) return;
        const curTime = new Date(ts).getTime();
        const recentEvents = playbackData.events.filter(e => {
            const evTime = new Date(e.t || e.timestamp).getTime();
            return Math.abs(evTime - curTime) < 60000;
        });

        recentEvents.forEach(ev => {
            const assetId = ev.asset || ev.asset_id;
            const targets = [assetId, ev.parent_asset].filter(Boolean);
            targets.forEach(tid => {
                const m = markers[tid];
                const el = m ? (typeof m.getElement === "function" ? m.getElement() : m._icon) : null;
                if (el) {
                    el.classList.add("flash-red");
                    setTimeout(() => {
                        el.classList.remove("flash-red");
                    }, 2000);
                }
            });
        });

        const banner = document.getElementById("playback-event-banner");
        if (banner) {
            if (recentEvents.length > 0) {
                const latest = recentEvents[recentEvents.length - 1];
                const evTs = new Date(latest.t || latest.timestamp).toLocaleTimeString();
                const evAsset = latest.asset || latest.asset_id || "SYSTEM";
                const evTitle = latest.title || latest.detail || latest.kind;
                banner.style.display = "block";
                banner.textContent = `⚡ [${evTs}] ${evAsset}: ${evTitle}`;
            } else {
                banner.style.display = "none";
            }
        }
    }

    function initPlaybackControls() {
        const playBtn = document.getElementById("play-btn");
        const pauseBtn = document.getElementById("pause-btn");
        const stopBtn = document.getElementById("stop-btn");
        const slider = document.getElementById("time-slider");
        const winSelect = document.getElementById("playback-window");
        const label = document.getElementById("time-label");
        const banner = document.getElementById("playback-event-banner");

        if (!playBtn || !pauseBtn || !stopBtn || !slider || !winSelect) return;

        playBtn.addEventListener("click", async () => {
            const mins = parseInt(winSelect.value, 10) || 30;
            if (!isPlayingBack) {
                await loadPlayback(mins);
                isPlayingBack = true;
            }
            if (!playbackData || !playbackData.timestamps || !playbackData.timestamps.length) {
                if (label) label.textContent = "No data — run traffic generator first";
                if (banner) {
                    banner.style.display = "block";
                    banner.textContent = "No data — run traffic generator first";
                }
                isPlayingBack = false;
                return;
            }
            playBtn.style.display = "none";
            pauseBtn.style.display = "inline-block";

            if (playbackTimer) clearInterval(playbackTimer);
            playbackTimer = setInterval(() => {
                if (currentIndex >= playbackData.timestamps.length - 1) {
                    clearInterval(playbackTimer);
                    playbackTimer = null;
                    playBtn.style.display = "inline-block";
                    pauseBtn.style.display = "none";
                    return;
                }
                currentIndex++;
                slider.value = currentIndex;
                applyPlaybackFrame(currentIndex);
            }, 200); // 5 fps
        });

        pauseBtn.addEventListener("click", () => {
            if (playbackTimer) {
                clearInterval(playbackTimer);
                playbackTimer = null;
            }
            playBtn.style.display = "inline-block";
            pauseBtn.style.display = "none";
        });

        stopBtn.addEventListener("click", () => {
            if (playbackTimer) {
                clearInterval(playbackTimer);
                playbackTimer = null;
            }
            isPlayingBack = false;
            playbackData = null;
            slider.value = slider.max;
            if (label) label.textContent = "LIVE";
            if (banner) banner.style.display = "none";
            playBtn.style.display = "inline-block";
            pauseBtn.style.display = "none";
            refreshMap();
        });

        slider.addEventListener("input", async (e) => {
            if (!isPlayingBack) {
                const mins = parseInt(winSelect.value, 10) || 30;
                await loadPlayback(mins);
                isPlayingBack = true;
            }
            if (!playbackData || !playbackData.timestamps || !playbackData.timestamps.length) {
                if (label) label.textContent = "No data — run traffic generator first";
                isPlayingBack = false;
                return;
            }
            currentIndex = parseInt(e.target.value, 10) || 0;
            applyPlaybackFrame(currentIndex);
        });

        winSelect.addEventListener("change", async () => {
            if (isPlayingBack) {
                const mins = parseInt(winSelect.value, 10) || 30;
                await loadPlayback(mins);
                applyPlaybackFrame(0);
            }
        });
    }

    function boot() {
        initMap();
        initPlaybackControls();
        fetchGeofences().then(async () => {
            await refreshMap();
            const params = new URLSearchParams(window.location.search);
            const pctParam = params.get("playback_pct");
            if (pctParam !== null) {
                const pct = Math.min(100, Math.max(0, parseInt(pctParam, 10) || 0));
                await loadPlayback(30);
                if (playbackData && playbackData.timestamps && playbackData.timestamps.length) {
                    isPlayingBack = true;
                    const maxIdx = playbackData.timestamps.length - 1;
                    currentIndex = Math.round((pct / 100) * maxIdx);
                    const slider = document.getElementById("time-slider");
                    if (slider) slider.value = currentIndex;
                    const playBtn = document.getElementById("play-btn");
                    const pauseBtn = document.getElementById("pause-btn");
                    if (playBtn && pauseBtn) {
                        playBtn.style.display = "none";
                        pauseBtn.style.display = "inline-block";
                    }
                    applyPlaybackFrame(currentIndex);
                }
            }
        });
        setInterval(refreshMap, REFRESH_MS);

        // Fetch weather on load (non-blocking) and refresh every 15 minutes
        fetchWeather();
        setInterval(fetchWeather, 15 * 60 * 1000);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();

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
            preferCanvas: true,
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
        const cls = riskClass(asset.risk_score);
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

        return `
            <div class="map-popup">
                <div class="map-popup-id">${a.asset_id}</div>
                <div class="map-popup-name">${a.name}</div>
                <div class="map-popup-row">
                    <span class="pill">${a.asset_type}</span>
                    <span class="badge state-${a.state}">${a.state}</span>
                    <span class="badge ${riskClass(a.risk_score)}">risk ${Number(a.risk_score).toFixed(1)}</span>
                </div>
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
            const res = await fetch(`/live/playback?minutes=${minutes}`);
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
            }
            if (trails[truckId]) {
                const slicePts = positions
                    .slice(0, idx + 1)
                    .filter(p => p && isInIndia(p.lat, p.lon))
                    .map(p => [p.lat, p.lon]);
                trails[truckId].setLatLngs(slicePts);
            }
        });

        checkEventsAtTime(ts);
    }

    function checkEventsAtTime(ts) {
        if (!playbackData || !playbackData.events) return;
        const curTime = new Date(ts).getTime();
        const recentEvents = playbackData.events.filter(e => {
            const evTime = new Date(e.timestamp).getTime();
            return Math.abs(evTime - curTime) < 15000;
        });

        recentEvents.forEach(ev => {
            const m = markers[ev.asset_id];
            if (m && m._icon) {
                m._icon.classList.add("flash-red");
                setTimeout(() => {
                    if (m._icon) m._icon.classList.remove("flash-red");
                }, 1500);
            }
        });

        const banner = document.getElementById("playback-event-banner");
        if (banner) {
            if (recentEvents.length > 0) {
                const latest = recentEvents[recentEvents.length - 1];
                banner.style.display = "block";
                banner.textContent = `⚡ [${new Date(latest.timestamp).toLocaleTimeString()}] ${latest.asset_id}: ${latest.detail} (${latest.severity})`;
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
                if (label) label.textContent = "No history";
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
            }, 300);
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
        refreshMap();
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

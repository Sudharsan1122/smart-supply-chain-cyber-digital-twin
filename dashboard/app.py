"""Phase 19 - Flask dashboard with real-time live monitoring."""
from __future__ import annotations

import asyncio, logging, os, uuid
from typing import Any
import requests
from flask import Flask, jsonify, render_template, request
from api_sources.weather_cache import get_weather, get_weather_batch

_SESSION_ID = str(uuid.uuid4())[:8]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://[::1]:8000")
REFRESH = int(os.getenv("DASHBOARD_REFRESH_SECONDS", "3"))
PORT = int(os.getenv("DASHBOARD_PORT", "5000"))

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["TEMPLATES_AUTO_RELOAD"] = True


def api_get(path: str, params: dict | None = None, timeout: float = 5.0) -> Any:
    for base in dict.fromkeys([API_URL, "http://[::1]:8000", "http://127.0.0.1:8000"]):
        try:
            r = requests.get(f"{base}{path}", params=params, timeout=timeout)
            if r.status_code == 200 and "application/json" in r.headers.get("Content-Type", ""):
                return r.json()
        except Exception as e:
            logger.debug("api_get failed for %s%s: %s", base, path, e)
    return None


@app.route("/")
def live():
    summary = api_get("/api/twin/summary") or {}
    state = api_get("/api/twin/state") or {"summary": {}, "states": {}}
    assets = api_get("/api/assets", params={"limit": 100}) or []
    risk = api_get("/api/risk/top", params={"n": 10}) or {"ranked": []}
    mqtt = api_get("/api/mqtt/status") or {}
    ready = api_get("/api/ready") or {}
    events = api_get("/api/events", params={"limit": 20}) or []
    return render_template(
        "live.html",
        active="live",
        refresh=REFRESH,
        api_url=API_URL,
        summary=summary,
        state_summary=state.get("summary", {}),
        assets=assets,
        risk=risk,
        mqtt=mqtt,
        ready=ready,
        events=events,
    )


@app.route("/stories")
def stories():
    rows = api_get("/api/attack-stories", params={"limit": 50}) or []
    return render_template(
        "stories.html",
        active="stories",
        refresh=REFRESH,
        api_url=API_URL,
        stories=rows,
    )


@app.route("/stories/<attack_id>")
def story_detail(attack_id):
    story = api_get(f"/api/attack-stories/{attack_id}")
    if not story or not isinstance(story, dict) or not story.get("attack_id"):
        return render_template("404.html", active="stories", refresh=REFRESH, api_url=API_URL), 404
    blast = api_get(f"/api/blast-radius/story/{attack_id}") or {}
    return render_template(
        "story_detail.html",
        story=story,
        blast=blast,
        active="stories",
        refresh=REFRESH,
        api_url=API_URL,
    )





@app.route("/threat-intel")
def threat_intel():
    iocs = api_get("/api/iocs", params={"limit": 100}) or []
    summary = api_get("/api/iocs/summary") or {}
    cache = api_get("/api/threat-intel/cache-stats") or {}
    return render_template(
        "threat_intel.html",
        active="threat-intel",
        refresh=REFRESH,
        api_url=API_URL,
        iocs=iocs,
        summary=summary,
        cache=cache,
    )


@app.route("/triage")
def triage():
    metrics = api_get("/api/triage/metrics") or {}
    recent = api_get("/api/triage", params={"limit": 100}) or []
    return render_template(
        "triage.html",
        active="triage",
        refresh=REFRESH,
        api_url=API_URL,
        metrics=metrics,
        recent=recent,
    )


@app.route("/healthz")
def healthz():
    ready = api_get("/api/ready") or {}
    return jsonify({
        "dashboard": "up",
        "api_url": API_URL,
        "api_ready": ready.get("ready", False),
    })


# ---------------------------------------------------------------------------
# Real-Time AJAX JSON Proxy Endpoints
# ---------------------------------------------------------------------------

@app.route("/live/summary")
def live_summary():
    """Return JSON for auto-refresh of KPIs and status."""
    summary = api_get("/api/twin/summary") or {}
    ready = api_get("/api/ready") or {}
    mqtt = api_get("/api/mqtt/status") or {}
    risk = api_get("/api/risk/top", params={"n": 10}) or {}
    state = api_get("/api/twin/state") or {}
    assets = api_get("/api/assets", params={"limit": 100}) or []
    return jsonify({
        "twin": summary,
        "ready": ready,
        "mqtt": mqtt,
        "risk_top": risk.get("ranked", []),
        "state_summary": state.get("summary", {}),
        "asset_states": {s["asset_id"]: s for s in state.get("states", [])} if isinstance(state.get("states"), list) else state.get("states", {}),
        "assets": assets,
    })


@app.route("/live/charts")
def live_charts():
    """Return time-series data for live charts with optional window and filters."""
    window = request.args.get("window", "30")
    severity = request.args.get("severity", "")
    asset_type = request.args.get("type", "")
    params = {"window_minutes": window}
    if severity:
        params["severity"] = severity
    if asset_type:
        params["asset_type"] = asset_type
    timeline = api_get("/api/analytics/timeline", params=params) or {}
    return jsonify(timeline)


@app.route("/live/asset/<asset_id>")
def live_asset(asset_id):
    """Return asset details, state, graph hierarchy, and latest detection."""
    data = api_get(f"/api/assets/{asset_id}") or {}
    all_det = api_get("/api/detections", params={"limit": 50}) or []
    match_det = None
    for d in all_det:
        if d.get("asset_code") == asset_id:
            match_det = d
            break
    data["latest_detection"] = match_det
    return jsonify(data)


@app.route("/live/risk/<asset_id>")
def live_risk(asset_id):
    """Return risk score and factor breakdown for asset."""
    return jsonify(api_get(f"/api/risk/asset/{asset_id}") or {})


@app.route("/live/events")
def live_events():
    """Return recent events and detections for the live stream panel."""
    events = api_get("/api/events", params={"limit": 25}) or []
    detections = api_get("/api/detections", params={"limit": 25}) or []

    combined = []
    for e in events:
        combined.append({
            "id": f"evt-{e['id']}",
            "event_type": e.get("event_type", "SECURITY_EVENT"),
            "severity": e.get("severity", "info"),
            "description": e.get("description", "Security event"),
            "timestamp": e.get("timestamp"),
        })
    for d in detections:
        combined.append({
            "id": f"det-{d['id']}",
            "event_type": d.get("rule_id") or d.get("detection_type", "ANOMALY"),
            "severity": d.get("severity", "medium"),
            "description": f"[{d.get('asset_code', 'ASSET')}] {d.get('description', 'Anomaly detected')}",
            "timestamp": d.get("detected_at"),
        })

    # Sort descending by timestamp
    combined.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return jsonify(combined[:25])


@app.route("/live/topology")
def live_topology():
    """Return the twin graph in a layout format with node risk scores."""
    graph = api_get("/api/twin/graph") or {"nodes": [], "edges": []}
    risk = api_get("/api/risk/top", params={"n": 50}) or {}
    risk_map = {r["asset_id"]: r["score"] for r in risk.get("ranked", [])}
    state = api_get("/api/twin/state") or {}
    state_map = {}
    if isinstance(state.get("states"), list):
        state_map = {s["asset_id"]: s.get("state", "unknown") for s in state.get("states", [])}
    elif isinstance(state.get("states"), dict):
        state_map = {k: v.get("state", "unknown") for k, v in state.get("states", {}).items()}

    for node in graph.get("nodes", []):
        aid = node.get("asset_id")
        node["risk_score"] = float(risk_map.get(aid, 0.0))
        node["state"] = state_map.get(aid, "unknown")

    return jsonify(graph)


@app.route("/live/stories")
def live_stories():
    """Return recent attack stories for in-place auto-refresh."""
    rows = api_get("/api/attack-stories", params={"limit": 50}) or []
    return jsonify(rows)


@app.route("/live/threat-intel")
def live_threat_intel():
    """Return threat intel data for in-place auto-refresh."""
    iocs = api_get("/api/iocs", params={"limit": 100}) or []
    summary = api_get("/api/iocs/summary") or {}
    cache = api_get("/api/threat-intel/cache-stats") or {}
    return jsonify({"iocs": iocs, "summary": summary, "cache": cache})


@app.route("/live/triage")
def live_triage():
    """Return triage metrics and recent triage for in-place auto-refresh."""
    metrics = api_get("/api/triage/metrics") or {}
    recent = api_get("/api/triage", params={"limit": 100}) or []
    return jsonify({"metrics": metrics, "recent": recent})


@app.route("/live/blast-radius/story/<attack_id>")
def live_blast_story(attack_id):
    """Return blast radius propagation data for an attack story."""
    return jsonify(api_get(f"/api/blast-radius/story/{attack_id}") or {})


@app.route("/live/triage/rules")
def live_triage_rules():
    """Return per-rule triage metrics for charts."""
    return jsonify(api_get("/api/triage/metrics/rules") or {"rules": []})



_DEFAULT_COORDS: dict[str, tuple[float, float]] = {
    "WH-001": (13.0827, 80.2707),   # Chennai Central
    "WH-002": (12.9716, 77.5946),   # Bengaluru Hub
    "WH-003": (19.0760, 72.8777),   # Mumbai DC
    "WH-004": (28.7041, 77.1025),   # Delhi NCR
    "TRUCK-001": (13.1500, 80.1800), # Chennai Corridor
    "TRUCK-002": (13.5500, 79.4200), # Tirupati Route
    "TRUCK-003": (12.9716, 77.5946), # Bengaluru
    "TRUCK-004": (15.3647, 75.1240), # Hubli
    "TRUCK-005": (19.0760, 72.8777), # Mumbai
    "TRUCK-006": (18.5204, 73.8567), # Pune
    "TRUCK-007": (23.0225, 72.5714), # Ahmedabad
    "TRUCK-008": (28.7041, 77.1025), # Delhi
    "DOOR-001": (13.0815, 80.2685),  # WH-001
    "HUM-001": (13.0840, 80.2720),   # WH-001
    "TEMP-001": (13.0835, 80.2690),  # WH-001
    "TEMP-002": (13.0818, 80.2715),  # WH-001
    "HUM-002": (19.0775, 72.8760),   # WH-003
    "DOOR-002": (28.7055, 77.1010),  # WH-004
    "VGW-101": (13.1520, 80.1820),   # On TRUCK-001
    "VGW-102": (13.5520, 79.4220),   # On TRUCK-002
    "VGW-103": (19.0780, 72.8790),   # On TRUCK-005
    "VGW-104": (28.7060, 77.1040),   # On TRUCK-008
    "API-GW-001": (28.6139, 77.2090),# North GW (Delhi)
    "API-GW-002": (19.0800, 72.8900),# West GW (Mumbai)
    "AUTH-001": (28.6120, 77.2070),  # Identity
    "DB-001": (28.6100, 77.2050),    # PostgreSQL DB
    "APP-001": (28.6150, 77.2110),   # Order Mgmt
    "APP-002": (19.0820, 72.8920),   # Fleet Track
    "SUP-001": (22.5726, 88.3639),   # Acme (Kolkata)
    "SUP-002": (17.3850, 78.4867),   # NorthStar (Hyderabad)
    "SUP-003": (21.1458, 79.0882),   # Titan Steel (Nagpur)
    "SUP-004": (11.0168, 76.9558),   # GreenLeaf (Coimbatore)
}


@app.route("/live/map-data")
def live_map_data():
    """Return all assets with GPS + risk for map rendering."""
    assets = api_get("/api/assets", params={"limit": 200}) or []
    risk = api_get("/api/risk/top", params={"n": 100}) or {"ranked": []}
    state = api_get("/api/twin/state") or {"states": {}}

    risk_by_id = {a["asset_id"]: a.get("score", 0) for a in risk.get("ranked", [])}
    states = state.get("states", {})
    if isinstance(states, list):
        states = {s.get("asset_id"): s for s in states}

    out = []
    for a in assets:
        aid = a["asset_id"]
        st = states.get(aid, {})
        pos = st.get("position") or {}
        meta_loc = (a.get("metadata") or {}).get("location") or {}

        lat = pos.get("lat") or pos.get("latitude") or meta_loc.get("lat") or meta_loc.get("latitude")
        lon = pos.get("lon") or pos.get("longitude") or meta_loc.get("lon") or meta_loc.get("longitude")

        # Fallback to default coordinates
        if (lat is None or lon is None) and aid in _DEFAULT_COORDS:
            lat, lon = _DEFAULT_COORDS[aid]

        if lat is None or lon is None:
            continue

        out.append({
            "asset_id": aid,
            "asset_type": a["asset_type"],
            "name": a.get("name", aid),
            "state": st.get("state") or a.get("state", "unknown"),
            "health": st.get("health") or a.get("health", "unknown"),
            "risk_score": risk_by_id.get(aid, 0),
            "lat": float(lat),
            "lon": float(lon),
        })

    return jsonify({
        "assets": out,
        "total": len(out),
        "session_id": _SESSION_ID,
    })


@app.route("/live/playback")
def live_playback():
    """Return time-series of historical truck positions and security events for playback."""
    minutes = request.args.get("minutes", "30")
    data = api_get(f"/api/analytics/playback?from_minutes_ago={minutes}") or {}
    return jsonify(data)


@app.route("/live/weather/<asset_id>")
def live_weather(asset_id):
    """Return live OpenWeather conditions for a specific asset."""
    state = api_get(f"/api/twin/state/{asset_id}") or {}
    pos = state.get("position") or {}
    lat = pos.get("lat") or pos.get("latitude")
    lon = pos.get("lon") or pos.get("longitude")
    if (lat is None or lon is None) and asset_id in _DEFAULT_COORDS:
        lat, lon = _DEFAULT_COORDS[asset_id]
    if lat is None or lon is None:
        return jsonify({"error": "no_position"}), 404

    data = asyncio.run(get_weather(float(lat), float(lon)))
    if not data:
        return jsonify({"error": "weather_unavailable"}), 502

    return jsonify({
        "asset_id": asset_id,
        "lat": float(lat),
        "lon": float(lon),
        "temperature_c": data.get("temperature_c"),
        "humidity_pct": data.get("humidity_pct"),
        "condition": data.get("condition"),
        "description": data.get("description"),
        "wind_speed_ms": data.get("wind_speed_ms"),
        "wind_deg": data.get("wind_deg"),
        "city": data.get("city"),
    })


@app.route("/live/weather-batch")
def live_weather_batch():
    """Return weather for all assets with GPS in one call."""
    state_all = api_get("/api/twin/state") or {}
    states = state_all.get("states", {})
    if isinstance(states, list):
        states = {s.get("asset_id"): s for s in states}

    coords: dict[str, tuple[float, float]] = dict(_DEFAULT_COORDS)
    for aid, st in states.items():
        pos = st.get("position") or {}
        lat = pos.get("lat") or pos.get("latitude")
        lon = pos.get("lon") or pos.get("longitude")
        if lat is not None and lon is not None:
            lat_f, lon_f = float(lat), float(lon)
            if 6.0 <= lat_f <= 37.0 and 68.0 <= lon_f <= 98.0:
                coords[aid] = (lat_f, lon_f)

    batch = asyncio.run(get_weather_batch(coords))
    out = {}
    for aid, data in batch.items():
        out[aid] = {
            "temp": data.get("temperature_c"),
            "temperature_c": data.get("temperature_c"),
            "humidity": data.get("humidity_pct"),
            "humidity_pct": data.get("humidity_pct"),
            "condition": data.get("condition"),
            "description": data.get("description"),
            "wind_speed_ms": data.get("wind_speed_ms"),
            "wind_deg": data.get("wind_deg"),
            "city": data.get("city"),
        }
    return jsonify(out)


@app.route("/live/geofences")
def live_geofences():
    """Return geofence zone definitions for all trucks."""
    from geofencing.zones import GEOFENCES
    return jsonify(GEOFENCES)


# ---------------------------------------------------------------------------
# Template Filters
# ---------------------------------------------------------------------------

@app.template_filter("fmt_ts")
def fmt_ts(ts):
    if not ts:
        return "---"
    return str(ts).replace("T", " ")[:19]


@app.template_filter("score_color")
def score_color(s):
    try:
        val = float(s)
    except (ValueError, TypeError):
        return "safe"
    if val >= 75:
        return "danger"
    if val >= 50:
        return "warn"
    if val >= 25:
        return "info"
    return "safe"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

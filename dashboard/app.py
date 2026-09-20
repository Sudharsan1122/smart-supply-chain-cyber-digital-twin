"""Phase 19 - Flask dashboard with real-time live monitoring."""
from __future__ import annotations

import logging, os
from typing import Any
import requests
from flask import Flask, jsonify, render_template, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
REFRESH = int(os.getenv("DASHBOARD_REFRESH_SECONDS", "3"))
PORT = int(os.getenv("DASHBOARD_PORT", "5000"))

app = Flask(__name__, template_folder="templates", static_folder="static")


def api_get(path: str, params: dict | None = None, timeout: float = 5.0) -> Any:
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=timeout)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        logger.debug("api_get failed for %s: %s", path, e)
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

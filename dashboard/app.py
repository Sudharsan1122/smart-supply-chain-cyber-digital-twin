"""Phase 19 - Flask dashboard."""
from __future__ import annotations
import logging, os
from typing import Any
import requests
from flask import Flask, jsonify, render_template, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://localhost:8000")
REFRESH = int(os.getenv("DASHBOARD_REFRESH_SECONDS", "5"))
PORT = int(os.getenv("DASHBOARD_PORT", "5000"))

app = Flask(__name__, template_folder="templates", static_folder="static")


def api_get(path, params=None, timeout=5.0):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=timeout)
        return r.json() if r.status_code == 200 else None
    except Exception:
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
    return render_template("live.html", active="live", refresh=REFRESH,
                           api_url=API_URL, summary=summary,
                           state_summary=state.get("summary", {}),
                           assets=assets, risk=risk, mqtt=mqtt,
                           ready=ready, events=events)


@app.route("/stories")
def stories():
    rows = api_get("/api/attack-stories", params={"limit": 50}) or []
    return render_template("stories.html", active="stories", refresh=REFRESH,
                           api_url=API_URL, stories=rows)


@app.route("/threat-intel")
def threat_intel():
    iocs = api_get("/api/iocs", params={"limit": 100}) or []
    summary = api_get("/api/iocs/summary") or {}
    cache = api_get("/api/threat-intel/cache-stats") or {}
    return render_template("threat_intel.html", active="threat-intel",
                           refresh=REFRESH, api_url=API_URL,
                           iocs=iocs, summary=summary, cache=cache)


@app.route("/triage")
def triage():
    metrics = api_get("/api/triage/metrics") or {}
    recent = api_get("/api/triage", params={"limit": 100}) or []
    return render_template("triage.html", active="triage", refresh=REFRESH,
                           api_url=API_URL, metrics=metrics, recent=recent)


@app.route("/healthz")
def healthz():
    ready = api_get("/api/ready") or {}
    return jsonify({"dashboard": "up", "api_url": API_URL,
                    "api_ready": ready.get("ready", False)})


@app.template_filter("fmt_ts")
def fmt_ts(ts):
    if not ts: return "---"
    return str(ts).replace("T", " ")[:19]


@app.template_filter("score_color")
def score_color(s):
    if s >= 75: return "danger"
    if s >= 50: return "warn"
    if s >= 25: return "info"
    return "safe"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

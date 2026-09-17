"""Phase 20 - End-to-end demo orchestrator."""
from __future__ import annotations
import argparse, os, sys, time
import requests

DEFAULT_API = os.getenv("API_URL", "http://localhost:8000")
ATTACK_DURATION = 8
ATTACK_INTENSITY = "high"


def hr(title=""):
    print("\n=== " + title + " ===")


class API:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.s = requests.Session()

    def get(self, path, **p):
        try:
            r = self.s.get(f"{self.base}{path}", params=p, timeout=15)
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    def post(self, path, body=None, **p):
        try:
            r = self.s.post(f"{self.base}{path}", json=body or {}, params=p, timeout=20)
            return r.json() if r.status_code in (200, 201) else None
        except Exception:
            return None


def run():
    api = API(DEFAULT_API)

    hr("Health Check")
    ready = api.get("/api/ready")
    if not ready or not ready.get("ready"):
        print("API not ready:", ready)
        return 1
    print("  Checks:", ready.get("checks"))

    hr("Twin Snapshot")
    summary = api.get("/api/twin/summary") or {}
    print("  Nodes:", summary.get("nodes"), "Edges:", summary.get("edges"))

    hr("Fire Attack Scenarios")
    attacks = [("SIM-01", "VGW-101"), ("SIM-02", "WH-001"), ("SIM-03", "AUTH-001")]
    runs = []
    for scenario_id, target in attacks:
        r = api.post("/api/attack-simulation/start", body={
            "scenario": scenario_id,
            "target": target,
            "duration_seconds": ATTACK_DURATION,
            "intensity": ATTACK_INTENSITY,
        })
        if r:
            runs.append(r)
            print(f"  Started {scenario_id} -> {target}")

    hr("Waiting for attacks")
    deadline = time.time() + ATTACK_DURATION + 30
    while time.time() < deadline:
        remaining = [r for r in runs
                     if api.get(f"/api/attack-simulation/runs/{r['run_id']}")]
        if not remaining:
            break
        print(f"  {len(remaining)} still running...")
        time.sleep(2)
    time.sleep(3)

    hr("Enrichment")
    sweep = api.post("/api/threat-intel/sweep?limit=50")
    print("  Enriched:", sweep.get("processed") if sweep else 0)

    hr("Attack Stories")
    for r in runs:
        detail = api.get(f"/api/attack-stories/{r['attack_story_uid']}")
        if detail:
            print(f"  {detail['title']} — status={detail['status']}, "
                  f"events={len(detail.get('events', []))}")

    hr("Triage Sweep")
    tri = api.post("/api/triage/sweep?limit=200")
    print("  Triaged:", tri.get("processed") if tri else 0)
    metrics = api.get("/api/triage/metrics") or {}
    print("  Precision:", metrics.get("precision"),
          "Recall:", metrics.get("recall"),
          "F1:", metrics.get("f1"))

    hr("Final Risk")
    top = api.get("/api/risk/top?n=5") or {}
    for a in top.get("ranked", []):
        print(f"  {a['asset_id']:<14} {a['score']}")

    print("\nDONE. Dashboard: http://localhost:5000")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=DEFAULT_API)
    args = parser.parse_args()
    return run()


if __name__ == "__main__":
    sys.exit(main())

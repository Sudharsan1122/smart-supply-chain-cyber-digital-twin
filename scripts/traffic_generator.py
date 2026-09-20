"""
traffic_generator.py — Continuously publishes synthetic telemetry to the API.

Run alongside the API + Dashboard to make the twin feel live.

Usage:
    python -m scripts.traffic_generator
    python -m scripts.traffic_generator --interval 2 --api http://localhost:8000
    python -m scripts.traffic_generator --mode normal   # baseline traffic only
    python -m scripts.traffic_generator --mode attack   # inject anomalies periodically

Modes:
    normal  → realistic baseline values (no detections)
    attack  → occasionally injects anomalies (triggers rules + ML)
"""
from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import datetime, timezone

import httpx


# ---------------------------------------------------------------------------
# Assets to simulate (asset_id, asset_type)
# ---------------------------------------------------------------------------
ASSETS = [
    ("TRUCK-001", "TRUCK"),
    ("TRUCK-003", "TRUCK"),
    ("TRUCK-005", "TRUCK"),
    ("WH-001", "WAREHOUSE"),
    ("WH-002", "WAREHOUSE"),
    ("TEMP-001", "SENSOR"),
    ("HUM-001", "SENSOR"),
    ("DOOR-001", "SENSOR"),
    ("VGW-101", "VEHICLE_GATEWAY"),
    ("VGW-103", "VEHICLE_GATEWAY"),
    ("API-GW-001", "API_GATEWAY"),
    ("APP-001", "APPLICATION"),
    ("AUTH-001", "AUTH_SYSTEM"),
    ("DB-001", "DATABASE"),
]


# ---------------------------------------------------------------------------
# Baseline generators (normal traffic)
# ---------------------------------------------------------------------------
def _truck_payload() -> dict:
    return {
        "speed": round(random.gauss(55, 12), 1),
        "temperature": round(random.gauss(-2, 2), 1),
        "fuel": round(max(0, min(100, random.gauss(70, 12))), 1),
        "battery": round(max(0, min(100, random.gauss(85, 5))), 1),
        "status": random.choice(["ACTIVE", "ACTIVE", "IDLE", "MOVING"]),
        "gps": {
            "latitude": round(random.gauss(13.08, 0.3), 4),
            "longitude": round(random.gauss(80.27, 0.3), 4),
        },
    }


def _warehouse_payload() -> dict:
    return {
        "temperature": round(random.gauss(22, 2), 1),
        "humidity": round(random.gauss(55, 5), 1),
        "occupancy": random.randint(40, 120),
        "power_consumption": round(random.gauss(45, 8), 1),
    }


def _sensor_payload() -> dict:
    return {
        "temperature": round(random.gauss(20, 3), 1),
        "humidity": round(random.gauss(50, 8), 1),
    }


def _gateway_payload() -> dict:
    return {
        "failed_logins": random.randint(0, 2),
        "api_calls": random.randint(80, 200),
        "unusual_api_calls": random.randint(0, 3),
        "status": "ACTIVE",
        "firmware": "v2.4.1",
    }


def _api_gateway_payload() -> dict:
    return {
        "api_calls": random.randint(4000, 6000),
        "unusual_api_calls": random.randint(0, 5),
    }


def _auth_payload() -> dict:
    return {
        "failed_logins": random.randint(0, 3),
        "auth_events": random.randint(30, 80),
    }


def _db_payload() -> dict:
    return {
        "api_calls": random.randint(1500, 2500),
        "unusual_api_calls": random.randint(0, 2),
    }


GENERATORS = {
    "TRUCK": _truck_payload,
    "WAREHOUSE": _warehouse_payload,
    "SENSOR": _sensor_payload,
    "VEHICLE_GATEWAY": _gateway_payload,
    "API_GATEWAY": _api_gateway_payload,
    "APPLICATION": _api_gateway_payload,
    "AUTH_SYSTEM": _auth_payload,
    "DATABASE": _db_payload,
    "SUPPLIER": lambda: {},
}


# ---------------------------------------------------------------------------
# Attack injections
# ---------------------------------------------------------------------------
def inject_anomaly(asset_id: str, asset_type: str) -> dict:
    """Return a payload with an injected anomaly (triggers detections)."""
    base = dict(GENERATORS.get(asset_type, lambda: {})())

    if asset_type == "TRUCK":
        variant = random.choice(["overspeed", "cold_chain", "geofence"])
        if variant == "overspeed":
            base["speed"] = round(random.uniform(110, 160), 1)
        elif variant == "cold_chain":
            base["temperature"] = round(random.uniform(12, 20), 1)
        elif variant == "geofence":
            base["gps"] = {"latitude": 51.5, "longitude": -0.1}  # London
    elif asset_type == "WAREHOUSE":
        base["temperature"] = round(random.uniform(42, 55), 1)
        base["door_status"] = "OPEN"
    elif asset_type == "VEHICLE_GATEWAY":
        base["failed_logins"] = random.randint(10, 25)
        base["unusual_api_calls"] = random.randint(150, 400)
        base["network_destinations"] = [
            f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            for _ in range(random.randint(5, 8))
        ]
        base["firmware"] = "v1.0.0"
    elif asset_type == "AUTH_SYSTEM":
        base["failed_logins"] = random.randint(15, 40)
        base["auth_events"] = random.randint(100, 300)

    return base


# ---------------------------------------------------------------------------
# Publisher loop
# ---------------------------------------------------------------------------
class TrafficGenerator:
    def __init__(self, api: str, interval: float, mode: str,
                 anomaly_rate: float, verbose: bool):
        self.api = api.rstrip("/")
        self.interval = interval
        self.mode = mode
        self.anomaly_rate = anomaly_rate
        self.verbose = verbose
        self.stats = {
            "sent": 0,
            "ok": 0,
            "failed": 0,
            "anomalies": 0,
        }

    def _build_payload(self, asset_id: str, asset_type: str) -> dict:
        is_anomaly = (
            self.mode == "attack"
            and random.random() < self.anomaly_rate
        )
        if is_anomaly:
            self.stats["anomalies"] += 1
            body = inject_anomaly(asset_id, asset_type)
        else:
            body = GENERATORS.get(asset_type, lambda: {})()
        return {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **body,
        }

    async def run(self) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print(f"Traffic generator started")
            print(f"  API:        {self.api}")
            print(f"  Interval:   {self.interval}s")
            print(f"  Mode:       {self.mode}")
            print(f"  Anomaly %:  {int(self.anomaly_rate * 100)}%")
            print(f"  Assets:     {len(ASSETS)}")
            print(f"Press Ctrl+C to stop.\n")

            tick = 0
            while True:
                tick += 1
                for asset_id, asset_type in ASSETS:
                    payload = self._build_payload(asset_id, asset_type)
                    self.stats["sent"] += 1
                    try:
                        r = await client.post(
                            f"{self.api}/api/telemetry", json=payload
                        )
                        if r.status_code in (200, 201):
                            self.stats["ok"] += 1
                        else:
                            self.stats["failed"] += 1
                            if self.verbose:
                                print(f"  [{asset_id}] HTTP {r.status_code}: {r.text[:120]}")
                    except Exception as e:
                        self.stats["failed"] += 1
                        if self.verbose:
                            print(f"  [{asset_id}] ERROR: {e}")

                if tick % 10 == 0:
                    print(
                        f"  tick={tick:>4}  sent={self.stats['sent']:>5}  "
                        f"ok={self.stats['ok']:>5}  "
                        f"anomalies={self.stats['anomalies']:>4}  "
                        f"failed={self.stats['failed']:>3}"
                    )

                await asyncio.sleep(self.interval)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description="Continuous telemetry generator")
    p.add_argument("--api", default="http://localhost:8000")
    p.add_argument("--interval", type=float, default=2.0,
                   help="Seconds between ticks")
    p.add_argument("--mode", choices=["normal", "attack"], default="attack",
                   help="normal = baseline only, attack = inject anomalies")
    p.add_argument("--anomaly-rate", type=float, default=0.05,
                   help="Fraction of payloads that are anomalies (0.0-1.0)")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()

    gen = TrafficGenerator(
        api=args.api,
        interval=args.interval,
        mode=args.mode,
        anomaly_rate=args.anomaly_rate,
        verbose=args.verbose,
    )

    try:
        asyncio.run(gen.run())
    except KeyboardInterrupt:
        print("\n\nStopped.")
        print(f"Stats: {gen.stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

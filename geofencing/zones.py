"""Geofence zone definitions and Haversine distance calculation."""
from __future__ import annotations

import math
from typing import Any

GEOFENCES: dict[str, dict[str, Any]] = {
    "TRUCK-001": {"center": (13.08, 80.27), "radius_km": 350, "buffer_km": 50},
    "TRUCK-002": {"center": (13.08, 80.27), "radius_km": 300, "buffer_km": 50},
    "TRUCK-003": {"center": (19.08, 72.88), "radius_km": 200, "buffer_km": 30},
    "TRUCK-004": {"center": (28.70, 77.10), "radius_km": 300, "buffer_km": 50},
    "TRUCK-005": {"center": (19.08, 72.88), "radius_km": 250, "buffer_km": 40},
    "TRUCK-006": {"center": (28.70, 77.10), "radius_km": 250, "buffer_km": 40},
    "TRUCK-007": {"center": (15.18, 78.02), "radius_km": 400, "buffer_km": 60},
    "TRUCK-008": {"center": (13.08, 80.27), "radius_km": 200, "buffer_km": 30},
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance in kilometers between two GPS points."""
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

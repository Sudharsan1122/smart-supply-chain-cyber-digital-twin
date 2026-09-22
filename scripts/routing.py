"""OSRM-based route interpolation via real roads."""
from __future__ import annotations

import logging
from functools import lru_cache
import httpx

logger = logging.getLogger(__name__)

OSRM_URL = "http://router.project-osrm.org/route/v1/driving"


@lru_cache(maxsize=32)
def get_road_path(waypoints: tuple) -> list[tuple[float, float]]:
    """
    Given a tuple of (lat, lon) waypoints, return a dense list of
    (lat, lon) points following real roads via OSRM.
    """
    if len(waypoints) < 2:
        return list(waypoints)

    coords = ";".join(f"{lon},{lat}" for lat, lon in waypoints)
    url = f"{OSRM_URL}/{coords}"

    try:
        r = httpx.get(
            url,
            params={"overview": "full", "geometries": "geojson"},
            timeout=10.0,
            headers={"User-Agent": "SSCDT-DigitalTwin/1.0"},
        )
        r.raise_for_status()
        data = r.json()
        route = data["routes"][0]
        geom = route["geometry"]["coordinates"]
        # OSRM returns [lon, lat]; flip to (lat, lon)
        path = [(float(c[1]), float(c[0])) for c in geom]
        logger.info("OSRM path: %d waypoints -> %d road points", len(waypoints), len(path))
        print(f"OSRM path: {len(waypoints)} waypoints -> {len(path)} road points")
        return path
    except Exception as e:
        logger.warning("OSRM failed (%s) - falling back to straight lines", e)
        print(f"OSRM failed ({e}) - falling back to straight lines")
        return list(waypoints)


"""Great-circle distance and distance formatting."""

import math

EARTH_RADIUS_M = 6_371_008.8  # mean Earth radius (IUGG)


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line (great-circle) distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def fmt_dist(m: float) -> str:
    """'180 m' under 1 km, else '18.4 km'."""
    if round(m) < 1000:
        return f"{round(m)} m"
    return f"{m / 1000:.1f} km"

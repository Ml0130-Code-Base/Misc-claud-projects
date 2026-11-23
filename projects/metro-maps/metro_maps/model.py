"""Load a stored snapshot into stations and lines, splitting out waypoints."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


class SnapshotError(Exception):
    """The payload does not have the structure we expect."""


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    lat: float
    lng: float
    is_waypoint: bool


@dataclass
class Line:
    id: str
    name: str
    mode: str
    color: str
    group_id: str
    station_ids: list[str]  # full sequence, waypoints included
    seq: list[str] = field(default_factory=list)  # non-waypoint stations only, in order


@dataclass
class Snapshot:
    title: str
    last_updated: int  # epoch ms, from the map's own data
    stations: dict[str, Station]  # every object, waypoints included
    lines: list[Line]  # sorted by name, then id
    line_groups: dict[str, str]  # id -> label

    @property
    def real_stations(self) -> dict[str, Station]:
        return {k: s for k, s in self.stations.items() if not s.is_waypoint}

    @property
    def waypoint_count(self) -> int:
        return sum(1 for s in self.stations.values() if s.is_waypoint)

    @property
    def updated_text(self) -> str:
        dt = datetime.fromtimestamp(self.last_updated / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")


def _keys(obj) -> str:
    return ", ".join(sorted(obj.keys())) if isinstance(obj, dict) else type(obj).__name__


def find_map(payload: dict) -> tuple[dict, dict]:
    """Return (map dict with stations/lines, systemDocData or {}).

    The handover notes the system has been seen under fullSystem, systemDocData or
    system, with stations/lines either under .map or at top level. Check each.
    """
    if not isinstance(payload, dict) or "props" not in payload:
        raise SnapshotError(f"missing key 'props'; found: {_keys(payload)}")
    props = payload["props"]
    if not isinstance(props, dict) or "pageProps" not in props:
        raise SnapshotError(f"missing key 'props.pageProps'; found: {_keys(props)}")
    pp = props["pageProps"]
    if not isinstance(pp, dict):
        raise SnapshotError("props.pageProps is not an object")
    doc = pp.get("systemDocData") if isinstance(pp.get("systemDocData"), dict) else {}
    for key in ("fullSystem", "systemDocData", "system"):
        cand = pp.get(key)
        if not isinstance(cand, dict):
            continue
        for m in (cand.get("map"), cand):
            if isinstance(m, dict) and isinstance(m.get("stations"), dict) and isinstance(m.get("lines"), dict):
                return m, doc
    found = {k: _keys(v) for k, v in pp.items() if isinstance(v, dict)}
    detail = "; ".join(f"{k}: [{v}]" for k, v in sorted(found.items())) or _keys(pp)
    raise SnapshotError(
        "missing key 'map.stations'/'map.lines' under props.pageProps.fullSystem, "
        f".systemDocData or .system; found pageProps.{detail}"
    )


def from_payload(payload: dict) -> Snapshot:
    m, doc = find_map(payload)
    stations: dict[str, Station] = {}
    for sid, s in m["stations"].items():
        try:
            stations[sid] = Station(
                id=sid,
                name=s.get("name", "") or "",
                lat=float(s["lat"]),
                lng=float(s["lng"]),
                is_waypoint=bool(s.get("isWaypoint", False)),
            )
        except (KeyError, TypeError, ValueError) as e:
            raise SnapshotError(f"station {sid} has no usable lat/lng ({e})") from None

    lines = []
    for lid, l in m["lines"].items():
        ids = [i for i in (l.get("stationIds") or []) if i in stations]
        lines.append(Line(
            id=lid,
            name=l.get("name", "") or "",
            mode=l.get("mode", "") or "",
            color=l.get("color", "") or "",
            group_id=l.get("lineGroupId", "") or "",
            station_ids=ids,
            seq=[i for i in ids if not stations[i].is_waypoint],
        ))
    lines.sort(key=lambda l: (l.name, l.id))

    groups = {}
    for gid, g in (m.get("lineGroups") or {}).items():
        if isinstance(g, dict):
            groups[gid] = g.get("label", "") or ""

    full = payload["props"]["pageProps"].get("fullSystem") or {}
    last_updated = doc.get("lastUpdated") or full.get("lastUpdated")
    if not isinstance(last_updated, (int, float)):
        raise SnapshotError("missing key 'lastUpdated' in systemDocData and fullSystem")
    title = doc.get("title") or m.get("title") or "(untitled map)"
    return Snapshot(title=title, last_updated=int(last_updated), stations=stations,
                    lines=lines, line_groups=groups)


def load_snapshot(path: Path) -> Snapshot:
    with open(path, encoding="utf-8") as f:
        return from_payload(json.load(f))

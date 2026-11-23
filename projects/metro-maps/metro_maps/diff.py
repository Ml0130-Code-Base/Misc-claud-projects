"""Compare two snapshots of the same map, matching objects by ID."""

from __future__ import annotations

from pathlib import Path

from .geo import fmt_dist, haversine_m
from .model import Line, Snapshot, Station, load_snapshot

MOVE_THRESHOLD_M = 25.0
WAYPOINT_MOVE_M = 1.0


def _q(name: str) -> str:
    return f"`{name}`"


def _moved(a: Station, b: Station) -> float:
    return haversine_m(a.lat, a.lng, b.lat, b.lng)


def _seq_changes(old: Line, new: Line, o: Snapshot, n: Snapshot) -> list[str]:
    """Describe station-sequence changes on a line that exists in both snapshots."""
    if old.seq == new.seq:
        return []
    out = []
    old_set, new_set = set(old.seq), set(new.seq)
    for pos, sid in enumerate(new.seq):
        if sid in old_set:
            continue
        prev_ = _q(n.stations[new.seq[pos - 1]].name) if pos > 0 else "(start)"
        next_ = _q(n.stations[new.seq[pos + 1]].name) if pos + 1 < len(new.seq) else "(end)"
        out.append(f"  - inserted {_q(n.stations[sid].name)} between {prev_} and {next_}")
    for sid in old.seq:
        if sid not in new_set:
            out.append(f"  - removed {_q(o.stations[sid].name)}")
    if not out:
        out.append("  - same stations, order changed")
    return out


def diff_snapshots(o: Snapshot, n: Snapshot) -> str:
    lines = [f"# Diff: {n.title}", "",
             f"Old: {o.last_updated} ({o.updated_text})  ",
             f"New: {n.last_updated} ({n.updated_text})", ""]

    def by_name(ids, snap):
        return sorted(ids, key=lambda i: (snap.stations[i].name, i))

    # Stations (non-waypoint on at least one side)
    added, removed, renamed, moved, toggled = [], [], [], [], []
    wp_moved = 0
    for sid in by_name([i for i in n.stations if i not in o.stations and not n.stations[i].is_waypoint], n):
        added.append(f"- {_q(n.stations[sid].name)}")
    for sid in by_name([i for i in o.stations if i not in n.stations and not o.stations[i].is_waypoint], o):
        removed.append(f"- {_q(o.stations[sid].name)}")
    for sid in by_name([i for i in n.stations if i in o.stations], n):
        a, b = o.stations[sid], n.stations[sid]
        if a.is_waypoint and b.is_waypoint:
            if _moved(a, b) > WAYPOINT_MOVE_M:
                wp_moved += 1
            continue
        if a.is_waypoint != b.is_waypoint:
            what = "waypoint -> station" if a.is_waypoint else "station -> waypoint"
            toggled.append(f"- {_q(b.name or a.name)}: {what}")
            continue
        if a.name != b.name:
            renamed.append(f"- {_q(a.name)} -> {_q(b.name)}")
        d = _moved(a, b)
        if d > MOVE_THRESHOLD_M:
            moved.append(f"- {_q(b.name)} moved {fmt_dist(d)}")

    # Lines
    ol = {l.id: l for l in o.lines}
    nl = {l.id: l for l in n.lines}
    l_added = [f"- {_q(l.name)} ({l.mode or 'no mode'}, {len(l.seq)} stations)" for l in n.lines if l.id not in ol]
    l_removed = [f"- {_q(l.name)}" for l in o.lines if l.id not in nl]
    l_changed = []
    for l in n.lines:
        if l.id not in ol:
            continue
        old = ol[l.id]
        notes = []
        if old.name != l.name:
            notes.append(f"  - renamed from {_q(old.name)}")
        if old.mode != l.mode:
            notes.append(f"  - mode {old.mode or '(none)'} -> {l.mode or '(none)'}")
        if old.color != l.color:
            notes.append(f"  - color {old.color} -> {l.color}")
        notes += _seq_changes(old, l, o, n)
        if notes:
            l_changed.append(f"- {_q(l.name)}")
            l_changed += notes

    def section(title, items):
        lines.append(f"## {title}")
        lines.append("")
        lines.extend(items or ["None."])
        lines.append("")

    section("Stations added", added)
    section("Stations removed", removed)
    section("Stations renamed", renamed)
    section(f"Stations moved (> {int(MOVE_THRESHOLD_M)} m)", moved)
    section("Station / waypoint switched", toggled)
    section("Lines added", l_added)
    section("Lines removed", l_removed)
    section("Lines changed", l_changed)
    lines.append(f"Waypoints moved: {wp_moved}")
    return "\n".join(lines) + "\n"


def diff_files(old: Path, new: Path) -> str:
    return diff_snapshots(load_snapshot(old), load_snapshot(new))

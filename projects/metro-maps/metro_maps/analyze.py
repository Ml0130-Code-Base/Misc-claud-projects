"""Turn a snapshot into a DELETE / MERGE / CREATE / HOUSEKEEPING punch list."""

from __future__ import annotations

import re
from itertools import combinations
from pathlib import Path

from . import report_dir
from .geo import fmt_dist, haversine_m
from .model import Line, Snapshot, load_snapshot

# Spacing between consecutive non-waypoint stations, metres: (too close, too far).
# Modes not listed (FERRY, empty, unknown) are not spacing-checked.
THRESHOLDS_M: dict[str, tuple[float, float]] = {
    "TRAM": (250, 1_500),
    "LIGHT": (500, 3_000),
    "BRT": (400, 3_000),
    "RAPID": (400, 3_000),
    "REGIONAL": (1_500, 15_000),
}
KNOWN_MODES = set(THRESHOLDS_M) | {"FERRY"}
DUPLICATE_RADIUS_M = 150

DRAFT_LINE = re.compile(r"^\s*$|^(concept|line)\s*\d+$|^untitled", re.I)
PLACEHOLDER_STATION = re.compile(
    r"^\s*$|^(station|stop|new station|new stop|station name|stop name|name|untitled|concept|tbd)(\s*\d+)?$"
    r"|^untitled", re.I
)
BAD_SPACING = re.compile(r"^\s|\s$|\s{2,}")


def q(name: str) -> str:
    """Exact name in backticks; blank names made visible."""
    return f"`{name}`" if name.strip() else "(blank name)"


def is_draft(line: Line) -> bool:
    return bool(DRAFT_LINE.search(line.name))


class Analysis:
    def __init__(self, snap: Snapshot):
        self.s = snap
        self.st = snap.real_stations
        self.drafts = [l for l in snap.lines if is_draft(l)]
        self.active = [l for l in snap.lines if not is_draft(l)]
        self.lines_of: dict[str, list[str]] = {}  # station id -> line names (non-draft)
        self.on_any_line: set[str] = set()
        for l in snap.lines:
            self.on_any_line.update(l.seq)
            if not is_draft(l):
                for sid in l.seq:
                    names = self.lines_of.setdefault(sid, [])
                    if l.name not in names:
                        names.append(l.name)

    def dist(self, a: str, b: str) -> float:
        x, y = self.s.stations[a], self.s.stations[b]
        return haversine_m(x.lat, x.lng, y.lat, y.lng)

    def name(self, sid: str) -> str:
        return self.s.stations[sid].name

    def where(self, sid: str) -> str:
        """Locate a station by its neighbours on its first line (for non-unique names)."""
        for l in sorted(self.active, key=lambda l: (l.name, l.id)):
            if sid in l.seq:
                i = l.seq.index(sid)
                prev_ = q(self.name(l.seq[i - 1])) if i > 0 else "(start)"
                next_ = q(self.name(l.seq[i + 1])) if i + 1 < len(l.seq) else "(end)"
                return f"on {q(l.name)} between {prev_} and {next_}"
        st = self.s.stations[sid]
        return f"at {st.lat:.5f}, {st.lng:.5f}"

    def served(self, sid: str) -> str:
        names = sorted(self.lines_of.get(sid, []))
        return ", ".join(q(n) for n in names) if names else "no line"

    # --- DELETE -------------------------------------------------------------
    def orphans(self) -> list[str]:
        out = []
        for sid in sorted((i for i in self.st if i not in self.on_any_line), key=lambda i: (self.name(i), i)):
            best = None
            for l in self.active:
                for other in l.station_ids:
                    d = self.dist(sid, other)
                    if best is None or d < best[0]:
                        best = (d, l.name)
            near = f"nearest line {q(best[1])} at {fmt_dist(best[0])}" if best else "no lines on map"
            out.append(f"- {q(self.name(sid))}: on no line; {near} (delete, or add it to that line)")
        return out

    # --- MERGE ----------------------------------------------------------------
    def duplicates(self) -> tuple[list[str], set[frozenset]]:
        # Stations served only by draft lines are excluded. Pairs sharing a line are left
        # to the spacing check; placeholder names never count as a name match.
        ids = sorted((i for i in self.st if i in self.lines_of or i not in self.on_any_line),
                     key=lambda i: (self.name(i), i))
        out, pairs = [], set()
        for a, b in combinations(ids, 2):
            if set(self.lines_of.get(a, ())) & set(self.lines_of.get(b, ())):
                continue
            d = self.dist(a, b)
            same = self.name(a) == self.name(b) and not PLACEHOLDER_STATION.search(self.name(a))
            if d <= DUPLICATE_RADIUS_M or same:
                why = "same name, " if same else ""
                out.append(f"- {q(self.name(a))} ({self.served(a)}) x {q(self.name(b))} "
                           f"({self.served(b)}): {why}{fmt_dist(d)} apart")
                pairs.add(frozenset((a, b)))
        return out, pairs

    def spacing(self, skip_pairs: set[frozenset]) -> tuple[list[str], list[str]]:
        # Keyed by (station pair, mode): lines of one mode sharing a segment become one
        # item; lines of different modes on that segment are judged by their own limit.
        close: dict[tuple, tuple[str, str, float, list[str], str]] = {}
        far: dict[tuple, tuple[str, str, float, list[str], str]] = {}
        for l in self.active:
            if l.mode not in THRESHOLDS_M:
                continue
            lo, hi = THRESHOLDS_M[l.mode]
            for a, b in zip(l.seq, l.seq[1:]):
                if a == b:
                    continue
                pair = frozenset((a, b))
                key = (pair, l.mode)
                d = self.dist(a, b)
                bucket = close if d < lo else far if d > hi else None
                if bucket is None or (bucket is close and pair in skip_pairs):
                    continue
                if key in bucket:
                    if l.name not in bucket[key][3]:
                        bucket[key][3].append(l.name)
                else:
                    limit = f"{l.mode} {'min' if bucket is close else 'max'} {fmt_dist(lo if bucket is close else hi)}"
                    bucket[key] = (a, b, d, [l.name], limit)

        def render(bucket, fmt):
            rows = sorted(bucket.values(), key=lambda r: (sorted(r[3])[0], self.name(r[0]), self.name(r[1]), r[4]))
            return [fmt(a, b, d, ", ".join(q(n) for n in sorted(ls)), lim) for a, b, d, ls, lim in rows]

        merge = render(close, lambda a, b, d, ls, lim:
                       f"- {q(self.name(a))} -> {q(self.name(b))} on {ls}: {fmt_dist(d)} ({lim}); merge or drop one")
        create = render(far, lambda a, b, d, ls, lim:
                        f"- infill between {q(self.name(a))} and {q(self.name(b))} on {ls}: gap {fmt_dist(d)} ({lim})")
        return merge, create

    # --- HOUSEKEEPING ---------------------------------------------------------
    def housekeeping(self) -> list[str]:
        out = []
        for sid in sorted((i for i in self.st if PLACEHOLDER_STATION.search(self.name(i))),
                          key=lambda i: (self.name(i), i)):
            out.append(f"- station {q(self.name(sid))}: placeholder name ({self.where(sid)})")
        for l in self.drafts:
            out.append(f"- line {q(l.name)}: draft line ({l.mode or 'no mode'}, {len(l.seq)} stations); "
                       "excluded from spacing and duplicate checks")
        for l in self.active:
            if not l.mode:
                out.append(f"- line {q(l.name)}: no mode set")
            elif l.mode not in KNOWN_MODES:
                out.append(f"- line {q(l.name)}: unknown mode `{l.mode}`, spacing not checked")
        for l in self.active:
            if l.name.strip() and BAD_SPACING.search(l.name):
                out.append(f"- line {q(l.name)}: leading, trailing or doubled space in name")
        for gid, label in sorted(self.s.line_groups.items(), key=lambda kv: (kv[1], kv[0])):
            if label.strip() and BAD_SPACING.search(label):
                out.append(f"- line group {q(label)}: leading, trailing or doubled space in label")
        for l in self.active:
            if len(l.seq) < 2:
                out.append(f"- line {q(l.name)}: only {len(l.seq)} station(s)")
        for l in self.active:
            seq = l.seq[:-1] if len(l.seq) > 2 and l.seq[0] == l.seq[-1] else l.seq
            seen, reported = set(), []
            for sid in seq:
                if sid in seen and sid not in reported:
                    reported.append(sid)
                seen.add(sid)
            if len(reported) == 1:
                sid = reported[0]
                out.append(f"- line {q(l.name)}: visits {q(self.name(sid))} {seq.count(sid)} times "
                           "(not a loop closing on its first station)")
            elif reported:
                names = ", ".join(q(self.name(sid)) for sid in reported)
                out.append(f"- line {q(l.name)}: visits {len(reported)} stations more than once "
                           f"(drawn out-and-back?): {names}")
        return out


def render_report(snap: Snapshot) -> str:
    a = Analysis(snap)
    dupes, dupe_pairs = a.duplicates()
    too_close, gaps = a.spacing(dupe_pairs)
    thresholds = ", ".join(f"{m} {fmt_dist(lo)}-{fmt_dist(hi)}" for m, (lo, hi) in THRESHOLDS_M.items())

    out = [
        f"# Punch list: {snap.title}",
        "",
        f"- Snapshot: {snap.last_updated} ({snap.updated_text})",
        f"- Stations: {len(a.st)} (waypoints excluded: {snap.waypoint_count})",
        f"- Lines: {len(snap.lines)} ({len(a.drafts)} draft)",
        f"- Spacing thresholds: {thresholds}; FERRY and lines without a known mode not checked",
        f"- Duplicate radius: {DUPLICATE_RADIUS_M} m, or identical names",
        "",
    ]

    def section(title, groups):
        out.append(f"## {title}")
        out.append("")
        any_items = False
        for sub, items in groups:
            if not items:
                continue
            any_items = True
            if sub:
                out.append(f"### {sub}")
                out.append("")
            out.extend(items)
            out.append("")
        if not any_items:
            out.append("Nothing found.")
            out.append("")

    section("DELETE", [("", a.orphans())])
    section("MERGE", [("Near-duplicate station objects", dupes), ("Stops closer than the mode minimum", too_close)])
    section("CREATE", [("", gaps)])
    section("HOUSEKEEPING", [("", a.housekeeping())])
    return "\n".join(out).rstrip("\n") + "\n"


def analyze_file(snapshot_path: Path, root: Path, slug: str) -> tuple[Path, str]:
    snap = load_snapshot(snapshot_path)
    text = render_report(snap)
    d = report_dir(root, slug)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{snap.last_updated}.md"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path, text

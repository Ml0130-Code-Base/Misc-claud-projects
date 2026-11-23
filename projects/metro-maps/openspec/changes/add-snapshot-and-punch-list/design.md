# Design

## Context

See proposal.md for motivation. Verified facts that shape the approach (2026-11-23):

- `https://metrodreamin.com/view/<id>` returns server-rendered HTML (about 320-370 KB) with the full system in `<script id="__NEXT_DATA__" type="application/json">`. A bare request without the `%3D` encoding gets a 308 redirect; with it, HTTP 200.
- `id` = base64 of `<userId>|<mapIndex>`, with `=` padding URL-encoded as `%3D`.
- Payload path on both in-scope maps: `props.pageProps.fullSystem.map` holds `stations`, `lines`, `interchanges`, `lineGroups`, both keyed by object id. `props.pageProps.systemDocData` holds `title`, `lastUpdated` (epoch ms), `numStations`, `isPrivate`.
- Stations: `id, lat, lng, name, isWaypoint?, info?, densityInfo`. Lines: `id, name, color, mode, stationIds[], lineGroupId, waypointOverrides`.
- Waypoints are most objects: Denver 1,017 of 1,405; San Diego 2,062 of 2,368. Non-waypoint counts match `numStations` (388 and 306).
- Modes seen: `TRAM, LIGHT, BRT, RAPID, REGIONAL, FERRY`, plus empty string on 3 San Diego lines.
- The machine has Python 3.12 and no Node; this project uses the Python standard library only.

## Goals / Non-Goals

**Goals:**
- Same snapshot in = same punch list out, byte for byte, so runs can be compared.
- Robust to payload drift: if the expected path is missing, fail loudly with the keys that were found rather than producing an empty report.
- Exact strings: station and line names pass through untouched (en dashes, double spaces, typos included), so the punch list can be searched in the editor.

**Non-Goals:**
- Writing to MetroDreamin. The output is a list for a human to apply.
- Benchmark comparison against RTD FasTracks or the SANDAG 2021 plan. That needs reference datasets and is a later change.
- Restructuring advice such as merging Denver's `- Extension` lines into their parent lines. Those lines are reported as-is; whether they are intentional phasing is a design call left to the map author.
- Profile-page scraping or index discovery beyond the configured list.

## Decisions

**Layout.** `metro_maps/` package with `fetch.py`, `diff.py`, `analyze.py`, `geo.py` (haversine), `model.py` (load snapshot, filter waypoints), plus one CLI entry `python -m metro_maps <fetch|diff|analyze>`. Alternative: three loose scripts as the handover suggested. A package keeps the shared loader and haversine in one place and makes unit tests importable.

**Config.** `maps.json` in the project root: owner `userId` and a list of `{index, slug}` (`1 -> denver`, `14 -> san-diego`). The userId is public (it is in every map URL), so it is committed. Alternative: CLI arguments only, rejected because every run would repeat them.

**Snapshot format and naming.** Save the extracted `__NEXT_DATA__` JSON as-is (not a trimmed subset) to `snapshots/<slug>/<lastUpdated>.json`, UTF-8, pretty-printed with sorted keys so files are diffable by eye. Keeping the full payload means later checks (density, ridership, interchanges) need no refetch. If a file with that `lastUpdated` exists, skip the write. `lastUpdated` comes from the map's own data, so naming does not depend on the local clock.

**Snapshots stay out of git.** `snapshots/` and `reports/` are gitignored. Map #14 is marked private on MetroDreamin, and this repo may be pushed. The diff step only needs the files on local disk.

**HTTP.** `urllib.request`, browser-like `User-Agent`, follow redirects, 30 s timeout, one request per map with a 1 s pause between maps. No retries; a failure for one map is reported and the others still run.

**Draft lines.** A line whose name matches a placeholder pattern (`^Concept \d+$`, `^Line \d+$`, `^Untitled`, blank) is a draft. Draft lines produce one HOUSEKEEPING item each ("draft line, N stations") and are excluded from spacing, duplicate, and orphan checks. Their stations still count as "on a line" so they are not reported as orphans. This keeps San Diego's five `Concept` airport trams from producing dozens of noisy findings.

**Spacing thresholds per mode** (km between consecutive non-waypoint stations along `stationIds`):

| Mode | Too close | Too far |
|---|---|---|
| TRAM | < 0.25 | > 1.5 |
| LIGHT | < 0.5 | > 3.0 |
| BRT, RAPID | < 0.4 | > 3.0 |
| REGIONAL | < 1.5 | > 15.0 |
| FERRY, empty, unknown | not checked | not checked |

Stored as a table in `analyze.py` so they are easy to adjust. Lines with an empty or unknown mode get a HOUSEKEEPING item instead. Alternative: one threshold for all modes, rejected because it flags every tram stop or every regional stop.

**Category mapping.**
- DELETE: orphan stations (on no line), with the nearest line and distance as context in case "assign" is the better fix.
- MERGE: pairs of distinct station objects within 150 m of each other, or sharing an identical name, with the distance and the lines each serves. Also "too close" spacing pairs.
- CREATE: "too far" spacing gaps, written as "infill between A and B on <line>, gap X km".
- HOUSEKEEPING: placeholder station names, draft lines, lines with no or unknown mode, line names or line-group labels with leading, trailing or doubled spaces, lines with fewer than 2 stations, and stations repeated in a line's sequence other than a loop closing on its start.

**Report format.** Markdown at `reports/<slug>/<lastUpdated>.md`, also printed to stdout. Header with map title, snapshot timestamp, counts. Then the four sections in fixed order, each item one line, sorted by line name and then sequence order. Distances in metres under 1 km, else km with one decimal. Names in backticks so exact strings survive copy-paste.

**Diff semantics.** Match stations and lines by object id. Report: added, removed, renamed (same id, different name), moved (same id, > 25 m), waypoint toggled; lines added, removed, renamed, mode or color changed, station sequence changed (with the stations inserted or removed). Waypoint-only coordinate changes are summarized as a count, not listed.

**Testing.** `unittest`, no network. Fixtures: a small hand-built snapshot covering each check, and one trimmed real HTML page to test extraction. Run with `python -m unittest`.

## Risks / Trade-offs

- [MetroDreamin changes its page structure] -> Extraction fails with a clear message naming the missing key and listing the keys found; the last good snapshot stays usable offline.
- [Private map still served by `/view/`] -> This may change. If it does, the fetch reports a non-200 or missing payload for that map; the Chrome extension remains the fallback.
- [Thresholds are judgment calls] -> They live in one table and the report prints the thresholds used, so the list can be re-read with different numbers in mind.
- [150 m duplicate radius flags legitimate cross-platform pairs, such as a tram stop beside a rail station] -> MERGE items list the lines each station serves; a different mode on each side is a hint to keep both. Interchange data can suppress these in a later change.
- [Full payload snapshots are about 350 KB each] -> Acceptable for a few maps; skip-if-unchanged prevents duplicates.

## Open Questions

- Should San Diego Rapid routes that the author treats as regional rail (handover notes name 235, 280 and 290; the current map has no lines with those numbers in their names) use REGIONAL thresholds even though they are drawn with another mode? Deferrable: the threshold table can gain per-line overrides later without changing the specs.

# Tasks

## 1. Project setup

- [x] 1.1 Create the `metro_maps/` package with `__init__.py` and `__main__.py` exposing `fetch`, `diff` and `analyze` subcommands; verify `python -m metro_maps --help` lists all three
- [x] 1.2 Add `maps.json` with the owner userId and `{1: denver, 14: san-diego}`; add `snapshots/` and `reports/` to a project `.gitignore`; verify `git status` from the repo root does not show either folder after creating a file in each
- [x] 1.3 Add `tests/` with a `unittest` layout and a hand-built fixture snapshot (stations, waypoints, lines of several modes, a Concept line, an orphan, a near-duplicate pair, a doubled-space name, an en-dash name); verify `python -m unittest` discovers and runs an empty smoke test

## 2. Snapshot model and geometry

- [x] 2.1 Implement `geo.py` haversine distance and distance formatting (metres under 1 km, else km with one decimal); verify unit tests against known city-pair distances
- [x] 2.2 Implement `model.py` to load a snapshot, locate `fullSystem.map`, and fail with the missing key plus the keys found; split stations from waypoints and resolve each line to its non-waypoint sequence; verify tests on the fixture, including the structure-changed error

## 3. Fetch and store

- [x] 3.1 Implement map ID building with `%3D` padding encoding and `__NEXT_DATA__` extraction from HTML; verify tests using a trimmed saved HTML fixture
- [x] 3.2 Implement fetch with per-map failure isolation, skip-if-unchanged by `lastUpdated`, sorted pretty UTF-8 output, and non-zero exit on any failure; verify tests with a stubbed HTTP layer covering new, unchanged and failed maps
- [x] 3.3 Run `python -m metro_maps fetch` against the live site; verify `snapshots/denver/` and `snapshots/san-diego/` each get one file, station counts are 388 and 306 (or the map's current `numStations`), and a second run reports both maps as unchanged

## 4. Diff

- [x] 4.1 Implement the snapshot diff (stations added, removed, renamed, moved over 25 m, waypoint toggled; lines added, removed, renamed, mode or color changed, sequence changed; waypoint-only moves as a count) and the default "two most recent" selection; verify tests on fixture pairs for each change type, including an en-dash rename

## 5. Punch list

- [x] 5.1 Implement draft-line detection and the per-mode spacing table with MERGE (too close) and CREATE (too far) items; verify fixture tests for tram too-close, regional gap, ferry skipped and Concept lines excluded
- [x] 5.2 Implement orphan (DELETE, with nearest line and distance) and near-duplicate (MERGE, 150 m or identical name, with each station's lines) checks; verify fixture tests
- [x] 5.3 Implement HOUSEKEEPING checks (placeholder station names, draft lines, empty or unknown mode, whitespace issues in line names and group labels, lines under two stations, non-loop repeated stations); verify fixture tests including the doubled-space name shown exactly
- [x] 5.4 Implement the Markdown report writer (header with thresholds, fixed section order, empty-section text, backticked exact names) to `reports/<slug>/<lastUpdated>.md` and stdout; verify a test that two runs on the same fixture are byte-identical

## 6. Documentation

- [x] 6.1 Fill in the project README Setup and Run sections with the PowerShell commands for fetch, diff, analyze and tests; verify each documented command runs as written from `projects/metro-maps`

## 7. Integration check

- [ ] 7.1 Run `analyze` on the live Denver and San Diego snapshots; verify both reports are produced, San Diego lists the five Concept lines and three no-mode lines under HOUSEKEEPING, Denver lists `D Line  - North Extension` with the doubled space, and spot-check three items per map against the map in the editor

## Workflow follow-up

- Archive the change after the reports are reviewed.

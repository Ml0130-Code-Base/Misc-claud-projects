# Metro Maps

Snapshot MetroDreamin fantasy transit maps to disk and analyze them offline (station spacing, orphans, near-duplicates, placeholder names, housekeeping) into exact, copy-pasteable edit punch lists. In scope: Denver Metro Fantasy Rail Map (#1) and San Diego County Transit Fantasy (#14). Planning is tracked with OpenSpec in `openspec/` (run `openspec` commands from this folder).

## Setup

Python 3.12+, standard library only. No packages to install.

```powershell
winget install Python.Python.3.12
```

```powershell
Set-Location projects/metro-maps
```

Maps to track are listed in `maps.json` (`index` is the MetroDreamin map number, `slug` names the folder).

## Run

All commands run from `projects/metro-maps`.

Download every configured map; a map whose `lastUpdated` already has a snapshot is reported as unchanged and nothing is written:

```powershell
python -m metro_maps fetch
```

Fetch only some maps:

```powershell
python -m metro_maps fetch san-diego
```

Write the punch list for the newest snapshot (printed and saved to `reports/<slug>/<lastUpdated>.md`):

```powershell
python -m metro_maps analyze denver
```

Compare the two newest snapshots of a map (needs at least two fetches across an edit):

```powershell
python -m metro_maps diff san-diego
```

Compare two specific snapshots (replace `<older>` and `<newer>` with file names from `snapshots/san-diego/`):

```powershell
python -m metro_maps diff san-diego --old snapshots/san-diego/<older>.json --new snapshots/san-diego/<newer>.json
```

Run the tests (no network):

```powershell
python -m unittest
```

## Notes

- Snapshots go to `snapshots/<slug>/<lastUpdated>.json`, named by the map's own edit time. `snapshots/` and `reports/` are gitignored: map #14 is private on MetroDreamin.
- Map ID = base64 of `<userId>|<mapIndex>`; the page is `https://metrodreamin.com/view/<id>` with `=` encoded as `%3D`. The data is the `<script id="__NEXT_DATA__">` JSON at `props.pageProps.fullSystem.map.{stations,lines}`.
- Waypoints (`isWaypoint`) are excluded from every check; spacing is measured between consecutive real stations along each line.
- Spacing thresholds per mode live in `THRESHOLDS_M` in `metro_maps/analyze.py`; every report header prints the values used.
- Lines named like `Concept 3`, `Line 4` or `Untitled` are treated as drafts: listed once under HOUSEKEEPING and skipped by the spacing and duplicate checks.
- Station and line names are copied exactly, including en dashes (`San Diego–Santa Fe Depot`) and doubled spaces, so you can search for them in the editor.

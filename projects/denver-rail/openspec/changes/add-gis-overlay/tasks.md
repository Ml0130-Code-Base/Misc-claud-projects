# Tasks

Paths are relative to `projects/denver-rail/`. Tests use the standard-library `unittest` and run with `python -I -m unittest discover -s tests` from the project folder, inside `.venv`. Fixtures are small synthetic files under `tests/fixtures/`, never real downloads.

## 1. Environment and scaffolding

- [ ] 1.1 Install Python 3.12+ for Windows (python.org installer or `winget install Python.Python.3.12`), and use the `py` launcher so the Microsoft Store `python` alias doesn't get in the way; verify that `py -3.12 --version` prints 3.12 or newer in PowerShell
- [ ] 1.2 Create `.venv` with `py -3.12 -m venv .venv`; verify that `.\.venv\Scripts\python.exe --version` runs
- [ ] 1.3 Create the folders `data/raw/`, `data/reference/`, `data/clean/`, `scripts/`, `tests/fixtures/`, `out/` and `docs/`, plus a project `.gitignore` that ignores `data/raw/`, `data/clean/` and `.venv/`; verify that `git status` shows no files under ignored paths after a dummy file is placed in each
- [ ] 1.4 Add `requirements.txt` (empty apart from a comment saying stdlib only, with `shapely` only if design decision 2 is revisited); verify that `.\.venv\Scripts\pip install -r requirements.txt` succeeds
- [ ] 1.5 Write `scripts/geo.py` with a local metric projection centred on 39.74 N, point-to-segment distance, line sampling at a fixed spacing and grid-cell binning; verify with unit tests (known distances along Colfax and Broadway within 1%, 50 m sampling of a 1 km line gives 21 points)
- [ ] 1.6 Fill in the README Setup and Test sections with the PowerShell commands from 1.1 to 1.5; verify by running each command as written in a fresh PowerShell window

## 2. Reference data

- [ ] 2.1 Export `streetcar-corridor-scorecard.md` by hand from the chat Project into `docs/`; verify that the file opens and contains the ridership table (this is the owner's action; groups 3 to 4 can proceed without it)
- [ ] 2.2 Create `data/reference/corridors.csv`, with every corridor from handover section 6 (13 table rows; "17th Ave / 6th Ave" and "Cherokee / Leyden-Arvada" are split, giving 15 corridors), their 1946 route numbers, modern routes, rail/BRT status, verdict text and verdict class as assigned in design decision 4; verify with the validator from 2.6
- [ ] 2.3 Create `data/reference/through_pairs_1946.csv` with the three pairs (Berkeley to S Gaylord, W 44th to E 28th, Sheridan to E 40th), each mapped to the corridor ids on both ends; verify with the validator from 2.6
- [ ] 2.4 Create `data/reference/planned.csv` for East Colfax BRT, Federal BRT, Colorado Blvd BRT, the L Line extension and the Colorado Connector, each with `source_route`, end stops, target year and `as_of` 2026-09; verify with the validator from 2.6 (stop ids are filled in during task 5.6, once GTFS is available)
- [ ] 2.5 Create `data/reference/ridership.csv` from the scorecard export (header only until 2.1 is done) and an empty `data/reference/cdot_to_1946.csv` with headers; verify with the validator from 2.6
- [ ] 2.6 Write `scripts/check_reference.py`, which checks required columns, that `verdict_class` is one of the five allowed values, unique corridor ids, and that through-pair corridor ids exist in `corridors.csv`; verify with unit tests covering one good fixture and one fixture for each error type, and that it passes on the real reference files
- [ ] 2.7 Document the reference files (what each holds, who edits it, where its values come from) in the README; verify that every file in `data/reference/` is described

## 3. Fetch and provenance

- [ ] 3.1 Verify the current download URLs for the CDOT historic streetcar layer (GeoJSON export preferred), the RTD GTFS feed, LODES8 CO `od_main_JT00`, `od_aux_JT00` and `xwalk` (latest year), and the tundria 1946 route page; record them with the check date in `NOTES.md`
- [ ] 3.2 Write `scripts/fetch.py`, which downloads each source into `data/raw/<source>/` and writes `data/raw/manifest.json` entries (URL, timestamp, size, SHA-256); verify with a unit test that fetches a `file://` fixture URL and checks the manifest entry
- [ ] 3.3 Make `fetch.py` exit non-zero when a download fails, printing the URL and the expected manual-download path; verify with a unit test that uses an unreachable URL
- [ ] 3.4 Add a `--register-manual` mode that records hand-placed files as source "manual" with size and SHA-256; verify with a unit test
- [ ] 3.5 Write `scripts/verify_raw.py`, which checks every raw file's SHA-256 against the manifest and exits non-zero on any mismatch; verify with a unit test that alters a fixture file after registering it
- [ ] 3.6 Run the fetch for real, placing any blocked source by hand and registering it; verify that the manifest lists every source, then append a dated `NOTES.md` entry with GTFS `feed_info` dates and the LODES year

## 4. Historic corridors

- [ ] 4.1 Inspect the CDOT download's schema, CRS and feature count; record the field list, CRS and count in `NOTES.md`, and note whether any field carries route names or numbers
- [ ] 4.2 Write `scripts/historic.py` to load the CDOT layer and write `data/clean/historic.geojson` in EPSG:4326 with every source attribute unchanged; verify with a unit test that compares fixture attributes and checks coordinates fall inside the Denver metro box. If the source is only available in a projected CRS, add `pyproj` to `requirements.txt` and record why in `NOTES.md`
- [ ] 4.3 Add `route_1946` matching (source attribute first, `cdot_to_1946.csv` override wins, otherwise empty and listed as unmatched); verify with unit tests for each of the three paths
- [ ] 4.4 Attach `corridor_id`, `verdict_text` and `verdict_class` from `corridors.csv`, and list corridors with no feature as unrepresented; verify with unit tests
- [ ] 4.5 Fill in `cdot_to_1946.csv` for features that could not be matched automatically, using the tundria 1946 list; verify by rerunning `historic.py` and confirming that every remaining unmatched feature is explained in `NOTES.md`

## 5. Transit network

- [ ] 5.1 Build a small synthetic GTFS fixture (2 bus routes, 1 rail route, 2 shapes per route, a few stops and a calendar) for the tests in this group
- [ ] 5.2 Write `scripts/transit.py` to check that the feed's service end date is on or after 2026-09-27, refuse to build otherwise, and record the service dates; verify with unit tests on both a stale and a current fixture calendar
- [ ] 5.3 Build route geometry (the shape with the most weekday trips per direction, merged into one feature per route) and split it into `bus_routes.geojson` and `rail_lines.geojson` by `route_type`; verify with unit tests that each route appears exactly once in the correct layer
- [ ] 5.4 Build `stations.geojson` for rail stops, each listing every serving rail route; verify with a unit test using a shared fixture station
- [ ] 5.5 Compute the weekday 10:00 to 14:00 headway for the busiest direction, leaving it empty when there is no midday service; verify with unit tests for both cases
- [ ] 5.6 Attach `ridership.csv` fields to bus routes, leaving them empty when missing. Fill in the stop ids in `planned.csv` from the real feed, then build `planned.geojson` by clipping source-route shapes between the end stops with `status`, `target_year` and `as_of`. Verify with unit tests for clipping and for missing ridership
- [ ] 5.7 Run `transit.py` on the real feed; verify that the 15, 15L, 16, 31, 38 and 40 routes and the W, A, E, H and L lines are present, and record the layer counts in `NOTES.md`

## 6. Commute flows

- [ ] 6.1 Build synthetic LODES OD and crosswalk fixtures with blocks inside and outside the seven RTD counties
- [ ] 6.2 Write `scripts/flows.py` to filter both ends to the seven RTD counties and produce `tract_density.geojson` (workers living there and jobs located there at the job-weighted centroid); verify with unit tests that totals match fixture sums and that out-of-area records are excluded
- [ ] 6.3 Build `commute_pairs.geojson` (2 km cells, combining both directions, minimum distance 3 km, top 100), with the cell size, minimum distance and N as named constants; verify with unit tests for the distance floor and for ranking and the cap
- [ ] 6.4 Record the LODES year and job type as layer metadata on both outputs; verify with a unit test
- [ ] 6.5 Run `flows.py` on the real data; record the counts and the LODES year in `NOTES.md`

## 7. Corridor comparison

- [ ] 7.1 Write `scripts/compare.py` to produce one comparison record per corridor, with the scorecard's routes, status, verdict and ridership; verify with a unit test that the record count equals the corridor count and that scorecard routes are always present
- [ ] 7.2 Add the geometric check (50 m sampling, 150 m buffer, overlap share threshold as a named constant), listing geometric matches with their share; verify with unit tests on synthetic parallel and diverging lines
- [ ] 7.3 Report disagreements as `named-not-overlapping` and `overlapping-not-named` without changing either input; verify with unit tests for each type
- [ ] 7.4 Add the through-routing comparison for the 1946 pairs (which modern routes cross downtown on both corridors, plus their ridership change); verify with a unit test using a fixture pair
- [ ] 7.5 Run `compare.py` on the real layers; write the results to `data/clean/comparison.json` and note in `NOTES.md` any disagreement that looks like a threshold artifact rather than a real finding

## 8. Overlay map

- [ ] 8.1 Write `scripts/map_template.html` (Leaflet 1.9.4 from cdnjs, CARTO Positron no-labels base, labels overlay, plain background fallback) and `scripts/build_map.py` to embed the clean layers as `const` GeoJSON in `out/map.html`; verify by opening the file through `file://` with tiles blocked and confirming every layer renders
- [ ] 8.2 Build a combined legend and toggle panel for Historic lines, Today's bus, Rail+BRT and Commute flows; verify in the browser that each toggle hides only its own group
- [ ] 8.3 Style historic lines by the five verdict classes plus an "unmatched" style, draw planned features dashed, and use muted modern layers with RTD route colors for rail; verify that the legend shows all six historic styles and that the colors match `corridors.csv` for three sample lines
- [ ] 8.4 Add popups for historic lines, bus routes, planned features and commute features with the attributes from the overlay-map spec; verify by clicking one of each in the browser
- [ ] 8.5 Make the legend collapsible and the layout fit 375 px; verify at a 375 px viewport that there is no horizontal scroll and every toggle can be reached
- [ ] 8.6 Add a Map section to the README (how to rebuild, how to open, what each layer means); verify that the instructions work as written

## 9. Reports

- [ ] 9.1 Write `scripts/report.py` to produce `out/layer_stats.json` (count per clean layer, unmatched features, unrepresented corridors, disagreements, thresholds used); verify with a unit test on fixture clean layers
- [ ] 9.2 Generate `summary.md` sections between marker comments (source versions, layer counts, join results, disagreements, a "re-check before publishing" list of planned-project dates), keeping text outside the markers; verify with a unit test that regenerates the file twice and checks hand-written text survives
- [ ] 9.3 Add `run_all.ps1` to run `check_reference`, `fetch` (skipping downloads already in the manifest), `verify_raw`, `historic`, `transit`, `flows`, `compare`, `build_map`, `report` and a final `verify_raw`, stopping at the first failure; verify that it exits non-zero when a reference file is broken on purpose

## 10. Integration checks

- [ ] 10.1 Run `run_all.ps1` from a clean `data/clean/` and confirm that it completes, that `verify_raw` passes at the end, and that a second run produces identical `data/clean/` files
- [ ] 10.2 Confirm on the map that every corridor from handover section 6 appears with the right verdict color
- [ ] 10.3 Spot-check Colfax, 38th Ave and Federal against the scorecard (routes, ridership, verdict, planned BRT year) and record the results in `NOTES.md`
- [ ] 10.4 Write the hand-written "surprises" section of `summary.md` (anything the data contradicts in the scorecard), keeping the whole file to one page
- [ ] 10.5 Run the full unit test suite and confirm that it passes; then update the denver-rail status in the root `README.md` Projects table

## Workflow follow-up

- Bring `NOTES.md`, `out/map.html` and `summary.md` back to the "Denver/CO Rail" chat Project for the synthesis document.
- Archive this change after review.
- Possible later changes: Reddit sentiment (handover Task B, once it's known whether it was already run), station-level ridership ranking, a Metro Maps corridor overlay, and schematic export.

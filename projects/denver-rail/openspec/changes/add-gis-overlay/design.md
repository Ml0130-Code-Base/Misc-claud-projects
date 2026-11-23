# Design

## Context

See proposal.md (Why) for the motivation and specs/ for the behavior contract. This document covers how the pipeline is built.

Constraints that shape the approach:

- **Machine:** Windows; run commands are given in PowerShell. Python is **not installed** on this machine yet: `python` resolves only to the Microsoft Store alias, and Node is not installed either. Setup has to install Python 3.12+ and create a project-local `.venv`.
- **Self-contained project:** all code, dependencies and data stay under `projects/denver-rail/`. Nothing is added at the repo root.
- **Source data is outside our control:**
  - We don't know the CDOT layer's attribute schema until we download it. In particular, we don't know whether it carries 1946 route numbers or line names.
  - RTD's GTFS has no ridership data and no planned projects.
  - LODES runs two to three years behind.
- **Hand-curated inputs:** the corridor verdicts and the 2024/2019 ridership figures come from the scorecard, which is curated by hand in the chat Project. This repo consumes them; it does not recompute them.
- **Output:** one static HTML page, with no server and no database.

## Goals / Non-Goals

**Goals:**
- Running the whole pipeline again from the raw files gives the same clean layers and the same map.
- Every number on the map can be traced to a raw file plus a hand-curated reference row.
- Keep the dependency footprint small enough that setup on Windows is "install Python, create venv, `pip install -r requirements.txt`" (ideally with nothing to install from pip).

**Non-Goals:**
- No tract or block polygon choropleths. Commute density is drawn as points, which avoids needing TIGER shapefiles and a shapefile reader.
- No automatic parsing of the scorecard markdown. Its figures are transcribed once into a reference CSV.
- No ridership modeling or forecasting. The map shows reported figures only.
- No schematic or diagrammatic redraw of lines. Geometry is geographic.

## Decisions

### 1. Pipeline shape: stage scripts over three data tiers

```
data/raw/        downloads, never edited, gitignored
data/reference/  hand-curated CSVs, committed (the human-owned truth)
data/clean/      derived GeoJSON/JSON, gitignored, fully regenerable
out/             map.html + layer_stats.json, committed
```

Each stage is a separate script in `scripts/`. It reads only from the tiers above it and writes only to `data/clean/` or `out/`. The stages are: `fetch`, `historic`, `transit`, `flows`, `compare`, `build_map` and `report`. A `run_all.ps1` runs them in order.

*Alternative considered:* a single notebook, rejected because it is hard to rerun cleanly and hard to diff. A Makefile was also rejected because it is awkward on Windows.

### 2. Python standard library only, with `shapely` as an escape hatch

All geometry work happens at metro scale (about 60 km). Points are converted to local metres with an equirectangular projection centred on Denver (39.74 N), where the error is well under 1%. That handles buffering, nearest-distance checks and grid binning in a few dozen lines, so we avoid geopandas and GDAL wheels on Windows.

The geometric cross-check works like this:
1. Sample each historic line every 50 m.
2. Measure the distance from each sample to every candidate modern shape.
3. Record the share of samples that fall within 150 m of the modern shape. This is the overlap.

If that turns out too slow or too fragile, we add `shapely` to `requirements.txt`. The specs do not change either way.

*Alternative considered:* geopandas, rejected because it is a heavy install for what amounts to point-to-line distances.

### 3. The scorecard mapping lives in committed reference CSVs

These files in `data/reference/` are the human-owned inputs:

| File | Contents |
|---|---|
| `corridors.csv` | One row per section 6 corridor: `corridor_id`, name, `routes_1946` (pipe-separated), `modern_routes`, `rail_brt_status`, `verdict_text`, `verdict_class` |
| `cdot_to_1946.csv` | Optional override: CDOT feature id → `routes_1946`. Used when a CDOT feature can't be matched automatically. |
| `ridership.csv` | `route`, `ridership_2019`, `ridership_2024`, `pct_change`, `source` (transcribed from the scorecard) |
| `planned.csv` | Planned or unbuilt corridors: `project`, `mode`, `status`, `target_year`, `source_route`, `from_stop`, `to_stop`, `as_of` |
| `through_pairs_1946.csv` | The three 1946 through-routed pairs named in the handover |

**Matching CDOT features to 1946 routes:** if a CDOT name or number field matches a route in `corridors.csv`, use it. Otherwise fall back to `cdot_to_1946.csv`. Anything still unmatched is flagged, never guessed.

*Alternative considered:* parsing the scorecard markdown directly. Rejected because the table formatting is not a stable interface, and a CSV gives clean diffs whenever a verdict changes.

### 4. Five verdict classes

| Class | Corridors (from scorecard section 6) |
|---|---|
| `built-or-building` | Golden via Lakewood; Colfax; Federal/Barnum; Park Hill |
| `returning` | Boulder interurban; Larimer to RiNo/Cole |
| `next-candidate` | Broadway/Englewood; Alameda/S Gaylord; Northwest via 38th Ave |
| `feeder-only` | Five Points/Downing; S Pearl/University Park/S Gaylord |
| `leave` | 17th Ave; 6th Ave; Cherokee; Leyden/Arvada |

Colfax is classed `built-or-building`. Its gap, West Colfax, is kept in `verdict_text` and shown in the popup, not split into a separate class.

**Colors:**
- The five classes use a categorical palette that works for colorblind viewers and reads in order from strong to muted. `leave` gets a desaturated grey.
- Modern layers use RTD-like neutrals: thin grey for bus, and line-specific colors for rail. That keeps the historic layer as the visual focus.

### 5. Modern network from GTFS, plus planned projects from reference data

- **Route geometry:** for each route and direction, use the `shape_id` with the most weekday trips. Merge the two directions into one feature per route.
- **Mode:** taken from `route_type`, where 0 is light rail, 2 is commuter rail and 3 is bus.
- **Frequency:** a weekday midday headway (10:00 to 14:00, busiest direction) is computed from `stop_times`. This supports the "every 30 min" and "hourly" verdicts with data.
- **Planned BRT and rail:** these are not in GTFS. Each `planned.csv` row is drawn by clipping its `source_route` GTFS shape between `from_stop` and `to_stop`. For example, East Colfax BRT comes from route 15 between Broadway and the I-225 area. Planned features are drawn dashed and carry `status`, `target_year` and `as_of`.
- **The 15/15L and 16 overlap:** both routes are kept as separate features. The comparison stage reports every modern route above the overlap threshold, not just one.

*Alternative considered:* hand-tracing planned alignments in geojson.io. Rejected because clipping the existing shape is reproducible and accurate enough at corridor scale.

### 6. Commute flows without polygons

Use LODES8 `co_od_main_JT00` and `co_od_aux_JT00` for the latest available year. Join them to `co_xwalk.csv.gz`, which gives every block its centroid latitude/longitude and its tract.

- **Filter:** only blocks in RTD district counties: Adams, Arapahoe, Boulder, Broomfield, Denver, Douglas and Jefferson.
- **Density layer:** one point per tract, carrying `workers_home` (residents who work) and `jobs_work` (jobs located there), at the tract's job-weighted centroid. It is drawn as proportional circles.
- **Top pairs:** blocks are grouped into 2 km grid cells. The 100 largest cell-to-cell flows between cells at least 3 km apart become straight desire lines. Width shows flow, and directions are combined.

The 3 km floor keeps short local hops from drowning out the longer trips that rapid transit serves.

*Alternative considered:* a tract-to-tract top-N list. Rejected because tract pairs are small and noisy, and the downtown tracts would take every slot.

### 7. Map: Leaflet with layers embedded in the page

- **Library:** Leaflet 1.9.4 from cdnjs.
- **Basemap:** a light, low-contrast raster (CARTO Positron, no labels), with a labels-only overlay above the data layers.
- **Data:** `build_map` reads a hand-written `scripts/map_template.html` and inserts the clean layers as `const` GeoJSON objects. The output is one file that only needs the network for tiles.
- **Layer toggles:** one per layer group, from a custom legend panel rather than Leaflet's default control, so the legend can double as the color key.
- **Popups:**
  - Historic lines show the 1946 route(s), corridor, verdict and today's routes.
  - Bus routes show 2019 and 2024 ridership, change and headway.

*Alternative considered:* MapLibre GL, which has better styling, but a good-looking vector basemap needs a style server or API key. Leaflet with raster tiles is simpler and looks clean enough.

### 8. Provenance and reports

- **`fetch`** writes `data/raw/manifest.json`. Each entry holds the source URL, retrieval timestamp, SHA-256 and byte size. GTFS also records `feed_info` dates; LODES also records its data year.
- **Manual downloads:** if an automatic fetch fails, `fetch` prints the URL and the expected file name, then stops. The manifest also records files that were downloaded by hand.
- **`report`** writes `out/layer_stats.json` (row counts, unmatched CDOT features, comparison disagreements) and regenerates the data sections of `summary.md` between marker comments. The narrative "surprises" section stays hand-written.
- **`NOTES.md`** is an append-only, dated working log written during implementation runs. It records feed dates, row counts and decisions.

**Safety:** all downloaded files are treated as untrusted data. Scripts read them by path, live in `scripts/` (never in `data/raw/`), and run with `python -I`.

### 9. Git hygiene

`projects/denver-rail/.gitignore` ignores `data/raw/`, `data/clean/` and `.venv/`. Committed are `data/reference/`, `out/map.html`, `out/layer_stats.json`, `NOTES.md`, `summary.md` and `docs/`.

## Risks / Trade-offs

- **[CDOT layer has no usable route identifiers]** → `cdot_to_1946.csv` is filled in by hand, using the tundria 1946 list and the map itself. This is the largest manual step. Unmatched features are listed rather than silently dropped.
- **[CDOT lines are segments, not whole routes]** → many features map to one corridor. Verdict coloring works per feature, and counts are reported per corridor and per feature.
- **[Scorecard not exported yet]** → `ridership.csv` and the `corridors.csv` verdict text are blocked until `docs/streetcar-corridor-scorecard.md` arrives. The section 6 table in the handover can seed `corridors.csv` in the meantime, and ridership attributes stay empty, not guessed.
- **[LODES lags reality (2022 or 2023 data vs. 2026 service)]** → the map labels the data year, and `summary.md` notes that commute patterns predate the 2026 service changes.
- **[Planned-project dates are as of Sept 2026]** → `planned.csv` carries `as_of`, popups show it, and `summary.md` lists the dates to re-check before anything is published.
- **[Basemap tiles need a network connection and have usage terms]** → acceptable for a personal research map. The layers still render on a blank background if tiles fail.
- **[The 150 m / 50 m thresholds misjudge streets that run side by side, e.g. Colfax vs. 14th/16th]** → thresholds are constants recorded in `layer_stats.json`. Disagreements are reported for review, not auto-resolved.
- **[Fetch URLs change]** → every URL is verified at implementation time and recorded in the manifest. Manual download is always a supported path.
- **[Python not installed]** → setup is the first task. README setup steps are written for PowerShell.

## Open Questions

- Which LODES year to use. Take the latest available when fetching; it doesn't affect the approach.
- The grid size (2 km), top-N (100) and distance floor (3 km) for commute pairs. These are starting values, to be tuned after the first render.
- The exact rail line colors. Match RTD's published line colors once the GTFS `route_color` field is inspected.

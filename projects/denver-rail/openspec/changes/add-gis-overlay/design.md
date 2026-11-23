# Design

## Context

See proposal.md (Why) for the motivation and specs/ for the behavior contract. This document covers how the pipeline is built.

Constraints that shape the approach:

- **Machine:** Windows; run commands are given in PowerShell. Python 3.12 is installed and reachable as `py -3.12` (3.12.10 as of 2026-11-23). The bare `python` command still resolves to the Microsoft Store alias, so every command uses the `py` launcher or the project `.venv`. Node is not installed.
- **Self-contained project:** all code, dependencies and data stay under `projects/denver-rail/`. Nothing is added at the repo root.
- **Source data is outside our control:**
  - The CDOT schema is now known (see "Verified sources" below). Route numbers are embedded in a free-text name field rather than held in a dedicated column.
  - RTD's GTFS has no ridership data and no planned projects.
  - LODES runs two to three years behind.

### Verified sources (checked 2026-11-23)

**CDOT historic streetcars.** The data is the ArcGIS feature service `Historic_Streetcar_Lines_of_Colorado`, owned by `ColoradoDOT_GIS` (item `4f80030034cb45cd88e59c4eaf31435d`). Base URL: `https://services.arcgis.com/yzB9WM8W0BO3Ql7d/arcgis/rest/services/Historic_Streetcar_Lines_of_Colorado/FeatureServer`. It is the GIS output of CDOT report CDOT-2020-11 and covers the whole state, split by technology:

| Layer | Name | Features (statewide) |
|---|---|---|
| 0 | `Horse_Streetcar` | 137, all closed by about 1900 |
| 1 | `Steam_Dummy` | 22 |
| 2 | `Cable_Streetcar` | 33, closed 1891 to 1900 |
| 3 | `Electric_Streetcar` | 481 |
| 4 | `Technology_Unknown_TBD_Streetcar` | 10 |
| 5 | `All_Lines` | 683, the union of 0 to 4 |

- Native CRS is NAD83 / UTM 13N (EPSG:26913). The server reprojects on request: `<base>/3/query?where=1%3D1&outFields=*&outSR=4326&f=geojson` returns HTTP 200 (about 630 KB). `maxRecordCount` is 2000, so one request returns the whole layer.
- Fields include `SEG_ID`, `LINE_ID`, `LINE_NM`, `COUNTY`, `CITY`, `TECH_DESCRIPTION`, `OPERATING_CO`, `OPS_START`, `OPS_END` (epoch-ms dates), `ACCURACY`, `SOURCE` and `DATA_STATUS`. There is no dedicated route-number field.
- 1946 route numbers sit at the end of `LINE_NM` as comma-separated integers, for example `DCTramwayCo- 17th Avenue Line, 27, 47`.
- Within the seven RTD counties, layer 3 has 265 segments. Of these, 85 were operating in 1946 (`OPS_START` year ≤ 1946 ≤ `OPS_END` year). 51 of those 85 have a parseable route number, covering 31 distinct routes. The other 34 have none, and many of them are interurbans (D&NW Arvada Flyer; the DL&G Golden, Morrison and Ruby branches).
- `COUNTY` can hold more than one county (`Denver, Jefferson`) and some values carry trailing spaces.
- One `LINE_NM` ends in `167` (`DCTramwayCo- Berkeley- Elitch's Line, 167`). This is probably a typo for routes 16 and 7, so it is left to the override table rather than guessed.
- Most geometry is `Estimated to Roadway Centerline` (`ACCURACY`), and the dates come from published histories. Both are research estimates, not survey data.

**RTD GTFS.** The static feed is at `https://www.rtd-denver.com/files/gtfs/google_transit.zip`. RTD asks users to accept a licence on its GTFS page before downloading, so an automated fetch may be refused and a manual download is the expected path. The Mobility Database listing (mdb-178) shows a service range ending 2026-06-06, which is stale, so the feed's own `calendar` dates have to be checked.

**LODES.** The LODES8 Colorado directory (`https://lehd.ces.census.gov/data/lodes/LODES8/co/od/`) has `co_od_main_JT00` files for 2021 to **2024**. 2024 is the latest year available.
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
| `cdot_to_1946.csv` | Optional override: CDOT `SEG_ID` → `routes_1946`, plus a `note` column. Used when a CDOT feature can't be matched automatically or its parsed number is wrong. |
| `ridership.csv` | `route`, `ridership_2019`, `ridership_2024`, `pct_change`, `source` (transcribed from the scorecard) |
| `planned.csv` | Planned or unbuilt corridors: `project`, `mode`, `status`, `target_year`, `source_route`, `from_stop`, `to_stop`, `as_of` |
| `through_pairs_1946.csv` | The three 1946 through-routed pairs named in the handover |

**Matching CDOT features to 1946 routes:**
1. An override row in `cdot_to_1946.csv`, keyed by `SEG_ID`, always wins.
2. Otherwise, parse the trailing comma-separated integers from `LINE_NM` (for example `…, 27, 47` gives `27|47`). Keep them only if every number is a route listed in `corridors.csv` or the tundria 1946 list.
3. Anything still unmatched gets an empty `route_1946` and is listed in the run report. It is never guessed.

A parsed number that is not a known route, such as the `167` in the Berkeley–Elitch's segment, counts as unmatched and is reported with its raw `LINE_NM`. It needs an override row. Decision 10 covers which features reach this step. The expected manual workload is about 34 segments.

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

Use LODES8 `co_od_main_JT00` and `co_od_aux_JT00` for the latest available year, which is 2024 as of 2026-11-23. `fetch` picks the newest year listed in the directory, so a later release is used automatically. Join them to `co_xwalk.csv.gz`, which gives every block its centroid latitude/longitude and its tract.

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
- **Manual downloads:** if an automatic fetch fails, `fetch` prints the URL and the expected file name, then stops. The manifest also records files that were downloaded by hand. The RTD GTFS zip is the source most likely to need this, because RTD's GTFS page asks for its licence to be accepted. The licence is accepted by a person in a browser, never by the script.
- **CDOT request:** `fetch` downloads layer 3 only, as GeoJSON in EPSG:4326, using the query URL from "Verified sources". The full query URL is recorded in the manifest.
- **`report`** writes `out/layer_stats.json` (row counts, unmatched CDOT features, comparison disagreements) and regenerates the data sections of `summary.md` between marker comments. The narrative "surprises" section stays hand-written.
- **`NOTES.md`** is an append-only, dated working log written during implementation runs. It records feed dates, row counts and decisions.

**Safety:** all downloaded files are treated as untrusted data. Scripts read them by path, live in `scripts/` (never in `data/raw/`), and run with `python -I`.

### 9. Git hygiene

`projects/denver-rail/.gitignore` ignores `data/raw/`, `data/clean/` and `.venv/`. Committed are `data/reference/`, `out/map.html`, `out/layer_stats.json`, `NOTES.md`, `summary.md` and `docs/`.

### 10. Historic source: electric layer, RTD counties, the 1946 network

The `historic` stage reads the raw layer-3 (`Electric_Streetcar`) GeoJSON and keeps a feature only when both of these hold:

- **County:** at least one entry in `COUNTY`, split on commas and trimmed, is one of the seven RTD counties. These are the same counties as the commute filter in decision 6.
- **In service in 1946:** the `OPS_START` year is 1946 or earlier, and the `OPS_END` year is 1946 or later. A missing `OPS_START` counts as "started before 1946" and is noted in the run report. One RTD-county segment has no start date.

The result is about 85 segments. Features dropped by either filter are counted by reason in `layer_stats.json`, so the cut can be audited. Matching (decision 3) and verdicts run only on the features that are kept.

**Why the electric layer, not `All_Lines`:** the horse, steam and cable layers all closed by 1900. Including them would put 19th-century routes under 1946 route labels and verdict colours. **Why a 1946 cut, not every electric segment:** 30 segments closed in 1941, and dozens closed in 1930 to 1931. The proposal and the historic-corridors spec both frame the layer as the 1946 network.

*Alternative considered:* keep all 265 electric segments and add an `in_1946` flag. Rejected for now because pre-1946 segments would flood the unmatched list. Showing closures as faded context remains an open question.

## Risks / Trade-offs

- **[Route numbers live in free text]** → they are parsed from the end of `LINE_NM`, which matched 51 of the 85 segments running in 1946. The other 34 segments (mostly interurbans) and anomalies like `167` go into `cdot_to_1946.csv` by hand, using the tundria 1946 list. Unmatched features are listed, never silently dropped.
- **[CDOT dates and alignments are research estimates]** → `ACCURACY` and `SOURCE` stay on every feature (they are source attributes), so the precision of any line can be looked up. The 1946 cut uses years, not exact dates, to avoid false precision.
- **[The CDOT service is changed or withdrawn]** → the raw GeoJSON is kept in `data/raw/` with its SHA-256. The CDOT-2020-11 report is the fallback reference.
- **[CDOT lines are segments, not whole routes]** → many features map to one corridor. Verdict coloring works per feature, and counts are reported per corridor and per feature.
- **[Scorecard not exported yet]** → `ridership.csv` and the `corridors.csv` verdict text are blocked until `docs/streetcar-corridor-scorecard.md` arrives. The section 6 table in the handover can seed `corridors.csv` in the meantime, and ridership attributes stay empty, not guessed.
- **[LODES lags reality (2024 data vs. 2026 service)]** → the map labels the data year, and `summary.md` notes that commute patterns predate the 2026 service changes.
- **[RTD GTFS sits behind a licence page]** → treated as a manual download from the start (decision 8). The feed's own `calendar` dates are checked against 2026-09-27 (task 5.2), because third-party listings are stale.
- **[Planned-project dates are as of Sept 2026]** → `planned.csv` carries `as_of`, popups show it, and `summary.md` lists the dates to re-check before anything is published.
- **[Basemap tiles need a network connection and have usage terms]** → acceptable for a personal research map. The layers still render on a blank background if tiles fail.
- **[The 150 m / 50 m thresholds misjudge streets that run side by side, e.g. Colfax vs. 14th/16th]** → thresholds are constants recorded in `layer_stats.json`. Disagreements are reported for review, not auto-resolved.
- **[Fetch URLs change]** → every URL is verified at implementation time and recorded in the manifest. Manual download is always a supported path.
- **[`python` is the Microsoft Store alias]** → every command uses `py -3.12` or `.\.venv\Scripts\python.exe`, never bare `python`. README setup steps are written for PowerShell.

## Open Questions

- Whether to also show the electric lines that closed before 1946 (mostly in 1930 to 1931 and 1941) as faded, unlabelled context. They are dropped for now (decision 10). Adding them would mean a second clean layer, not a change to the 1946 layer.
- The grid size (2 km), top-N (100) and distance floor (3 km) for commute pairs. These are starting values, to be tuned after the first render.
- The exact rail line colors. Match RTD's published line colors once the GTFS `route_color` field is inspected.

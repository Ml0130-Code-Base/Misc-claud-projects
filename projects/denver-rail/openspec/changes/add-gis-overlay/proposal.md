# Proposal

## Why

The streetcar corridor scorecard (Sept 2026) rates each 1946 Denver Tramway line against today's bus ridership and RTD's rail and BRT plans, but it exists only as a table. Putting the old lines, today's network and commute demand on one map lets us check those verdicts against real geography and spot what the table cannot show. One example is whether the 1946 through-routed pairs line up with the routes that are holding or gaining riders today. The aim is a corridor map for deciding where modern rapid transit makes sense. It is not a case for bringing streetcars back.

## What Changes

- Add a reproducible local pipeline in `projects/denver-rail/` that downloads source data, normalizes it to GeoJSON (EPSG:4326) and builds one static, self-contained map page.
- Ingest the CDOT "Historic Streetcar Lines" layer, keep its attribute table unchanged, and label each line with its 1946 route number(s) and the scorecard verdict.
- Build modern RTD layers from a freshly pulled GTFS feed (bus routes, rail lines, BRT where present, stations). Attach 2024 and 2019 ridership from the scorecard, since GTFS does not include ridership.
- Group Census LODES origin-destination commute flows into a coarse density layer and a set of top commute pairs.
- Compare each historic corridor with today's service: attach the modern route(s), rail or BRT status and verdict from the scorecard's mapping table (the source of truth), then check that table against the geometry and report any disagreements.
- Render `out/map.html` with toggleable layers (Historic lines, Today's bus, Rail+BRT, Commute flows), historic lines colored by verdict, and a professional legend and color system.
- Record each source's version or feed date, the row count of every cleaned layer, and any historic line that matches no 1946 route in `NOTES.md`. Write a one-page `summary.md` for hand-back to the chat synthesis.

Out of scope for this change: Reddit sentiment collection, station-level ridership ranking, overlaying Metro Maps proposed corridors, schematic-style export, and any hosting.

## Capabilities

### New Capabilities

- `historic-corridors`: The cleaned historic streetcar line layer, with CDOT attributes preserved and 1946 route numbers and verdicts attached.
- `transit-network`: Current RTD bus, rail and BRT routes and stations from GTFS, with ridership attributes taken from the scorecard.
- `commute-flows`: LODES commute flows grouped into a density surface and top origin-destination pairs.
- `corridor-comparison`: Links each historic corridor to today's service and verdict, and checks the hand-made mapping against geometric overlap.
- `overlay-map`: The static, self-contained interactive map with layer toggles, verdict coloring and legend.
- `data-provenance`: Keeps raw downloads unedited, records source dates and layer row counts, and produces the `NOTES.md` log and `summary.md` report.

### Modified Capabilities

None. This is the project's first change.

## Impact

- **New project content**: `data/raw/`, `data/clean/`, `scripts/`, `out/`, `docs/`, `NOTES.md`, `summary.md` and `requirements.txt` under `projects/denver-rail/`.
- **Dependencies**: Python standard library first; `shapely` (or `geopandas`) only if the geometric check needs it. All dependencies stay inside the project folder.
- **External data**: geodata.colorado.gov (CDOT), RTD's GTFS open-data feed, Census LEHD/LODES and the tundria.com 1946 route list. Any fetch that is blocked becomes a manual download into `data/raw/`.
- **Inputs needed from the chat Project**: `docs/streetcar-corridor-scorecard.md`, exported by hand. Ridership attributes and verdicts depend on it.
- **Repository**: downloaded and cleaned data must be gitignored, because GTFS and LODES files run to tens of MB. No secrets are involved in this change.
- **Viewing**: the map page needs a network connection for its basemap tiles; the data layers are embedded in the page.
- **Staleness**: RTD changed service on 2026-09-27, and BRT and Colorado Connector dates are as reported in Sept 2026. The pipeline must use a fresh GTFS pull, and the dates must be re-checked before anything is published.

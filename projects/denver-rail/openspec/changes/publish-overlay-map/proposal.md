# Proposal

## Why

The add-gis-overlay change builds `out/map.html` as a static, self-contained page, but it leaves hosting out of scope, so the map can only be viewed from a local file. Publishing it on GitHub Pages gives a stable link to share. Once the page is public, a few things that were fine for a private research map have to be handled: basemap and data credits, a notice that the site is not affiliated with RTD, visible as-of dates, and a deliberate check before each publish so stale planned-project dates don't go live.

## What Changes

- Publish the Denver Rail map, and only that map, to GitHub Pages for the `Ml0130-Code-Base/Misc-claud-projects` repo, served from a `gh-pages` branch. Nothing is added at the repo root: no `.github/` workflow and no root `docs/` folder.
- Add a project-local `publish.ps1` that copies the committed `out/map.html` into the `gh-pages` branch as `index.html`, then commits and pushes it. Publishing happens only when someone runs the script, never automatically on a push to `main`.
- Before publishing, check that the build is current and that the "re-check before publishing" items in `summary.md` have been confirmed. If either check fails, the script stops.
- Add credits and disclosures to the map page: OpenStreetMap and CARTO attribution on the map itself, a notice that the site is unofficial and not affiliated with or endorsed by RTD, the GTFS feed dates and the LODES year, and an About panel listing every source with its as-of date.
- Use a CARTO API key for the basemap, as CARTO's free non-commercial tier now requires. The key is restricted to the Pages domain, kept out of `main`, and added only to the published copy.
- Set a size budget for the published page and round embedded coordinates, so the page loads in reasonable time on a phone.
- Document the one-time Pages setup (enable Pages with the `gh-pages` branch as its source) and how to publish in the project README.

Out of scope: publishing any other project in this repo, a custom domain, analytics, CI builds of the data pipeline (raw RTD GTFS needs a licence accepted by hand, so the pipeline stays local), and switching map libraries or basemap providers.

## Capabilities

### New Capabilities

- `site-publishing`: How the built map becomes the public Pages site: the manual publish step, the checks before publishing, the `gh-pages` branch layout, the size budget, and how the basemap key is handled.
- `map-attribution`: The credits, the RTD non-affiliation notice, and the source and as-of information that the map page shows to viewers.

### Modified Capabilities

None. The `overlay-map` and `data-provenance` capabilities are still deltas in the unarchived add-gis-overlay change, so this change adds new capabilities rather than modifying them.

## Impact

- **Depends on add-gis-overlay**: needs `scripts/map_template.html`, `scripts/build_map.py`, `out/map.html` and `summary.md` from that change (task groups 8 and 9). This change extends those files; it does not replace them.
- **New project files**: `publish.ps1`, a `tests/` case for the publish checks, and `.env.example` entries for the CARTO key. All of them live in `projects/denver-rail/`.
- **Repository**: a new orphan `gh-pages` branch that holds only the published page. GitHub Pages has to be enabled once in the repo settings, which the owner does or approves.
- **Public URL**: `https://ml0130-code-base.github.io/Misc-claud-projects/`.
- **External terms** (checked 2026-11-23):
  - RTD's GTFS licence agreement grants rights to use and redistribute the data. It forbids RTD logos and content and any suggestion that RTD endorses the site, and it lets RTD require an "unofficial site" notice.
  - The agreement's wording refers to GTFS Realtime, so it is unclear whether it covers the static feed. This is recorded as a risk and not treated as a blocker.
  - CARTO's basemap terms (dated 2026-09-29) give free non-commercial use with an API key, a limit of 5M tiles a month, and attribution on the map itself.
- **Secrets**: the CARTO key will be visible in the public page, which is unavoidable for a browser key. It is restricted to the Pages domain and never committed to `main`. It is read from a gitignored `.env`.
- **Follow-up outside this change**: decision 7 and task 8.1 of add-gis-overlay assume CARTO tiles need no key. They should be updated to point to the key handling defined here.

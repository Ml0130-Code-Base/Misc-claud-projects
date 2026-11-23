# Design

## Context

See proposal.md (Why) for the motivation, and specs/ for the behavior contract. This document covers how publishing is built on top of the add-gis-overlay pipeline.

Current state and constraints:

- **Repository:** `Ml0130-Code-Base/Misc-claud-projects` is public and owned by an organization. GitHub Pages is not enabled, and there is no `.github/` folder. Each repo gets one Pages site, so this map's URL is `https://ml0130-code-base.github.io/Misc-claud-projects/`.
- **Repo rule:** CLAUDE.md keeps tooling out of the repo root. A Pages Actions workflow has to live in the root `.github/workflows/`, so this design avoids one.
- **Pipeline:** add-gis-overlay builds the map locally with Python. The RTD GTFS download needs its licence accepted by hand in a browser, and raw and clean data are gitignored, so CI cannot rebuild the map. Publishing therefore ships the committed `out/map.html`; it never rebuilds it.
- **Inherited from add-gis-overlay:**
  - `scripts/map_template.html` and `scripts/build_map.py` (decision 7, task 8.1) produce `out/map.html`.
  - `report.py` writes `summary.md` with a "re-check before publishing" section between marker comments (task 9.2).
  - `data/raw/manifest.json` records every source (decision 8).
- **Machine:** Windows and PowerShell. Python runs through `py -3.12` or the `.venv` interpreter, never bare `python`. Git and `gh` are available.
- **External terms, checked 2026-11-23:**
  - CARTO's basemap terms (dated 2026-09-29) need an API key for free non-commercial use. Requests without a key may be watermarked. The free tier allows 5M tile requests a month, needs OSM and CARTO credits on the map itself, and forbids proxying or caching tiles on a server.
  - RTD's GTFS licence agreement allows redistribution. It forbids RTD marks and any suggestion of endorsement, and it reserves the right to require an "unofficial site" notice.

## Goals / Non-Goals

**Goals:**
- One PowerShell command, run from `projects/denver-rail/`, takes a committed map to the live site, or stops with a clear reason.
- The repo root stays unchanged.
- Every check the publish step makes can be run without pushing, through the dry run.

**Non-Goals:**
- No Pages site for other projects. If a second project needs Pages, the approach changes (see Decision 1, alternative A).
- No automatic deploys, preview deploys or branch previews.
- No server-side tile caching or proxying, which CARTO's terms forbid.
- The publish step does not rebuild the map.

## Decisions

### 1. Deploy from an orphan `gh-pages` branch, driven by a project-local script

```
 main                                   gh-pages (orphan, site only)
 +-----------------------------+        +----------------------+
 | projects/denver-rail/       |        | index.html  (+ key)  |
 |   out/map.html (placeholder)| -----> | .nojekyll            |
 |   publish.ps1               |  run   +----------+-----------+
 |   .env  (gitignored, key)   |                   |
 +-----------------------------+                   v
                                        GitHub Pages (source: gh-pages, /)
```

`publish.ps1` lives in `projects/denver-rail/`. It works in a temporary `git worktree` of `gh-pages`, so the owner's checkout is never switched or disturbed. It removes the worktree afterwards, whether the publish succeeded or not. On the first run, if `gh-pages` doesn't exist yet, it creates it as an orphan branch.

Each publish is one new commit on `gh-pages`. Its message carries the main-branch commit id of the map. Earlier publishes stay in the branch history, which is how rollback works (see Migration Plan).

*Alternatives considered:*
- **A. A GitHub Actions workflow** that uploads the map as a Pages artifact. This is the cleaner option when several projects publish, but it needs `.github/workflows/` at the repo root, which breaks the repo rule. It also can't build the map either, so it adds little for one project.
- **B. A root `docs/` folder deployed from `main`.** This also breaks the repo rule. And deploying from the root of `main` would publish every project's files.
- **C. A separate repo just for the map.** That means a second repo to keep in sync for a single file.

### 2. The publish step runs its checks in a fixed order

`publish.ps1` runs these steps in order. It stops at the first failure and changes nothing until step 8.

1. **Clean map.** `git status --porcelain out/map.html` is empty, so the working copy matches `HEAD`. The id of the last commit that touched `out/map.html` becomes the "source commit" shown to the owner.
2. **Re-check confirmed.** Read the confirmation line in `summary.md` (Decision 3) and compare its date with the build date embedded in the map (Decision 6).
3. **Key present.** `CARTO_API_KEY` is set in `projects/denver-rail/.env`.
4. **Assemble.** Copy the map to a temporary `index.html` and replace the key placeholder (Decision 4). Fail if the placeholder is missing or appears more than once.
5. **Size.** The assembled `index.html` is 5 MB or smaller.
6. **Stop here for a dry run.** `-DryRun` reports every check result, the page size and the temporary path, then ends without committing or pushing.
7. **Show and confirm.** Print the source commit, page size and target URL, then ask y/N. Anything other than `y` ends the run without pushing.
8. **Commit and push.** Commit to `gh-pages` in the worktree, push `origin gh-pages`, and append the `NOTES.md` entry.

The check logic lives in a small Python module, `scripts/publish_checks.py`, so it can be unit-tested with `unittest` like the rest of the pipeline. `publish.ps1` only handles git, the prompt and the push.

*Alternative considered:* writing every check in PowerShell. That was rejected because the project's tests are Python `unittest`, and parsing dates and markers is easier to test in Python.

### 3. The re-check confirmation lives in `summary.md`, outside the generated markers

The "re-check before publishing" list is generated between markers, as in add-gis-overlay task 9.2. The owner confirms the check by hand-editing one line placed after the generated block, outside the markers:

```
Re-checked: 2026-12-01
```

`report.py` regenerates only what is inside the markers, so the confirmation survives rebuilds. A rebuild still invalidates it in effect, because the map's build date moves past the confirmation date.

*Alternative considered:* a flag such as `-IConfirmDatesChecked`. It was rejected because a flag leaves no record, while a dated line in `summary.md` is committed and can be reviewed.

### 4. The basemap key uses a placeholder on `main` and is substituted at publish time

- `map_template.html` builds the CARTO tile URL with the literal token `__CARTO_API_KEY__`. `build_map.py` always writes that token, never a real key. The token is held in one key constant that both the base and labels tile layers use, so it appears exactly once in the page. add-gis-overlay decision 7 and task 8.1 put this in place. This keeps the key out of `main`, which follows the repo's "never commit secrets" rule. The key is not truly secret, since it is visible in the browser and restricted by domain, but it still stays out of history.
- `publish.ps1` reads `CARTO_API_KEY` from `projects/denver-rail/.env`, using the same format as `.env.example`, and replaces the token only in the assembled `index.html`.
- In the CARTO dashboard, the key is restricted to `ml0130-code-base.github.io`.
- When the map is opened locally, tile requests go out with the unreplaced token. CARTO may refuse them or add a watermark. The overlay-map requirement "Basemap unavailable" from add-gis-overlay already covers this: the data layers still render on a plain background.

*Alternatives considered:*
- **Writing the key into `out/map.html` during the local build.** This puts the key into `main`'s history.
- **A keyless basemap** (OpenFreeMap or plain OSM tiles). OpenFreeMap means moving to a vector map library. OSM's standard tiles look busier and come with their own usage policy. Both reopen add-gis-overlay decision 7, so they stay out of this change.

### 5. Disclosures are part of the map template, not added at publish time

The credit, the unofficial notice and the About panel are written into `map_template.html` and filled in by `build_map.py`. That way the local map and the published page are the same apart from the key, which satisfies the "Disclosures in every build" requirement.

- **Credit:** Leaflet's attribution control in the bottom-right corner, with this text: `© OpenStreetMap contributors, © CARTO`, linking to `https://www.openstreetmap.org/copyright` and `https://carto.com/attribution/`. The legend docks top-left at 375 px, so it never covers the credit.
- **Unofficial notice:** a one-line strip that is always visible, for example "Unofficial research map, not affiliated with or endorsed by RTD.", with an "About" link that opens the panel.
- **About panel:** built from `data/raw/manifest.json` (source URLs and retrieval dates), the GTFS `feed_info` and service dates, the LODES year, the scorecard date, and the `as_of` values from `planned.csv`. All of these are already recorded by add-gis-overlay decision 8, so nothing new has to be collected.
- No RTD logos are used. Rail lines use RTD's GTFS `route_color` values, which are data, not branding.

### 6. The build date and coordinate rounding are added in `build_map.py`

- `build_map.py` writes a build date into the page, both as a `<meta name="build-date">` tag and in the About panel. The publish check reads it from the meta tag.
- Every coordinate is rounded to 5 decimal places (about 1 m) as layers are embedded. Rounding happens only in the page output; `data/clean/` keeps full precision. Rounding can collapse consecutive points to the same value, and those duplicates are dropped.
- `build_map.py` prints the page size, so a page over budget shows up at build time and not first at publish.

*Alternative considered:* geometry simplification (Douglas–Peucker). It was held back because rounding alone may bring the page within budget. If it doesn't, simplification can be added later in `build_map.py` without any spec change.

### 7. A one-time Pages setup, done by the owner

After the first publish creates `gh-pages`, Pages is switched on with source `gh-pages` and folder `/`. The owner can do this in the repo's Settings → Pages, or with:

```powershell
gh api -X POST repos/Ml0130-Code-Base/Misc-claud-projects/pages -f "source[branch]=gh-pages" -f "source[path]=/"
```

This is a repo settings change, so the owner runs it or approves it. It is documented in the README and is never run by `publish.ps1`.

## Risks / Trade-offs

- **[RTD's agreement is titled for GTFS Realtime, so it may not clearly cover the static feed]** → The notice and the no-branding rules are applied anyway. RTD can be asked by email for confirmation that a non-commercial derived map is fine. The open question is recorded in `NOTES.md`, and it doesn't block publishing.
- **[CARTO's terms could change, or the free tier could be revoked without notice]** → The data layers still render on a plain background. Switching providers is a separate change to add-gis-overlay decision 7.
- **[CARTO's older GitHub LICENSE.md says tiles are for enterprise customers only, which conflicts with the 2026-09-29 terms]** → This design follows the dated terms. If CARTO says otherwise, fall back to the alternatives in Decision 4.
- **[The CARTO key is visible to anyone who views the page]** → That's unavoidable for a browser key. Restricting it to the Pages domain limits misuse, and the key can be rotated in the CARTO dashboard and republished.
- **[Pages propagation takes a few minutes]** → The script prints the URL and says the change may take a few minutes to appear. It doesn't poll.
- **[An orphan branch is unfamiliar and easy to delete by mistake]** → The README explains it. Deleting the branch only takes the site down, and the next publish recreates it.
- **[The page could stay over 5 MB even after rounding]** → Commute pairs are capped at 100 and bus routes are one feature each, so the likely cause would be GTFS shapes. Simplification is the planned fallback (Decision 6).
- **[The confirmation line could be added without the checks really being done]** → This is a process risk, not a technical one. The dated line is committed, so it can be reviewed.

## Migration Plan

1. Finish add-gis-overlay through task group 9, so the map, summary and manifest exist.
2. Build with the disclosures, then commit `out/map.html` and `summary.md` with the `Re-checked:` line.
3. Run `.\publish.ps1 -DryRun` and fix any failed checks.
4. Run `.\publish.ps1` to create `gh-pages` and push it.
5. Enable Pages once (Decision 7), then open the URL to confirm the site loads.

**Rollback:** check out the previous `gh-pages` commit into a worktree and push it, or run `git revert` on `gh-pages`. To take the site down entirely, disable Pages in the repo settings.

## Open Questions

- Whether to ask RTD by email for written confirmation about the static feed's licence scope. Publishing doesn't wait on this.
- The exact wording of the unofficial notice and the About panel's purpose statement. This is settled while writing the template, within the spec.

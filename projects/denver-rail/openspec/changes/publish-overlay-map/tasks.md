# Tasks

Paths are relative to `projects/denver-rail/`. This change starts after add-gis-overlay task groups 8 and 9 are done, because it extends `scripts/map_template.html`, `scripts/build_map.py`, `scripts/report.py` and `summary.md`. Tests use the standard-library `unittest` and run with `.\.venv\Scripts\python.exe -I -m unittest discover -s tests`. Fixtures are small synthetic files under `tests/fixtures/`.

## 1. Map build changes

- [ ] 1.1 Confirm that the `__CARTO_API_KEY__` placeholder from add-gis-overlay task 8.1 is in place, and extend its unit test so the built page has the token exactly once (one key constant shared by the base and labels tile layers) and contains no `.env` value; verify by running the test
- [ ] 1.2 Round every embedded coordinate to 5 decimal places in `build_map.py` and drop consecutive duplicate points created by rounding, leaving `data/clean/` at full precision; verify with unit tests that no embedded coordinate has more than 5 decimals and that a line whose points collapse keeps at least 2 points
- [ ] 1.3 Write a `<meta name="build-date">` tag into the page, and make `build_map.py` print the page size after building; verify with a unit test that the meta tag holds the run date in ISO format
- [ ] 1.4 Add `CARTO_API_KEY=` to `.env.example` and confirm `.env` is gitignored at the project or root level; verify that `git check-ignore .env` prints the path

## 2. Disclosures on the map

- [ ] 2.1 Add the attribution control with `© OpenStreetMap contributors, © CARTO`, linking to `https://www.openstreetmap.org/copyright` and `https://carto.com/attribution/`; verify in the browser that the credit is visible on load at desktop width and at 375 px, with the legend expanded and collapsed
- [ ] 2.2 Add the always-visible notice saying the map is unofficial and not affiliated with or endorsed by RTD, with an "About" link; verify in the browser that it is visible on load at both widths and causes no horizontal scroll at 375 px
- [ ] 2.3 Build the About panel from `data/raw/manifest.json`, the GTFS service dates, the LODES year, the scorecard date and the `planned.csv` `as_of` values, plus the purpose statement; verify with a unit test on fixture inputs that every source appears with a link and a date, and in the browser that the panel opens and closes at both widths
- [ ] 2.4 Check that the page embeds no RTD logo or image from RTD's site; verify by listing every `<img>`, `url(` and `data:` reference in the built page and confirming none comes from RTD
- [ ] 2.5 Open the built map from disk with tiles blocked; verify that the credit, the notice and the About panel all still appear, along with every data layer

## 3. Publish checks

- [ ] 3.1 Add a `Re-checked: YYYY-MM-DD` line outside the generated markers in `summary.md`, and make sure `report.py` leaves it alone; verify with a unit test that regenerating the summary keeps the line unchanged
- [ ] 3.2 Write `scripts/publish_checks.py` with these checks: re-check date on or after the map's build date, key placeholder present exactly once, key substitution, and size of 5 MB or less. Each check returns a pass/fail result with a message; verify with unit tests covering each pass and failure case (no `Re-checked` line, a date before the build date, a missing or duplicated placeholder, an empty key, and an oversized page)
- [ ] 3.3 Give `publish_checks.py` an `assemble` entry point that writes `index.html` (with the key substituted) and `.nojekyll` to a given folder; verify with a unit test that the folder holds only those two files and that `index.html` contains the key and no placeholder

## 4. Publish script

- [ ] 4.1 Write `publish.ps1`. It checks that `out/map.html` has no uncommitted changes, reads `CARTO_API_KEY` from `.env`, calls `publish_checks.py` to check and assemble into a temporary folder, and supports `-DryRun`; verify that a dry run on a clean, confirmed build reports every check and the temp path, and that `git status` and `git ls-remote origin gh-pages` are unchanged afterwards
- [ ] 4.2 Make `publish.ps1` stop with a clear message when the map has uncommitted changes, when the re-check is missing or stale, when the key is missing, and when the page is over budget; verify by causing each condition in turn and running `-DryRun`
- [ ] 4.3 Add the publish path: a temporary `git worktree` of `gh-pages` (created as an orphan branch if it does not exist), the y/N confirmation showing the source commit, page size and URL, a commit whose message includes the source commit, the push, removal of the worktree on success or failure, and a dated `NOTES.md` entry; verify that answering `n` pushes nothing, and that after a real run `git ls-tree origin/gh-pages` lists only `index.html` and `.nojekyll`
- [ ] 4.4 Document in the README the publish flow (confirming the re-check, setting up `.env`, dry run, publish), the one-time Pages setup command, restricting the CARTO key to `ml0130-code-base.github.io`, and how to roll back; verify that every command runs as written in PowerShell

## 5. Go live

- [ ] 5.1 The owner registers for a CARTO key, restricts it to `ml0130-code-base.github.io` and puts it in `.env`; verify that `publish.ps1 -DryRun` passes the key check
- [ ] 5.2 Run the first real publish; verify that `origin/gh-pages` exists and its latest commit message names the main commit of the map
- [ ] 5.3 The owner enables Pages (source `gh-pages`, `/`) in the repo settings or with the command from design decision 7; verify that `gh api repos/Ml0130-Code-Base/Misc-claud-projects/pages` reports the `gh-pages` source
- [ ] 5.4 Open `https://ml0130-code-base.github.io/Misc-claud-projects/` at desktop width and at 375 px; verify that the basemap tiles load without a watermark, every layer toggle works, and the credit, the notice and the About dates match the published build
- [ ] 5.5 Record in `NOTES.md` the open question about whether RTD's licence covers the static feed and whether to email RTD; verify that the entry is present

## Workflow follow-up

- Update the denver-rail row in the root `README.md` Projects table with the live URL once the site is up.
- Archive this change after add-gis-overlay is archived, so that `overlay-map` exists in the main specs first.

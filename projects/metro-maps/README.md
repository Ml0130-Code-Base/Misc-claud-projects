# Metro Maps

Snapshot MetroDreamin fantasy transit maps to disk and analyze them offline (station spacing, orphans, near-duplicates, placeholder names, coverage gaps) into exact, copy-pasteable edit punch lists. In scope: Denver Metro Fantasy Rail Map (#1) and San Diego County Transit Fantasy (#14). Planning is tracked with OpenSpec in `openspec/` (run `openspec` commands from this folder).

## Setup

```powershell
# TBD: runtime not chosen yet (Python not installed on this machine)
```

## Run

```powershell
# TBD
```

## Notes

- Map ID = base64 of `<userId>|<mapIndex>`; fetch `https://metrodreamin.com/view/<id>` with `=` encoded as `%3D`, then parse `<script id="__NEXT_DATA__">` -> `props.pageProps.fullSystem.map.{stations,lines}`.
- Filter `isWaypoint` objects before any spacing or duplicate analysis.

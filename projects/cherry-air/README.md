# Cherry Air (CHY)

Schedule and dispatch system for Cherry Air, a VATSIM virtual airline: moving the route/flight-number master out of the v6 spreadsheet into a small self-hosted app without changing a single flight number.

Read [CLAUDE.md](CLAUDE.md) first — it is the authoritative handoff (numbering, allocator, callsigns, route doctrine).

## Layout

```
CLAUDE.md                 # authoritative v6 handoff + explore-mode decisions
data/source/              # read-only seed drop (v6 workbook, routes CSV, ledger)
apps-script/              # v6.1 Google Sheets allocator (reference for the port)
openspec/                 # OpenSpec root for this project (specs + changes)
```

## Setup

```powershell
# not decided yet: Python via uv on the desktop is the proposed dev setup
```

## Run

```powershell
# no app yet
```

## Notes

- Run `openspec` commands from this folder — the OpenSpec root is per-project, not at the repo root.
- `data/source/` is input only; never edit it in place.

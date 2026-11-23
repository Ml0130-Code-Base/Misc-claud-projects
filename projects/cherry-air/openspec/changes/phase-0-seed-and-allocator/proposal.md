# Proposal

## Why

Cherry Air's flight numbers live in a spreadsheet: values frozen in the v6 workbook, plus a Google Apps Script allocator. Every earlier numbering mechanism (RANDBETWEEN, then positional formulas) renumbered routes when rows moved. One retired number, CHY118, was already reissued before v6 froze. Before the app can replace the sheet, it has to own the numbering with the same v6 guarantees. It must also prove, number for number, that it imported the network without changing anything.

## What Changes

- New SQLite-backed route registry seeded from `data/source/routes_v6.csv` and `data/source/ledger_v6.json`: 147 active routes (7 hub connectors, 114 spokes, 26 thrus) and 294 ledger numbers, imported exactly with no renumbering. Running the import twice produces an identical database.
- The import cross-checks the CSV against the v6 workbook's route sheets (`HubFlights`, `Flights`, `Thru Flights`). If any pairing or FLT # disagrees, the import refuses to run.
- Pre-v6 history (the "was X/Y" route notes and the workbook's `Change Log` sheet) is imported as historical text only, never as numbering input.
- A port of the v6 allocator becomes the only way a flight number is assigned. It takes the lowest free even pair in the origin hub's block (1–99 for hub connectors), skipping any number live or in the ledger, and writes both numbers to the ledger in the same transaction.
- Retiring a route is a status change. Its numbers stay in the ledger and are never reissued.
- Route authority as code: a route is added or retired only by approving a pending route-change proposal. Nothing else mutates routes.
- The golden tests from the handoff (CLAUDE.md §11, tests 1, 2, 3 and 5), plus the allocator simulation (next KVGT spoke 1130/1129, next KTVC thru 3122/3121, next connector 16/15), become the acceptance gate for this phase.
- **Not in this change:** callsigns and dispatch, the lookup page and HTTP endpoints, SERVICE_TYPE tagging, the day-pattern schedule layer, xlsx export, auth, and Docker/Caddy deployment. No route is added, retired or renumbered as part of this change; the network after import is exactly v6.

## Capabilities

### New Capabilities
- `flight-numbering`: the hub-number scheme (spoke/thru/connector blocks, even outbound with return = outbound − 1, hub decode), the permanent ledger, and the allocator that assigns new pairs.
- `route-registry`: the stored network of routes (kind, origin/stop/dest, numbers, status, notes), how it is seeded from the v6 export with parity checks, and how routes are retired.
- `route-change-approval`: the gate that turns route additions and retirements into pending proposals that change the registry only once explicitly approved.

### Modified Capabilities
- None. This is the project's first change.

## Impact

- New code under `projects/cherry-air/`: a Python package (domain logic, SQLite schema, importer) and a pytest suite. No HTTP server yet.
- New dependencies (project-local): Python 3.12+, pytest, and openpyxl (read-only, for the workbook cross-check and Change Log import). Managed with uv. This is the proposed default for the desktop dev setup, which isn't decided yet. The desktop currently has no Python installed.
- New local file `data/cherry.db` (gitignored). `data/source/` is read only.
- The spreadsheet stays the source of truth. This change produces the parity evidence for a later cutover; it does not perform one.

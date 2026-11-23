# Design

## Context

See proposal.md (Why) for motivation, and the three specs for the required behavior.

- **Starting point:** the project folder holds the v6 seed data, the v6.1 Apps Script allocator (`apps-script/CherryAllocator.gs`, reference only) and CLAUDE.md. There is no code yet.
- **Seed data (verified during planning):**
  - `routes_v6.csv`: 147 rows, 8 comma-separated columns with no quoting (`kind,origin,stop,dest,out,ret,hub,notes`).
  - Every row is even outbound with return = outbound − 1.
  - `ledger_v6.json` equals the 294 live numbers exactly.
  - The workbook's `HubFlights`, `Flights` and `Thru Flights` FLT # columns hold exactly the CSV's outbound numbers per kind. Retired routes are not rows in those sheets.
- **Next free pairs** from the seed data, by the v6 rule: connector 16/15, KTVC spoke 138/137, KTVC thru 3122/3121, KVGT spoke 1130/1129. This matches the handoff's allocator simulation.
- **Desktop:** Windows 11, with no Python, Node, Docker or WSL installed today. The server is not yet identified.

## Goals / Non-Goals

**Goals:**
- A small Python package whose domain rules (blocks, decode, allocation, approval) are pure and fully tested. SQLite enforces the invariants a second time, so a bug in Python cannot renumber or reissue.
- One command seeds `data/cherry.db` from `data/source/` and fails loudly on any parity problem.
- The test suite runs in seconds on the desktop with no services.

**Non-Goals:**
- No HTTP layer, FastAPI app, UI or auth. This phase exposes a Python API plus a small CLI, and FastAPI arrives with the dispatch phase.
- No Docker or Caddy files. Nothing here needs a server.
- No porting of the sheet's derived helpers (Registry, NextFree, ThruSeg). They are views that later phases rebuild from the database.

## Decisions

### D1. Python 3.12 + uv, src layout, pytest
`projects/cherry-air/pyproject.toml`, package `src/cherry/`, tests in `tests/`. Dependencies: `openpyxl` at runtime (read-only workbook access), `pytest` for development. Python and the lockfile are managed by uv, so the desktop needs one install (uv) and nothing system-wide.
- *Alternative: Node.* It would add a second ecosystem for no gain. The later API is FastAPI, so Python now avoids a rewrite.
- *Alternative: Docker Desktop for development.* It needs WSL2, a VM and gigabytes of downloads to run pure SQLite logic. Containers stay a server concern.
- **Assumption awaiting your confirmation:** this is the desktop dev setup. If you choose Docker or server-only instead, only task group 1 changes.

### D2. Module boundaries
- `hubs.py`: the hub table (N, ICAO, region, spoke letter, thru letter), block math and number decode. Pure functions with no I/O.
- `db.py` + `schema.sql`: connection setup (WAL, foreign keys, busy timeout) and schema creation.
- `allocator.py`: `next_pair(conn, kind, origin)`. It reads the used set and scans the block. It must run inside the caller's write transaction.
- `registry.py`: read queries and validation (ICAO shape, thru stop, duplicates). It has no public write functions.
- `proposals.py`: submit, preview, approve and reject. Approve is the only code path that inserts or retires a route.
- `seed.py`: validates the CSV, ledger and workbook, then writes everything in one transaction.
- `__main__.py`: CLI (`python -m cherry seed`, `python -m cherry check`).

The callsign module from the original sketch is deliberately left out of this phase.

### D3. Schema (SQLite)
- `hubs(n PK, icao UNIQUE, region, spoke_letter, thru_letter)`: seeded from `hubs.py`.
- `routes(id PK, kind CHECK IN ('HUB','SPOKE','THRU'), origin, stop NULL, dest, out_no UNIQUE, ret_no UNIQUE, status CHECK IN ('active','retired'), source CHECK IN ('seed-v6','proposal'), created_at, retired_at NULL, notes)`.
  - CHECK constraints: `out_no % 2 = 0`, `ret_no = out_no - 1`, and `stop` set if and only if kind is THRU.
- `ledger(no PK, route_id FK, source, assigned_at)`.
- `proposals(id PK, op CHECK IN ('ADD','RETIRE'), payload JSON, status CHECK IN ('pending','approved','rejected'), submitted_by, submitted_at, decided_by, decided_at, reason, last_error, route_id NULL)`.
- `change_log(id PK, era CHECK IN ('pre-v6','post-v6'), at, text, proposal_id NULL, route_id NULL, numbers NULL)`.
- `meta(key PK, value)`: holds the seed fingerprint.

**Triggers enforce the permanence rules inside the database**, so no code path can bypass them:
- `BEFORE DELETE ON ledger` raises an error, and so does `BEFORE UPDATE ON ledger`.
- `BEFORE DELETE ON routes` raises an error.
- `BEFORE UPDATE OF out_no, ret_no, kind, origin, stop, dest ON routes` raises an error.
- `BEFORE UPDATE OF status ON routes` raises an error unless the change is active to retired.

**Duplicate rule as partial unique indexes:**
- `(kind, origin, IFNULL(stop,''), dest) WHERE status='active'`
- For connectors: `(MIN(origin,dest), MAX(origin,dest)) WHERE kind='HUB' AND status='active'`

*Alternative: checks only in Python.* Rejected, because the specs promise that numbers are never changed or reissued, and the database is the last line of defense.

### D4. Allocator = lowest free pair inside `BEGIN IMMEDIATE`
The used set is the union of the ledger and all route numbers (the ledger already contains every route number; the union is defensive). Scan `lo+2, lo+4, …` up to the block's top and take the first `c` where neither `c` nor `c−1` is used. The caller (approve) holds a `BEGIN IMMEDIATE` transaction, so SQLite's reserved lock serializes concurrent approvals, and `busy_timeout` makes the second writer wait instead of failing. This is the same semantics as `CherryAllocator.gs` with `RECYCLE=false`, and LockService maps to the SQLite write lock.
- *Alternative: max + 2.* Rejected, because it diverges from v6 (it skips gaps that are legitimately free) and would break the 1130/1129 and 16/15 expectations.

### D5. Seeding: validate everything, then write once
1. Parse the CSV and JSON.
2. Read the workbook route sheets with openpyxl (`read_only=True`, `data_only=True`, since the FLT # cells are frozen values).
3. Run every check in the route-registry spec and collect all violations.
4. If there are any violations, exit non-zero, print the list, and write nothing.

Otherwise, in one transaction, insert the hubs, the routes (`source='seed-v6'`, `created_at` set to the fixed seed timestamp `2026-11-23T00:00:00Z` so two seeds are identical), the ledger and the pre-v6 change log. Then store the SHA-256 of the three source files in `meta`.

**Idempotence:**
- An empty database gets seeded.
- A database whose fingerprint matches and that has no `source='proposal'` routes and no post-v6 log reports "already seeded" and does nothing.
- Anything else is refused.

**Workbook parsing:** column positions follow CLAUDE.md §9. Pairings in `Flights` and `HubFlights` column B are split on `-`. Sheet headers ("Orgin") are ignored; only the column positions are used. A data row is one whose FLT # cell is numeric.

### D6. Pre-v6 history
Each CSV note is stored verbatim in `routes.notes`. The workbook's `Change Log` rows are joined cell by cell with ` | ` and stored as `change_log` rows with `era='pre-v6'` and no route or number links. Nothing parses numbers out of these strings.

### D7. Testing strategy
- **Unit tests** for `hubs.py`: every block boundary and the decode round-trip for all eight hubs.
- **A golden suite** against a freshly seeded temporary database (pytest `tmp_path`, never `data/cherry.db`):
  - uniqueness, pair shape and block bounds
  - seed equals CSV, the seed spot checks, and seeding twice
  - the allocator simulation (1130/1129, 3122/3121, 16/15)
  - retire then add (no reissue)
  - concurrent approval: two threads with separate connections each approve a KBJC proposal
- **Trigger tests:** raw SQL attempts to delete or renumber are refused by the database.
- **A seed-failure test:** a copied CSV with one corrupted number must leave the database empty.

## Risks / Trade-offs

- **[The workbook layout drifts from CLAUDE.md §9's column map]** → The cross-check fails loudly with row references. It never guesses. The fix is a mapping update, not a data change.
- **[openpyxl reads cached values, and a recalculated Google export could differ]** → The cross-check compares only FLT # values and pairings, which are static values in v6. A mismatch blocks seeding instead of silently picking one side.
- **[Partial indexes with `MIN()`/`MAX()` need a deterministic expression]** → SQLite allows multi-argument `min`/`max` in index expressions. A test checks that the reverse-connector rejection really fires.
- **[Proposals have no auth yet, so anyone with database access can approve]** → This is acceptable for a desktop-only phase. The approver's name is required and logged. Auth arrives with the HTTP layer.
- **[Preview pairs can mislead if several additions are pending]** → The spec says previews reserve nothing, and approval reports the actual pair.

## Migration Plan

There is no cutover in this phase. Everything runs on the desktop:
1. Install uv.
2. Run `uv sync`.
3. Run `uv run python -m cherry seed`.
4. Run `uv run pytest`.

The spreadsheet stays the source of truth. Rolling back means deleting `data/cherry.db`. The server is untouched.

## Open Questions

- **Server identity and hosting details:** needed only for a later deploy phase.
- **Whether Change Log rows need column structure** (date, item, before, after) rather than joined text: storing the raw text keeps the option open.

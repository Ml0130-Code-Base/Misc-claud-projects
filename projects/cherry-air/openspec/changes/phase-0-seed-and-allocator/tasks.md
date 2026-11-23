# Tasks

> Group 1 assumes design D1 (Python via uv on the Windows desktop). Confirm D1 before applying. If it changes, only group 1 changes.

## 1. Project scaffolding (desktop)

- [ ] 1.1 Confirm uv is installed on the desktop (`winget install --id=astral-sh.uv -e`, which the user runs) and verify `uv --version` prints a version in PowerShell
- [ ] 1.2 Create `pyproject.toml` (Python >=3.12, package `cherry` in `src/`, runtime dep `openpyxl`, dev dep `pytest`), `src/cherry/__init__.py` and an empty `tests/`; verify `uv sync` succeeds and `uv run pytest` reports "no tests ran" without errors
- [ ] 1.3 Add `data/cherry.db*` and `.venv/` handling to a project-local `.gitignore` (nothing at the repo root); verify `git status` does not list `data/cherry.db` after creating an empty one
- [ ] 1.4 Fill README Setup with the uv steps (PowerShell, desktop only); verify the commands run as written from `projects/cherry-air`

## 2. Hub numbering rules

- [ ] 2.1 Implement `src/cherry/hubs.py`: the hub table (N 1–8, ICAO, region, spoke/thru letters per CLAUDE.md §3), spoke/thru/connector block bounds, rejection of reserved hubs 9–14, and decode of a number to (kind, hub); verify with `tests/test_hubs.py` covering every hub's block edges, the thru mirror rule (+3000), and the spec scenarios (1128 → KVGT spoke, 4361 → KLMT thru, 15 → connector, hub 9 rejected)
- [ ] 2.2 Add a round-trip test: for every even number in every block, decode returns the hub whose block contains it; verify it passes

## 3. Schema and database guards

- [ ] 3.1 Write `src/cherry/schema.sql` with the tables, CHECK constraints and partial unique indexes from design D3, and `src/cherry/db.py` (open a connection with WAL, foreign_keys, busy_timeout; create the schema if missing); verify `tests/test_schema.py` creates a fresh database in `tmp_path` and lists every expected table and index
- [ ] 3.2 Add the triggers from D3 (ledger has no delete or update; routes have no delete; numbers and airports can't be updated; status can only go active → retired); verify trigger tests where raw SQL DELETE or UPDATE attempts fail with an error and leave rows unchanged
- [ ] 3.3 Verify the CHECK and index guards with tests: odd outbound rejected, ret ≠ out−1 rejected, THRU without stop rejected, duplicate active spoke rejected, reverse connector (KVGT–KTVC vs KTVC–KVGT) rejected, retired duplicate allowed

## 4. Registry reads and validation

- [ ] 4.1 Implement `src/cherry/registry.py`: list routes filtered by kind, base hub and status; find a route by its outbound or return number; validate a candidate route (4-char uppercase ICAO, thru stop present and distinct, origin is a hub for SPOKE/THRU, both ends hubs for HUB, no active duplicate). It exposes no write functions. Verify `tests/test_registry.py` covers each route-registry scenario that doesn't need seeding, including "KEG" rejected and a KSGF-origin spoke rejected

## 5. Seed from v6

- [ ] 5.1 Implement CSV and ledger parsing plus whole-dataset validation in `src/cherry/seed.py` (uniqueness across out+ret, pair shape, block bounds per kind/origin hub, every number in the ledger), collecting all violations; verify a test with a copied CSV containing a duplicate outbound number reports it and leaves the database empty
- [ ] 5.2 Implement the workbook cross-check (openpyxl read-only, data_only; column map per CLAUDE.md §9; data rows = numeric FLT #) comparing kind, airports, outbound and return with the CSV; verify that against the shipped files it reports 7/114/26 matches and zero mismatches, and that a test with one CSV number altered refuses to seed and names the route
- [ ] 5.3 Implement the single-transaction write (hubs, routes as `seed-v6` with the fixed seed timestamp, ledger, pre-v6 Change Log rows verbatim, source fingerprint in `meta`) and the idempotence rules from D5; verify tests: seeded counts are 147 (7/114/26) and 294; two fresh seeds produce identical route and ledger dumps; re-seeding the same database reports "already seeded" with no changes; a database with a proposal-created route refuses to seed
- [ ] 5.4 Add the seed spot-check test (KVGT–KVNY 1128/1127, KBJC–KSTP 514/513, KTVC–KDLH 108/107, KTVC–KDLH–KGFK 3106/3105, KTVC–KSTP–KMOT 3112/3111, KVGT–KSBP–KMRY 4102/4101) and the "was 454/453 is text only" test; verify both pass
- [ ] 5.5 Add the CLI `python -m cherry seed [--db PATH]` and `python -m cherry check` (re-runs all validations against an existing database, exit 0/1); document both in README Run; verify `uv run python -m cherry seed` creates `data/cherry.db` and a second run prints "already seeded"

## 6. Allocator

- [ ] 6.1 Implement `src/cherry/allocator.py` per design D4 (used set = ledger ∪ route numbers; lowest even c from block start + 2 with c and c−1 free; "block full" error naming the block; must be called inside a write transaction). Verify against a seeded `tmp_path` database that the next pairs are KVGT spoke 1130/1129, KTVC thru 3122/3121 and connector 16/15
- [ ] 6.2 Add a block-full test using a small synthetic database whose KLUK spoke block is fully in the ledger; verify allocation fails with the block named and the ledger unchanged

## 7. Route-change approval

- [ ] 7.1 Implement submit and preview in `src/cherry/proposals.py`: ADD (kind, airports, notes; any supplied number is rejected) and RETIRE (existing active route by number; unknown number rejected at submission); the preview shows the would-be pair and reserves nothing. Verify tests: submitting leaves routes and ledger unchanged; two pending KVGT ADDs both preview 1130/1129
- [ ] 7.2 Implement approve (approver name required; `BEGIN IMMEDIATE`; validate, then allocate and insert for ADD or retire for RETIRE; ledger rows and a post-v6 change_log entry in the same transaction; on invalidity, roll back and keep the proposal pending with `last_error`) and reject (reason, decider, time; no effect); decisions are final. Verify tests for every route-change-approval scenario, including the second pending KVGT ADD receiving 1132/1131 after the first is approved
- [ ] 7.3 Add the no-reissue test (retire a KVGT spoke via proposal, approve a new KVGT spoke, check it gets the next free pair and the retired pair stays in the ledger and on the retired route) and the immutability test (no public function writes routes except seed and approve; asserted by inspecting the `cherry` package's public API); verify both pass
- [ ] 7.4 Add the concurrency test: two threads, each with its own connection to the same file database, approve one KBJC ADD each at the same time; verify they get different pairs, both are in the ledger, and neither fails
- [ ] 7.5 Document the proposal workflow (submit, preview, approve, reject) with a short PowerShell example using `uv run python -c ...` in README Notes; verify the example runs against a seeded scratch database

## 8. Phase 0 parity gate

- [ ] 8.1 Run `uv run pytest` and `uv run python -m cherry check` against a freshly seeded `data/cherry.db`; verify everything passes and record the result (test count, check output) in CLAUDE.md §12 as "Phase 0 parity: passed on <date>"

## Workflow follow-up

- Michael reviews the parity evidence before any cutover decision; the spreadsheet remains the source of truth until then.
- Archive the change once reviewed.

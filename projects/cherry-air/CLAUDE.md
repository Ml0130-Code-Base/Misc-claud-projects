# Cherry Air (CHY) — Claude Code Handoff

Handoff from the claude.ai spreadsheet phase (Aug 2026, CCVA project) into code. Read this whole file before touching data. Owner: **Michael LaRosh** (founder/management). He prefers complete, deployment-ready systems; lightweight stack (Docker Compose, Caddy, FastAPI, SQLite, vanilla JS/Tailwind); copy-pasteable commands; and for any implementation reply the order **Goal → Architecture → Files → Run → Verify → Upgrades**. When work spans machines, state explicitly what happens on the desktop vs. the server.

---

## 0. Standing rules (non-negotiable)

1. **No route changes without Michael's explicit approval.** Recommendations and implementation are separate steps. Produce suggestions, wait for sign-off, then apply.
2. **FLT # is never user-defined.** It is assigned by the system from the route's hub. Humans type pairings only.
3. **A flight number, once assigned, is permanent and never reissued** — not after deletion, re-sorting, or edits elsewhere. Adding or removing a route must never change any other route's number.
4. **ATC is weather.** Nothing is ever planned around VATSIM controller staffing — no event routes, no "flyable now" logic, no staffing-aware features.
5. **Every callsign Cherry emits is VATSIM-legal**: `CHY` + at most 4 characters, digits first, at most one letter, letter only at the end.

> ⚠️ **Superseded rule — ignore it if you see it elsewhere.** Older notes (project memory, the ops-strategy handoff doc) say "flight numbers are positional; append new routes at the bottom of a hub block; never insert mid-block." That was the v5 formula model. **v6 replaced it with an allocator** (§4). Rows can now be added, deleted, or alphabetized freely. The append-only rule is retired.

---

## 1. Identity

Virtual airline on VATSIM. HQ **KTVC** (Cherry Capital, Traverse City MI). Corporate charter + scheduled operator flying from **corporate/reliever fields instead of airline hubs** — the founding pattern is `KDEN>KBJC`, `KMSP>KSTP`, `KSAN>KMYF` ("not here > but here").

Hybrid identity by *cities served* (not economics/regulatory simulation) — from the ops-strategy chat:

| SERVICE_TYPE | DNA | Meaning |
|---|---|---|
| SHUTTLE | JSX | Scheduled metro-to-metro between reliever fields |
| COMM | EAS commuters (Key Lime/DAC, Contour) | Thin small-community service; real federal EAS anchors already in network: KEAU, KMKG, KPUB, KSUX |
| CORP | NetJets | Resort / corporate destinations (KEGE, KHDN, KSBS, KTRK, KMVY, KHYA, KEYW…) |
| FERRY | — | Positioning / continuity |

Fleet: open — any corporate jet (or turboprop/regional per service type) that sensibly fits the pairing. KLMT–PAFA (~1,624 nm) is the range outlier.

**SERVICE_TYPE is not yet a column in the data.** Name collision warning: the lookup page has an input also labeled "SERVICE TYPE" meaning *routing* class (ANY/NORMAL/HUB/THRU). Rename the lookup field to **ROUTING TYPE** when you build anything new.

---

## 2. Organization

| Region | Hubs | Manager / Assistant (Discord roles) |
|---|---|---|
| Great Lakes | KTVC (Hub 1) | GLM / GLAM |
| Eastern | KTEB (Hub 2) | EM / EAM — *mapping assumed, not confirmed by Michael* |
| Mountain | KBJC (Hub 3), KAFW (Hub 4) | MM / MAM |
| Southeast | KPDK (Hub 5), KLUK (Hub 8) | SEH / SEAM |
| Western | KVGT (Hub 6), KLMT (Hub 7) | WM / WAM |

Plus "Management" and "Assistant Management" roles. **Hub managers have write access and largely own their region's pairings.** There are currently no line pilots — management only. Cross-region editing is allowed by trust (no per-region locking); ownership is made visible, not enforced.

Staff home fields / ARTCCs (route-protecting, see §6): **KSGF, ZDV, ZID, ZLA, PAZA**. Michael is originally from San Diego.

---

## 3. Numbering architecture (authoritative)

Every hub has a **hub number N (1–8)**. Everything derives from N.

| N | Hub | Spoke block | Thru block | Spoke letter | Thru letter |
|---|---|---|---|---|---|
| 1 | KTVC | 100–299 | 3100–3299 | T | A |
| 2 | KTEB | 300–499 | 3300–3499 | E | B |
| 3 | KBJC | 500–699 | 3500–3699 | J | C |
| 4 | KAFW | 700–899 | 3700–3899 | W | D |
| 5 | KPDK | 900–1099 | 3900–4099 | P | F |
| 6 | KVGT | 1100–1299 | 4100–4299 | V | G |
| 7 | KLMT | 1300–1499 | 4300–4499 | M | H |
| 8 | KLUK | 1500–1699 | 4500–4699 | U | K |
| 9–14 | future | 1700–2899 (reserved) | 4700–5899 (reserved) | — | — |

- **Hub-to-hub connectors: 1–99** (pairs 2/1 … 98/97).
- Spoke block start = `200·N − 100`, width 200.
- **Thru = spoke block + 3000** ("mirror rule"). Decode any thru: subtract 3000 → lands in its hub's spoke block. Thru space ceiling 6999.
- **Pairs: outbound even, return = outbound − 1.**
- Hub decode: spoke `N = floor((n+100)/200)`; thru `N = floor((n−3100)/200) + 1`; `n < 100` → hub connector.
- The hub of a spoke/thru is its **origin** (first ICAO of the pairing).

---

## 4. The allocator (v6 — current mechanism)

Implemented in `apps-script/CherryAllocator.gs` (Google Apps Script, v6.1). **Install status in the live Google Sheet is unconfirmed — ask Michael.**

Semantics (keep these exactly in any reimplementation):

- Trigger: a pairing is entered (Flights col B; Thru cols D/E/F all filled; HubFlights col B) and the row's FLT # cell is empty.
- Choose block from origin hub (or 1–99 for connectors). Scan `cand = lo+2, lo+4, …` and take the **lowest even `cand` where neither `cand` nor `cand−1` is in USED**.
- USED = **Ledger ∪ every live FLT # and its return**. With `RECYCLE=false` (default) the Ledger makes deleted routes' numbers permanently retired.
- Write the number as a **static value** (purple bold), append both numbers to the Ledger. Never overwrite an existing number.
- `LockService` serializes concurrent hub-manager edits.
- `setup()` (run once as sheet owner) installs an **installable onEdit trigger running as the owner** and protects: FLT # columns (C) on all three route sheets, plus Ledger / Registry / NextFree / ThruSeg / Network Plan / Change Log. Hub managers keep write on pairing columns and notes.
- Menu "Cherry Air → Allocate missing numbers" handles bulk pastes (Google doesn't fire edit events for programmatic writes).

Verified by simulation against frozen v6 state: add spoke → 1130/1129; add thru → 3122/3121; add connector → 16/15; delete a route then add another in the same hub → next pair, **deleted pair not reissued**.

---

## 5. Callsigns & dispatch (VATSIM)

Limit: `CHY` + ≤4 chars = 7 total; letters **only** as a single trailing character (`CHY3M61` style is invalid).

| Flight | Session callsign | "If taken" backup |
|---|---|---|
| 3-digit (spokes < 1000) | number + random letter from pool **LNQRSXYZ** → `CHY178R` | number + another pool letter |
| 4-digit spoke (≥1000) | as-is → `CHY1159` | `CHY` + last 3 digits (zero-padded) + **spoke** letter → `CHY159V` |
| Thru | as-is → `CHY3179` | `CHY` + `(n−3000) mod 1000` zero-padded + **thru** letter → `CHY179A`, `CHY4361` → `CHY361H` |
| Hub connector | as-is (1–2 digits) + pool letter if needed | — |

Why it's collision-free: the 16 hub letters (TEJWPVMU + ABCDFGHK) are **reserved** — the random pool never uses them (I and O excluded for radio hygiene), so a trailing hub letter always means a hub-coded backup. Swept all 138 four-digit numbers: alternates unique, all match `^CHY\d{3}[A-Z]$`, zero overlap with the session-suffix space. Every form identifies the base hub.

Design history worth knowing: the original sheet used `RANDBETWEEN` per row to dodge VATSIM callsign conflicts. It re-rolled the entire airline on every recalc and baked in 38 duplicate numbers. Michael's *intent* (avoid callsign overlap) is preserved by the session-suffix layer; the *mechanism* is gone. Don't reintroduce randomness into flight numbers.

---

## 6. Route doctrine

Three independent, equally valid justifications for a route — any one suffices:
1. **Real-world demand** (metro-to-metro corporate/charter traffic — evaluate city/metro pairs, not airport pairs)
2. **Staff home airspace/fields** (KSGF; ZDV, ZID, ZLA, PAZA)
3. **Founder/staff local knowledge**

Selection philosophy: reliever/corporate fields over airline hubs; serve cities airlines forgot (COMM is a feature); respect hot-and-high field performance (KANK 7,523 ft; KSBS short high strip — turboprop territory).

**Design-protected (do not propose cutting):** all KSGF service (staff home field / de facto focus city); San Diego ×3 — KMYF, KCRQ, KSDM are distinct catchments (founder knowledge); short Michigan legs from KTVC (local intrastate service; KMKG is real EAS); thin Texas legs KAFW–KABI / KAFW–KLRD (feeder routes); ZDV/ZLA/ZID/PAZA routes incl. KBJC–KANK, KBJC–KPUB, KVGT–KIFP, KVGT–KHII, KLMT–PAFA.

Double-served markets (nonstop + thru) are intentional; lookup priority is direct → hub connector → thru, with the thru alternative always shown.

---

## 7. Current network state (v6)

- **147 active routes**: 7 hub connectors, 114 spokes, 26 thrus. **294 numbers in the Ledger.** All unique, all in-block (verified on export).
- Market-review changes applied (approved by Michael): KTVC–KGFK nonstop retired (KGFK served only by KTVC–KDLH–KGFK thru); KBJC–KEAU retired → **KBJC–KSTP** added; KVGT–KSBP retired → **KVGT–KSBP–KMRY** thru added (KVGT–KMRY nonstop kept); Provo consolidated to **KBJC–KPVU** (KVGT and KLMT originations retired); KLMT–KEGU (invalid ICAO) removed by Michael in v5.
- Note: v6 numbers came from the v5 positional era (dense; e.g. KVGT–KVNY = 1128/1127, connectors 2/1…14/13). They are now frozen. (Michael alphabetized the Flights sheet in v5, so earlier examples like KVGT–KVNY = 1102 are stale; v6 has 1128.)

---

## 8. Open items

| Item | Status / owner |
|---|---|
| Dakotas thru cluster (KMOT/KBIS/KGFK legs via KSTP, KRAP, KBZN) | **Benched** — Michael researching Bakken-era demand. GLM/MM/WM jointly. |
| Chicago gateways from KLUK (KARR, KRFD cut candidates; KPWK/KDPA/KMDW keep); KLUK–KUGN–KGRB stop | **Delegated** to SEH/SEAM |
| Stage-3 growth: KTEB–KPDK (top pick), KBJC/KAFW–KTEB, KPDK–KAGS seasonal, KVGT–KMRY Pebble Beach emphasis, KBJC–KELP | Not started; open-items post drafted for Discord |
| KLUK has no hub link | Suggest KLUK↔KPDK (same Southeast region) and/or KLUK↔KTVC |
| KLMT only tied via long KTVC connector | Suggest KLMT↔KVGT (same Western region) |
| KSGF formal status | Effectively answered: staff home field → designate focus city |
| Ops "day-pattern" schedule layer (SHUTTLE banks, COMM AM/PM rotations, CORP unscheduled, FERRY) | Coming from ops chat; natural fit for the code DB |
| Eastern region = KTEB | Assumed; confirm |
| Is the v6 allocator installed in the live Google Sheet? | Unknown; confirm |

---

## 9. Files in this bundle

```
cherry-air/
├── CLAUDE.md                          ← this file
├── apps-script/CherryAllocator.gs     ← v6.1 allocator (paste into Sheets → Extensions → Apps Script; run setup() once)
└── data/
    ├── Cherry_Air_Schedule_v6.xlsx    ← master workbook, numbers frozen as values
    ├── routes_v6.csv                  ← clean export: kind,origin,stop,dest,out,ret,hub,notes  (147 rows)
    └── ledger_v6.json                 ← {"ever_assigned":[...294 ints]}
```

Workbook sheets: `HubFlights` (B pairing, C FLT#, H return#, K CHECK) · `Flights` (B pairing, C FLT#, G return#, J CHECK, K Notes) · `Thru Flights` (D/E/F origin/stop/dest, C FLT#, I return#, M CHECK, N Notes) · `FLT # Look up` (A2 origin, B2 dest, C2 routing type → D2/E2/F2 result, D3 thru routing; row 8 dispatch: A8 schedule, B8 session, C8 if-taken, E8 base hub; B14 mirrors origin → thru browse rows 16–39) · `Network Plan` (blocks, next-free, region owners, doctrine notes) · `Change Log` · `Review` · `Ledger` · hidden `Registry`, `NextFree`, `ThruSeg` (6 segments per thru; col G show-flag dedupes the browse panel).

---

## 10. Gotchas learned the hard way

- **Google Sheets → xlsx export strips the `_xlfn.` prefix** from `SWITCH`/`MAXIFS` → `#NAME?` in Excel; it also turns some cells into `ArrayFormula` objects. Pick one master format deliberately.
- **openpyxl:** `ws.cell(row, col, value=None)` does **not** clear a cell (None = "no value passed"). Use `ws.cell(row, col).value = None`.
- openpyxl writes formulas without values; recalc with LibreOffice before reading `data_only=True`.
- CHECK/Registry ranges cap at rows 200 (Flights) / 60 (Thru) / 30 (HubFlights). The allocator scans all rows; the audit goes blind beyond those caps.
- The Next-Free panel is advisory; the Ledger is authoritative.
- Any pure-formula numbering scheme renumbers on insert/delete — stable numbers need persisted state. That's why v6 exists, and why the DB below exists.

---

## 11. Likely next build — "Option B": the sheet stops being the database

Agreed direction (deferred until now): SQLite + FastAPI, Docker Compose, Caddy; the xlsx becomes an export/view. Also the natural home for the ops schedule layer.

**Sketch (refine with Michael before building):**

- Tables: `hubs(n, icao, region, spoke_letter, thru_letter)`, `routes(id, kind[HUB|SPOKE|THRU], origin, stop, dest, out_no UNIQUE, ret_no UNIQUE, service_type, status[active|retired], created_by, created_at, retired_at, notes)`, `ledger(no PRIMARY KEY, route_id, assigned_at)`, `change_log(...)`.
- Allocator in the insert path inside one transaction (`BEGIN IMMEDIATE`), identical semantics to §4. Retire = status change, never row delete.
- Endpoints: route CRUD (hub-manager auth, region shown but not enforced unless asked), `/lookup?origin=&dest=&routing=`, `/thru-from/{icao}`, `/dispatch/{flt}` (session + backup callsign + base hub), `/export.xlsx`.
- UI: single mobile-friendly lookup page (vanilla JS/Tailwind) replicating the "FLT # Look up" terminal.
- Seed from `data/routes_v6.csv` + `data/ledger_v6.json` **without renumbering anything**.

**Golden tests (must pass before anything ships):**
1. All `out_no`/`ret_no` unique across live + ledger; `ret = out − 1`; `out` even.
2. Every number inside its hub's block (§3); connectors 1–99; thru = spoke block + 3000.
3. Delete/retire a route → add a new one in the same hub → old pair not reissued; no other route's number changed.
4. Every generated callsign matches `^CHY\d{1,4}[A-Z]?$` and is ≤ 7 chars; backups unique and never end in a pool letter; session suffixes never use a hub letter.
5. Seeded numbers equal `routes_v6.csv` exactly.
6. Lookup: `KTVC>KGFK` → thru 3106; `KTVC>KDLH` → direct 108 with thru shown; `KVGT>KVNY` → 1128, backup `CHY128V`, base KVGT; `KSTP>KMOT` → thru 3112 (KTVC–KSTP–KMOT); `KVGT>KSBP` → thru 4102; `KBJC>KSTP` → 514.

---

## 12. Decisions from the Claude Code explore session (2026-11-23)

- **This file (v6) is authoritative.** An older handoff written in the CCVA chats (v5.3, positional numbering, "port the formulas exactly", append-only) is superseded; only its phase plan and open structural decisions carry forward, as proposal material.
- **The v6 export is current.** The live Google Sheet has not been edited since; `data/source/routes_v6.csv` + `ledger_v6.json` are the seed.
- **Ledger protection starts at the v6 freeze — no backfill.** Pre-v6 numbers were not protected: e.g. CHY118 was KTVC–KGFK (nonstop, retired in the market review) and is now KTVC–KGRB. The "was X/Y" notes come from the RANDBETWEEN era and overlap current blocks, so they cannot be retired. Import them and the Change Log as historical text only.
- **OpenSpec root is per-project** at `projects/cherry-air/openspec/` (initialized with `--tools none`; the OpenSpec skills are installed at user level).
- **Still open:** dev environment (the desktop currently has no Python, Node, Docker or WSL; proposed: Python via uv on the desktop, Docker Compose + Caddy on the server only), what/where "the server" is, KTEB = Eastern region confirmation.

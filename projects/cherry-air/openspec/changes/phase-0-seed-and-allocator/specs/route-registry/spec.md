# Spec Delta

## Purpose

Holds Cherry Air's network of hub connectors, spokes and thrus as durable records, seeds it from the frozen v6 export with proven number-for-number parity, and keeps retired routes on record rather than deleting them.

## ADDED Requirements

### Requirement: Route record
Each route SHALL record its kind (HUB, SPOKE or THRU), origin, destination, outbound and return numbers, status (active or retired), and free-text notes. A thru SHALL also record its intermediate stop. Airports SHALL be four-character uppercase ICAO codes. A route's base hub is its origin.

#### Scenario: Thru without a stop
- **WHEN** a THRU route is submitted without a stop
- **THEN** it is rejected

#### Scenario: Stop repeats an endpoint
- **WHEN** a THRU route is submitted whose stop equals its origin or destination
- **THEN** it is rejected

#### Scenario: Malformed ICAO
- **WHEN** a route is submitted with the airport code "KEG"
- **THEN** it is rejected

### Requirement: No duplicate active routes
There SHALL be at most one active route of a given kind with the same origin, stop and destination. For hub connectors, a route and its reverse (A–B vs B–A) count as the same route. The same market served both nonstop and by a thru is allowed.

#### Scenario: Duplicate spoke
- **WHEN** an active KBJC–KSTP spoke exists and another KBJC–KSTP spoke is submitted
- **THEN** it is rejected

#### Scenario: Reverse connector
- **WHEN** an active KTVC–KVGT connector exists and a KVGT–KTVC connector is submitted
- **THEN** it is rejected

#### Scenario: Nonstop and thru to the same city
- **WHEN** the KTVC–KDLH spoke and the KTVC–KDLH–KGFK thru are both active
- **THEN** both are accepted

### Requirement: Seed from the v6 export without renumbering
Seeding SHALL load every row of `data/source/routes_v6.csv` as an active route, keeping its exact kind, airports, numbers and notes. It SHALL load every number in `data/source/ledger_v6.json` into the ledger. Seeding SHALL never run the allocator.

#### Scenario: Seeded network matches the export
- **WHEN** an empty database is seeded
- **THEN** it holds 147 active routes (7 HUB, 114 SPOKE, 26 THRU) and 294 ledger numbers, and every route's numbers equal its CSV row

#### Scenario: Seeded spot checks
- **WHEN** the seeded registry is queried
- **THEN** KVGT–KVNY is 1128/1127, KBJC–KSTP is 514/513, KTVC–KDLH is 108/107, KTVC–KDLH–KGFK is 3106/3105, KTVC–KSTP–KMOT is 3112/3111 and KVGT–KSBP–KMRY is 4102/4101

### Requirement: Seed data is validated before anything is written
Before writing, seeding SHALL verify that:
- no number appears twice across all outbound and return numbers
- every pair is even outbound with return = outbound − 1
- every number lies in its block for its kind and origin hub
- every number is in the ledger

If any check fails, seeding SHALL write nothing and report every violation.

#### Scenario: Corrupt export
- **WHEN** the CSV contains a duplicate outbound number
- **THEN** seeding writes nothing and reports the duplicate

### Requirement: Seed is cross-checked against the workbook
Seeding SHALL compare the CSV with the route sheets of the v6 workbook (`HubFlights`, `Flights`, `Thru Flights`) and SHALL refuse to seed if any pairing or number differs between them.

#### Scenario: CSV and workbook agree
- **WHEN** the shipped v6 CSV and workbook are compared
- **THEN** every route matches on kind, airports and numbers, and seeding proceeds

#### Scenario: CSV drifted from workbook
- **WHEN** a CSV row's outbound number differs from the workbook's
- **THEN** seeding writes nothing and reports the mismatched route

### Requirement: Seeding is idempotent and never overwrites
Seeding two empty databases from the same source SHALL produce identical route and ledger content. Seeding a database already holding identical seed content SHALL change nothing. Seeding a database whose routes differ from the source SHALL be refused, not overwritten.

#### Scenario: Re-seed an already seeded database
- **WHEN** seeding runs twice against the same database
- **THEN** the second run reports no changes and the content is unchanged

#### Scenario: Database has diverged
- **WHEN** a route has been added through an approved change and seeding is run again
- **THEN** seeding is refused and the database is unchanged

### Requirement: Pre-v6 history is text only
Route notes (including "was X/Y" mappings) and the rows of the workbook's `Change Log` sheet SHALL be imported verbatim as historical text and marked as pre-v6. Numbers found in this text SHALL never be read as flight numbers, ledger entries or allocator input.

#### Scenario: Old number in a note
- **WHEN** a seeded route's note reads "200-block shift (was 454/453)"
- **THEN** the note is stored verbatim, and 454 and 453 are neither in the ledger nor treated as in use unless the v6 data assigns them

### Requirement: Retiring keeps the route on record
Retiring a route SHALL set its status to retired and record when that happened. Its numbers, airports and notes are kept. A route SHALL never be deleted. A retired route stays readable but no longer counts toward the no-duplicate rule.

#### Scenario: Retire a spoke
- **WHEN** an active spoke is retired
- **THEN** it is still found by its outbound number with status retired, and its numbers remain in the ledger

#### Scenario: Re-add a retired market
- **WHEN** a spoke is retired and a new spoke with the same origin and destination is later approved
- **THEN** the new route gets a fresh pair and the retired route keeps its original numbers

### Requirement: Registry reads
The registry SHALL let callers list routes filtered by kind, base hub and status, and find a route by any of its numbers, outbound or return.

#### Scenario: Find by return number
- **WHEN** route 1127 is looked up
- **THEN** the KVGT–KVNY spoke (1128/1127) is returned

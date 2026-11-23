# Spec Delta

## Purpose

Captures MetroDreamin maps as versioned snapshots on local disk and reports what changed between two snapshots of the same map, so analysis is repeatable offline.

## ADDED Requirements

### Requirement: Fetch configured maps
The system SHALL fetch every map listed in the project configuration by building its ID from the owner's userId and map index, requesting the map's public view page, and extracting the embedded system payload.

#### Scenario: Map fetched successfully
- **WHEN** the fetch command runs and the view page for index 14 returns HTTP 200 with an embedded payload
- **THEN** the system extracts the payload and reports the map title, station count and last-updated time for index 14

#### Scenario: ID padding encoded
- **WHEN** the base64 map ID ends in `=` padding
- **THEN** the request URL carries the padding as `%3D`

### Requirement: Store snapshots by map edit time
The system SHALL save each fetched payload as UTF-8 JSON under a folder for the map, named by the map's own last-updated timestamp, and SHALL NOT write a new file when a snapshot with that timestamp already exists.

#### Scenario: New edit saved
- **WHEN** a fetched map's last-updated timestamp has no snapshot on disk
- **THEN** a new snapshot file is written and the command reports it as new

#### Scenario: Unchanged map skipped
- **WHEN** a fetched map's last-updated timestamp matches an existing snapshot
- **THEN** no file is written and the command reports the map as unchanged

#### Scenario: Names preserved exactly
- **WHEN** a station name contains an en dash or other non-ASCII character
- **THEN** the stored snapshot contains the identical characters

### Requirement: Isolate per-map fetch failures
The system SHALL report a failed fetch or a payload missing its expected structure for one map without stopping the other maps, and SHALL exit non-zero if any map failed.

#### Scenario: One map fails
- **WHEN** index 1 returns HTTP 500 and index 14 succeeds
- **THEN** index 14 is saved, index 1 is reported as failed with its status code, and the command exits non-zero

#### Scenario: Payload structure changed
- **WHEN** the view page has no stations and lines at the expected payload location
- **THEN** the map is reported as failed with the missing key and the keys that were found, and no snapshot is written

### Requirement: Diff two snapshots
The system SHALL compare two snapshots of the same map, matching stations and lines by object ID, and report added, removed and renamed stations and lines, stations moved more than 25 m, stations switched between station and waypoint, line mode or color changes, and changes to each line's station sequence.

#### Scenario: Station renamed
- **WHEN** a station keeps its ID but its name changes from `Santa Fe Depot` to `San Diego–Santa Fe Depot`
- **THEN** the diff lists it as renamed with the old and new names exactly

#### Scenario: Station added to a line
- **WHEN** the newer snapshot's line contains a station ID absent from the older snapshot's sequence
- **THEN** the diff lists the line with the inserted station and its neighbors

#### Scenario: Waypoint-only edits
- **WHEN** only waypoint coordinates changed between snapshots
- **THEN** the diff reports the count of moved waypoints without listing each one

#### Scenario: Default comparison
- **WHEN** the diff command is given only a map
- **THEN** it compares that map's two most recent snapshots, or reports that fewer than two exist

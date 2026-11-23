# Spec Delta

## Purpose

Turns a stored map snapshot into an exact, copy-pasteable edit list of station and line quality problems, grouped by the kind of edit the map author has to make.

## ADDED Requirements

### Requirement: Exclude waypoints from analysis
The system SHALL treat only non-waypoint stations as stations for every check, and SHALL measure spacing between consecutive non-waypoint stations along each line's sequence.

#### Scenario: Waypoints between stations
- **WHEN** a line's sequence is station A, three waypoints, station B
- **THEN** spacing is measured once, between A and B, and no waypoint appears in the report

### Requirement: Flag spacing by mode
The system SHALL flag consecutive station pairs closer than the minimum or farther than the maximum spacing for the line's mode, using straight-line (great-circle) distance, and SHALL NOT check spacing for ferry lines or lines with no or unknown mode.

#### Scenario: Tram stops too close
- **WHEN** two consecutive stations on a TRAM line are 180 m apart and the TRAM minimum is 250 m
- **THEN** the pair is listed under MERGE with both names, the line name and the distance

#### Scenario: Regional gap
- **WHEN** two consecutive stations on a REGIONAL line are 18.4 km apart and the REGIONAL maximum is 15 km
- **THEN** an infill item is listed under CREATE with both names, the line name and the distance

#### Scenario: Ferry skipped
- **WHEN** a FERRY line has stops 9 km apart
- **THEN** no spacing item is produced for that line

### Requirement: Report orphan stations
The system SHALL list every station that appears on no line under DELETE, with the nearest line and the distance to it.

#### Scenario: Station on no line
- **WHEN** a station's ID appears in no line's station sequence
- **THEN** it is listed under DELETE with its exact name, the nearest line's name and the distance

### Requirement: Report near-duplicate stations
The system SHALL list under MERGE each pair of distinct station objects within 150 m of each other or with identical names, with the distance and the lines each serves.

#### Scenario: Two objects at one location
- **WHEN** two station objects are 40 m apart
- **THEN** the pair is listed once under MERGE with both exact names, the distance and each station's lines

#### Scenario: Same name far apart
- **WHEN** two station objects share the name `County Admin. Ctr.` and are 2 km apart
- **THEN** the pair is listed under MERGE with the distance so the author can rename or merge

### Requirement: Treat placeholder-named lines as drafts
The system SHALL treat a line whose name matches a placeholder pattern (such as `Concept 3`, `Line 4`, `Untitled`, or blank) as a draft, list it once under HOUSEKEEPING with its station count, and exclude it from spacing and duplicate checks while still counting its stations as on a line.

#### Scenario: Concept lines present
- **WHEN** the map has lines `Concept 1` through `Concept 5`
- **THEN** HOUSEKEEPING lists five draft lines and no spacing or duplicate item names a Concept line

### Requirement: Report housekeeping issues
The system SHALL list under HOUSEKEEPING placeholder station names, lines with no or unknown mode, line names or line-group labels with leading, trailing or doubled spaces, lines with fewer than two stations, and stations repeated within a line's sequence other than a loop closing on its first station.

#### Scenario: Line missing mode
- **WHEN** a line's mode is empty
- **THEN** HOUSEKEEPING lists the line's exact name with "no mode set"

#### Scenario: Doubled space in name
- **WHEN** a line is named `D Line  - North Extension`
- **THEN** HOUSEKEEPING lists it with the name shown exactly, including both spaces

#### Scenario: Out-and-back repeat
- **WHEN** a line's sequence visits `Santa Fe Depot` twice and does not start and end there
- **THEN** HOUSEKEEPING lists the line and the repeated station

### Requirement: Produce a deterministic punch list
The system SHALL write a Markdown punch list for a snapshot with a header (map title, snapshot time, station and line counts, thresholds used) followed by DELETE, MERGE, CREATE and HOUSEKEEPING sections in that order, with names copied exactly, and SHALL produce identical output for the same snapshot.

#### Scenario: Same snapshot twice
- **WHEN** analysis runs twice on the same snapshot
- **THEN** both reports are byte-identical

#### Scenario: Empty section
- **WHEN** a map has no orphan stations
- **THEN** the DELETE section is present and states that nothing was found

#### Scenario: Exact names
- **WHEN** a station is named `San Diego–Santa Fe Depot`
- **THEN** the report shows that name with the en dash, never a hyphen

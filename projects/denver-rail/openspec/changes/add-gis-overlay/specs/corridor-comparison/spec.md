# Spec Delta

## Purpose

Links each historic streetcar corridor to the modern service that now runs along it, and checks the hand-curated scorecard mapping against the actual geometry. Any disagreement becomes a finding to review rather than being silently resolved.

## ADDED Requirements

### Requirement: Corridors joined to modern service
For each corridor in the reference table, the system SHALL produce a comparison record. It lists the corridor's 1946 routes, the modern routes named by the scorecard, the rail or BRT status, the verdict, and the ridership of the named bus routes where known.

#### Scenario: Comparison record per corridor
- **WHEN** the comparison stage runs
- **THEN** there is exactly one comparison record for each corridor in the reference table

#### Scenario: Scorecard is authoritative
- **WHEN** the scorecard names a modern route for a corridor
- **THEN** that route appears in the corridor's record, whatever the geometric check finds

### Requirement: Geometric cross-check
For each corridor, the system SHALL measure how much of its historic geometry lies within a set distance of each modern route. Every modern route above a set overlap share is listed as a geometric match.

#### Scenario: Overlapping modern route found
- **WHEN** at least the configured share of a corridor's historic geometry lies within the configured distance of a modern route
- **THEN** that route is listed as a geometric match, with its overlap share

#### Scenario: Thresholds recorded
- **WHEN** the comparison stage completes
- **THEN** the distance and overlap thresholds used are recorded with the results

### Requirement: Disagreements reported
The system SHALL report every case where the scorecard and the geometry disagree. It does not change either one.

#### Scenario: Scorecard route without geometric support
- **WHEN** a route named by the scorecard falls below the overlap threshold for its corridor
- **THEN** the pair is reported as a disagreement of type "named-not-overlapping"

#### Scenario: Geometric match not named by scorecard
- **WHEN** a modern route is a geometric match for a corridor but is not named by the scorecard
- **THEN** the pair is reported as a disagreement of type "overlapping-not-named"

### Requirement: Through-routing comparison
The system SHALL compare the 1946 through-routed pairs listed in the reference data with today's routes that cross downtown. The results go into the report.

#### Scenario: Pair compared
- **WHEN** a 1946 through-routed pair is listed in the reference data
- **THEN** the report states which modern routes, if any, run through downtown on both of the pair's corridors, along with their ridership change where known

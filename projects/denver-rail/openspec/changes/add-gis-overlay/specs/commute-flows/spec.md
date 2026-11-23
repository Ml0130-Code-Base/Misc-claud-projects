# Spec Delta

## Purpose

Turns Census LODES origin-destination employment data into commute-demand layers for the RTD district: where workers live, where jobs are, and the largest longer-distance commute pairs. These are used to judge whether a corridor serves real travel demand.

## ADDED Requirements

### Requirement: Flows limited to the RTD district
The system SHALL include only commutes where both the home and the work location fall in Adams, Arapahoe, Boulder, Broomfield, Denver, Douglas or Jefferson County, Colorado.

#### Scenario: Out-of-area commute excluded
- **WHEN** a LODES record has a home or work block outside those counties
- **THEN** that record does not contribute to any commute-flow layer

### Requirement: Density layer of homes and jobs
The system SHALL produce a point layer with one feature per census tract. Each feature carries the number of workers living in the tract and the number of jobs located in it.

#### Scenario: Tract totals
- **WHEN** the flows stage completes
- **THEN** each tract feature's worker count equals the sum of in-area flows originating in its blocks, and its job count equals the sum of in-area flows ending in its blocks

### Requirement: Top commute pairs layer
The system SHALL produce a line layer of the largest commute flows between coarse zones, skipping pairs closer together than a minimum distance. Each line carries its total flow, both directions combined.

#### Scenario: Short hops excluded
- **WHEN** two zones are closer together than the configured minimum distance
- **THEN** no commute-pair line is produced between them

#### Scenario: Ranked and capped
- **WHEN** the top-pairs layer is built
- **THEN** it holds at most the configured number of lines, all with flows greater than or equal to every excluded qualifying pair

### Requirement: Data year is labeled
Every commute-flow layer SHALL record the LODES data year and job type it was built from.

#### Scenario: Year visible downstream
- **WHEN** a commute-flow layer is read by the map or the report
- **THEN** the LODES data year and job type are available as layer metadata

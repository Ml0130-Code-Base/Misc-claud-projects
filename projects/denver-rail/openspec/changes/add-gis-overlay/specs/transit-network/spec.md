# Spec Delta

## Purpose

Provides today's RTD network (bus, light rail, commuter rail, stations and planned BRT or rail projects) as geographic layers, with service frequency and reported ridership. This gives each historic corridor a modern network to compare against.

## ADDED Requirements

### Requirement: Modern routes built from a current GTFS feed
The system SHALL build route layers from an RTD GTFS feed whose service dates cover the run date or a date after 2026-09-27. Routes are split into bus and rail by GTFS route type, with one feature per route.

#### Scenario: Current feed used
- **WHEN** the transit stage runs
- **THEN** the feed's service start and end dates are recorded, and the stage refuses to build if the feed's service ended before 2026-09-27

#### Scenario: Bus and rail separated
- **WHEN** route layers are built
- **THEN** bus routes (GTFS route type 3) are written to a bus layer, light rail and commuter rail (route types 0 and 2) are written to a rail layer, and each route appears exactly once

### Requirement: Stations layer
The system SHALL produce a station layer of point features for rail stops. Each station lists the rail routes that serve it.

#### Scenario: Station with multiple lines
- **WHEN** a rail station is served by more than one rail route
- **THEN** its feature lists all of those routes

### Requirement: Routes carry service frequency
Each route feature SHALL carry a weekday midday headway in minutes, taken from the scheduled trips in the feed.

#### Scenario: Headway computed
- **WHEN** a route has scheduled weekday trips between 10:00 and 14:00
- **THEN** its feature carries the average headway in minutes for its busiest direction in that window

#### Scenario: No midday service
- **WHEN** a route has no weekday trips between 10:00 and 14:00
- **THEN** its headway field is empty and it is not reported as zero

### Requirement: Bus routes carry reported ridership
Bus route features SHALL carry 2019 and 2024 ridership and their percentage change, taken from the hand-curated ridership table, along with that table's source.

#### Scenario: Ridership available
- **WHEN** a route appears in the ridership table
- **THEN** its feature carries the 2019 and 2024 figures, the percentage change and the source

#### Scenario: Ridership missing
- **WHEN** a route does not appear in the ridership table
- **THEN** its ridership fields are empty and no value is estimated

### Requirement: Planned projects shown separately from operating service
Planned or unbuilt BRT and rail projects from the planned-projects table SHALL appear as features marked planned, with mode, target year and the date the information was current.

#### Scenario: Planned BRT drawn
- **WHEN** the planned-projects table lists a BRT project with a source route and two end stops
- **THEN** a planned feature is produced along that route's geometry between those stops, carrying `status`, `target_year` and `as_of`

#### Scenario: Planned never mixed with operating
- **WHEN** layers are built
- **THEN** no planned feature is marked as operating, and no operating route is marked as planned

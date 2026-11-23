# Spec Delta

## Purpose

Presents the historic, modern and commute-demand layers together on one static, self-contained interactive map page. It uses a clean, transit-style legend and color system, so corridor verdicts can be checked visually.

## ADDED Requirements

### Requirement: Single self-contained page
The system SHALL render the map as one HTML file with every data layer embedded. Only the basemap tiles and the map library are loaded over the network.

#### Scenario: Opened from disk
- **WHEN** the map file is opened directly from the local file system in a current browser
- **THEN** every data layer displays without a local server

#### Scenario: Basemap unavailable
- **WHEN** basemap tiles fail to load
- **THEN** all data layers still display over a plain background

### Requirement: Layer toggles
The map SHALL let the viewer show or hide each of these layer groups on its own: Historic lines, Today's bus, Rail+BRT, and Commute flows.

#### Scenario: Toggle a group
- **WHEN** the viewer turns off one layer group
- **THEN** only that group's features are hidden, and the other groups are unaffected

### Requirement: Historic lines colored by verdict
Historic lines SHALL be drawn in one color per verdict class. The legend names all five classes with their colors.

#### Scenario: Verdict color applied
- **WHEN** a historic line has a verdict class
- **THEN** it is drawn in that class's legend color

#### Scenario: Unmatched line distinguishable
- **WHEN** a historic line has no matched 1946 route
- **THEN** it is drawn in a distinct "unmatched" style that the legend also explains

### Requirement: Planned service drawn as planned
Planned BRT and rail features SHALL be visually distinct from operating service. They are labeled with their target year and the date that information was current.

#### Scenario: Planned project inspected
- **WHEN** the viewer selects a planned feature
- **THEN** its details show the mode, target year and as-of date, and the line is drawn in a planned style (for example, dashed)

### Requirement: Feature details on selection
Selecting a feature SHALL show its key attributes.
- Historic lines show the 1946 route(s), corridor, verdict text and today's routes.
- Bus routes show 2019 and 2024 ridership, percentage change and midday headway.
- Commute features show the flow or counts and the LODES data year.

#### Scenario: Historic line selected
- **WHEN** the viewer selects a historic line
- **THEN** the details show its 1946 route(s), corridor name, verdict text and modern routes

#### Scenario: Bus route selected
- **WHEN** the viewer selects a bus route
- **THEN** the details show its ridership figures, where known, and its midday headway

### Requirement: Usable at phone width
The map and its legend SHALL stay usable at a 375-pixel-wide viewport, with no horizontal page scrolling.

#### Scenario: Narrow viewport
- **WHEN** the page is viewed at 375 pixels wide
- **THEN** the legend can be collapsed, and every layer toggle can still be reached

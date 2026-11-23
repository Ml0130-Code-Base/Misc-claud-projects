# Spec Delta

## Purpose

Makes the map page credit its basemap and data sources, state that it is unofficial, and show how current its data is. Viewers of the public page can then judge what they are looking at, and the page meets the basemap and RTD data terms.

## ADDED Requirements

### Requirement: Basemap credit on the map
The map SHALL show a credit for OpenStreetMap contributors and CARTO on the map itself, with links to their attribution pages. It SHALL be visible without any click, at every supported viewport width.

#### Scenario: Credit at desktop width
- **WHEN** the page is opened at a desktop viewport
- **THEN** the OpenStreetMap and CARTO credit is visible on the map without any interaction

#### Scenario: Credit at phone width
- **WHEN** the page is opened at a 375-pixel-wide viewport with the legend expanded or collapsed
- **THEN** the credit stays visible and readable, and is not covered by the legend

### Requirement: Unofficial notice
The page SHALL state, visibly and without any click, that it is an unofficial site that RTD has not endorsed, sponsored or affiliated itself with. The page SHALL NOT show RTD logos or reuse content from RTD's website.

#### Scenario: Notice visible on load
- **WHEN** the page loads
- **THEN** the unofficial, not-affiliated-with-RTD notice is visible without any interaction

#### Scenario: No RTD branding
- **WHEN** the page's embedded assets are inspected
- **THEN** none of them is an RTD logo or an image taken from RTD's website

### Requirement: Data currency shown
The page SHALL show the GTFS feed's service dates, the LODES data year, the date of the scorecard used, and the as-of date of the planned-project information.

#### Scenario: Dates shown
- **WHEN** the viewer opens the About panel
- **THEN** it shows the GTFS service dates, the LODES year, the scorecard date and the planned-project as-of date, each matching the run that built the page

### Requirement: Source list
The page SHALL have an About panel listing every data source used to build it, each with its name, a link to its origin, and its retrieval or as-of date. It SHALL also say what the map is for: a corridor study, not advocacy for restoring streetcars.

#### Scenario: Sources listed
- **WHEN** the viewer opens the About panel
- **THEN** it lists the CDOT historic streetcar layer, RTD GTFS, Census LODES, the 1946 route list and the scorecard, each with a link and a date

#### Scenario: Purpose stated
- **WHEN** the viewer opens the About panel
- **THEN** it says the map is a corridor study for modern rapid transit, not a case for bringing streetcars back

### Requirement: Disclosures in every build
The credit, notice and About panel SHALL appear both in the locally built map and in the published page, including when the page is opened from disk without basemap tiles.

#### Scenario: Opened from disk without tiles
- **WHEN** the locally built map is opened from the file system and basemap tiles fail to load
- **THEN** the credit, the unofficial notice and the About panel are all still present

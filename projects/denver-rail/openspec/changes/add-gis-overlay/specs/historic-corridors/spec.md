# Spec Delta

## Purpose

Provides the historic Denver Tramway streetcar network as a clean geographic layer. Each line is labeled with its 1946 route number(s) and the scorecard verdict for its corridor, so the old network can be read as a corridor map.

## ADDED Requirements

### Requirement: Historic lines are normalized to GeoJSON
The system SHALL produce a cleaned historic streetcar layer as GeoJSON in EPSG:4326 from the CDOT "Historic Streetcar Lines" source, without modifying the raw download.

#### Scenario: Clean layer produced from raw download
- **WHEN** the historic stage runs against a CDOT download present in the raw data folder
- **THEN** a GeoJSON FeatureCollection with coordinates in longitude/latitude (EPSG:4326) is written to the clean data folder
- **AND** the raw download is byte-identical before and after the run

#### Scenario: Source in a different projection
- **WHEN** the CDOT download uses a projected coordinate system
- **THEN** the cleaned layer's coordinates are reprojected to EPSG:4326 and fall within the Denver metro bounding box

### Requirement: CDOT attributes are preserved
Every cleaned historic feature SHALL keep all attribute fields and values from the CDOT source unchanged. Added fields SHALL NOT overwrite a source field.

#### Scenario: Attribute table intact
- **WHEN** a cleaned feature is compared with its source feature
- **THEN** every source attribute is present with the same value

### Requirement: Lines are labeled with 1946 routes
Each cleaned historic feature SHALL carry a `route_1946` field listing the 1946 route number(s) it belongs to. Matching uses source attributes first, then the hand-curated override table.

#### Scenario: Matched by source attribute
- **WHEN** a CDOT feature's name or number corresponds to a route listed in the corridor reference table
- **THEN** its `route_1946` field lists that route

#### Scenario: Matched by override
- **WHEN** a CDOT feature has an entry in the override table
- **THEN** its `route_1946` field uses the override value, even if a source-attribute match exists

#### Scenario: No match
- **WHEN** a CDOT feature matches neither a source attribute nor an override entry
- **THEN** its `route_1946` field is empty and the feature is listed as unmatched in the run report

### Requirement: Lines carry their corridor verdict
Each matched historic feature SHALL carry the `corridor_id`, `verdict_text` and `verdict_class` of its corridor from the reference table. `verdict_class` SHALL be one of `built-or-building`, `returning`, `next-candidate`, `feeder-only` or `leave`.

#### Scenario: Verdict attached
- **WHEN** a feature's `route_1946` belongs to a corridor in the reference table
- **THEN** the feature carries that corridor's id, verdict text and one of the five verdict classes

#### Scenario: Every corridor represented
- **WHEN** the historic stage completes
- **THEN** every corridor in the reference table has at least one matched feature, or it is listed as unrepresented in the run report

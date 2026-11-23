# Spec Delta

## Purpose

Makes every output traceable to its sources. Raw downloads are never edited, each source is recorded with its date and checksum, and layer counts and findings are reported. Results can then be re-checked and handed back to the chat synthesis.

## ADDED Requirements

### Requirement: Raw downloads are immutable and recorded
Each raw source file SHALL be recorded in a manifest with its source URL (or "manual"), retrieval time, size and SHA-256. No pipeline stage SHALL modify a file in the raw data folder.

#### Scenario: Automatic download recorded
- **WHEN** the fetch stage downloads a source
- **THEN** the manifest gains an entry with its URL, retrieval timestamp, byte size and SHA-256

#### Scenario: Manual download recorded
- **WHEN** a source file was placed in the raw data folder by hand
- **THEN** the fetch stage records it in the manifest with source "manual", its size and its SHA-256

#### Scenario: Raw files untouched
- **WHEN** any stage after fetch runs
- **THEN** every raw file's SHA-256 still matches its manifest entry

### Requirement: Failed fetch stops with instructions
When an automatic download fails, the system SHALL stop and print the source URL and the expected file name and location for a manual download. It SHALL NOT continue with missing data.

#### Scenario: Blocked download
- **WHEN** a source download fails or is blocked
- **THEN** the fetch stage exits with a non-zero status and prints the URL and the expected file path

### Requirement: Source versions recorded
The run report SHALL record the GTFS feed's service dates and version, the LODES data year, and the date of the scorecard used.

#### Scenario: Versions in report
- **WHEN** the report stage runs
- **THEN** the GTFS service dates, LODES year and scorecard date all appear in the summary

### Requirement: Layer statistics
The system SHALL write the feature count of every cleaned layer, the list of unmatched historic features, any corridors with no historic feature, and all comparison disagreements to a machine-readable statistics file.

#### Scenario: Counts written
- **WHEN** the report stage runs
- **THEN** the statistics file holds a feature count for each cleaned layer and lists every unmatched feature, unrepresented corridor and disagreement

### Requirement: One-page summary for hand-back
The system SHALL produce `summary.md`. It contains generated sections for layer counts, the join results, disagreements with the scorecard, and dates to re-check before publishing. Hand-written sections are kept when it is regenerated.

#### Scenario: Regeneration keeps narrative
- **WHEN** the report stage regenerates `summary.md`
- **THEN** generated sections are replaced with current data, and text outside them is unchanged

#### Scenario: Stale dates flagged
- **WHEN** the summary is generated
- **THEN** it lists every planned-project target year with its as-of date, under a "re-check before publishing" heading

### Requirement: Working log
The project SHALL keep `NOTES.md` as a dated, append-only log of pipeline runs. Each entry records the feed dates, layer counts and any decisions made.

#### Scenario: Run logged
- **WHEN** a full pipeline run is completed during implementation
- **THEN** a dated entry with that run's feed dates and layer counts is appended to `NOTES.md` and earlier entries stay unchanged

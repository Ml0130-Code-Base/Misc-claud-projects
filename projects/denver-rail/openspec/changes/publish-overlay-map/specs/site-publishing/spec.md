# Spec Delta

## Purpose

Turns the locally built overlay map into the public GitHub Pages site. Publishing is a deliberate, checked step. It never exposes project source or data beyond the page itself, and it never commits the basemap key to the main branch.

## ADDED Requirements

### Requirement: Publishing is manual
The public site SHALL change only when the owner runs the publish step. Pushing commits to the main branch, including commits that change the built map, SHALL NOT change the public site.

#### Scenario: Rebuilt map pushed to main
- **WHEN** a new `out/map.html` is committed and pushed to the main branch, and the publish step has not been run
- **THEN** the public site still serves the previously published page

#### Scenario: Publish step run
- **WHEN** the owner runs the publish step and every check passes
- **THEN** the public site serves the new page once GitHub Pages finishes deploying

### Requirement: Publishes only the committed build
The publish step SHALL publish the map exactly as committed on the main branch. It SHALL refuse to publish when the working copy of the built map has uncommitted changes.

#### Scenario: Uncommitted map changes
- **WHEN** the built map differs from its committed version and the publish step runs
- **THEN** the publish step stops without changing the published branch, and says the map must be committed first

### Requirement: Dates re-checked before publishing
The publish step SHALL refuse to publish unless the "re-check before publishing" list in the summary has a confirmation date on or after the date the map was built.

#### Scenario: Re-check not confirmed
- **WHEN** the summary's re-check list has no confirmation date, or one earlier than the map's build date
- **THEN** the publish step stops, lists the items to re-check, and leaves the published branch unchanged

#### Scenario: Re-check confirmed
- **WHEN** the confirmation date is on or after the map's build date
- **THEN** the publish step continues to its remaining checks

### Requirement: Published branch holds only the site
The published branch SHALL contain only the page, served as `index.html`, and the files GitHub Pages needs to serve it as-is. It SHALL NOT contain scripts, reference or raw data, OpenSpec files, or other projects' files.

#### Scenario: Published branch contents
- **WHEN** a publish completes
- **THEN** the published branch lists only `index.html` and the Pages control file that disables site processing

### Requirement: Basemap key only in the published copy
The basemap API key SHALL be read from local, gitignored configuration and added only to the published copy of the page. The map committed on the main branch SHALL NOT contain the key.

#### Scenario: Key kept off main
- **WHEN** the map is built and committed to the main branch
- **THEN** the committed file contains a placeholder instead of the key

#### Scenario: Key missing at publish
- **WHEN** the publish step runs and no basemap key is configured
- **THEN** the publish step stops and names the configuration entry to set

#### Scenario: Key in published page
- **WHEN** a publish completes
- **THEN** the published `index.html` contains the configured key and no placeholder

### Requirement: Page size budget
The published page SHALL be no larger than 5 MB. The publish step SHALL refuse to publish a page over that size and report its actual size.

#### Scenario: Page over budget
- **WHEN** the page to be published is larger than 5 MB
- **THEN** the publish step stops, reports the page size, and leaves the published branch unchanged

### Requirement: Coordinate precision
Every coordinate embedded in the map page SHALL carry no more than 5 decimal places.

#### Scenario: Embedded coordinates rounded
- **WHEN** the map is built
- **THEN** no embedded longitude or latitude has more than 5 digits after the decimal point

### Requirement: Dry run
The publish step SHALL offer a dry run that runs every check and assembles the site in a temporary location, without committing or pushing anything.

#### Scenario: Dry run
- **WHEN** the owner runs the publish step as a dry run
- **THEN** it reports each check's result, the page size, and where the assembled site was written, and neither the published branch nor the remote changes

### Requirement: Publish confirmed before push
After its checks pass, the publish step SHALL show what it will publish (source commit, page size, target URL) and push only after the owner confirms.

#### Scenario: Owner declines
- **WHEN** the owner declines the confirmation prompt
- **THEN** nothing is pushed to the remote

### Requirement: Publishes are logged
Each completed publish SHALL add a dated entry to the working log, recording the main-branch commit of the map, the published-branch commit, and the page size.

#### Scenario: Publish logged
- **WHEN** a publish is pushed
- **THEN** `NOTES.md` gains an entry with the date, both commit ids and the page size, and earlier entries stay unchanged

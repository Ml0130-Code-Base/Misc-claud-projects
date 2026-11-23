# Proposal

## Why

Map cleanup for the MetroDreamin fantasy systems has so far run as ad-hoc JavaScript in a live browser tab, so every review starts from scratch, results can't be reproduced, and edit lists go stale as soon as the map changes (the San Diego #14 punch list from August already references station names that no longer exist). A plain HTTP fetch of the `/view/` page has been verified to return the full map payload, so the whole workflow can move into repeatable offline scripts.

## What Changes

- New fetch step: build map IDs for configured map indices, download each `/view/` page, extract the embedded system payload, and save a timestamped snapshot to disk. Re-running when the map is unchanged writes nothing.
- New diff step: compare two snapshots of the same map and report what changed (stations and lines added, removed, renamed, moved, re-sequenced).
- New analysis step: load a snapshot, drop waypoints, run spacing (thresholds per mode), orphan, near-duplicate, placeholder-name, and housekeeping checks, and emit a Markdown punch list grouped DELETE / MERGE / CREATE / HOUSEKEEPING with exact name strings, distances, and line assignments.
- Initial scope: Denver Metro Fantasy Rail Map (#1) and San Diego County Transit Fantasy (#14). Other maps on the profile can be added by config, not code.

## Capabilities

### New Capabilities
- `map-snapshots`: fetching a MetroDreamin map by owner and index, storing it as a versioned snapshot on disk, and diffing two snapshots of the same map.
- `map-punch-list`: analyzing a stored snapshot for station and line quality problems and producing an actionable, copy-pasteable edit list.

### Modified Capabilities
- None.

## Impact

- New Python 3.12 scripts under `projects/metro-maps/`, standard library only.
- Network: read-only GET requests to `metrodreamin.com/view/...` for the owner's own maps.
- Snapshot files on local disk. Map #14 is flagged private on MetroDreamin, so snapshots stay out of git by default.
- No changes outside `projects/metro-maps/`.

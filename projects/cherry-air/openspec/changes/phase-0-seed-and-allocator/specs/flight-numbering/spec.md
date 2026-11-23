# Spec Delta

## Purpose

Assigns every Cherry Air route a permanent outbound/return flight-number pair from its hub's block, and guarantees that no number is ever changed, user-chosen, or reissued.

## ADDED Requirements

### Requirement: Hub number blocks
Each hub SHALL have a hub number N in the fixed order KTVC=1, KTEB=2, KBJC=3, KAFW=4, KPDK=5, KVGT=6, KLMT=7, KLUK=8. A spoke's numbers SHALL lie in its origin hub's spoke block, 200·N−100 to 200·N+99. A thru's numbers SHALL lie in that block plus 3000. A hub connector's numbers SHALL lie in 1–99. Hub numbers 9–14 are reserved and have no block in use.

#### Scenario: Spoke block for KVGT
- **WHEN** the spoke block for KVGT (N=6) is requested
- **THEN** it is 1100–1299

#### Scenario: Thru block mirrors spoke block
- **WHEN** the thru block for KTVC (N=1) is requested
- **THEN** it is 3100–3299, the KTVC spoke block plus 3000

#### Scenario: Reserved hub numbers
- **WHEN** a block is requested for hub number 9
- **THEN** the request is rejected because hubs 9–14 are reserved

### Requirement: Paired numbers
Every route SHALL have an even outbound number and a return number equal to the outbound minus one.

#### Scenario: Pair shape
- **WHEN** any route's numbers are read
- **THEN** the outbound is even and the return is outbound − 1

### Requirement: Hub decode
Given any assigned number, the system SHALL determine its kind and base hub. A number below 100 is a hub connector. A number from 100 to 2899 is a spoke of hub floor((n+100)/200). A number from 3100 to 5899 is a thru of hub floor((n−3100)/200)+1.

#### Scenario: Decode a spoke
- **WHEN** 1128 is decoded
- **THEN** the result is a spoke with base hub KVGT

#### Scenario: Decode a thru
- **WHEN** 4361 is decoded
- **THEN** the result is a thru with base hub KLMT

#### Scenario: Decode a connector
- **WHEN** 15 is decoded
- **THEN** the result is a hub connector

### Requirement: Lowest-free-pair allocation
A new route's pair SHALL be the lowest even number c in its block, scanning from block start + 2, where neither c nor c−1 is in use. "In use" means held by any route, active or retired, or present in the ledger. Spokes and thrus use the origin hub's block; hub connectors use 1–99.

#### Scenario: Next KVGT spoke from the v6 state
- **WHEN** a new spoke originating at KVGT is allocated against the seeded v6 data
- **THEN** it receives 1130/1129

#### Scenario: Next KTVC thru from the v6 state
- **WHEN** a new thru originating at KTVC is allocated against the seeded v6 data
- **THEN** it receives 3122/3121

#### Scenario: Next hub connector from the v6 state
- **WHEN** a new hub connector is allocated against the seeded v6 data
- **THEN** it receives 16/15

### Requirement: Allocation requires a hub origin
Allocating a spoke or thru SHALL be rejected when its origin is not one of the eight hubs. Allocating a hub connector SHALL be rejected unless both endpoints are hubs.

#### Scenario: Non-hub origin
- **WHEN** a spoke originating at KSGF is allocated
- **THEN** the allocation is rejected and no number is assigned

### Requirement: Full block is refused
When a block has no free pair, the allocation SHALL fail with an error that names the block. No number outside the block may be assigned.

#### Scenario: Block exhausted
- **WHEN** every pair in a hub's spoke block is in use and another spoke is allocated for that hub
- **THEN** the allocation fails with a "block full" error and the ledger is unchanged

### Requirement: Permanent ledger
Each assigned number, outbound and return, SHALL be recorded in the ledger in the same transaction that assigns it. Ledger entries SHALL never be removed or edited.

#### Scenario: Allocation records both numbers
- **WHEN** a pair is allocated
- **THEN** both numbers appear in the ledger once the transaction commits

#### Scenario: Failed allocation leaves no trace
- **WHEN** an allocation's transaction fails or is rolled back
- **THEN** neither the route nor its numbers are written

### Requirement: Numbers are never reissued
A number in the ledger SHALL never be assigned to another route, even after the route holding it is retired.

#### Scenario: Retire then add in the same hub
- **WHEN** a KVGT spoke is retired and a new KVGT spoke is then allocated
- **THEN** the new spoke receives the next free pair, not the retired pair

### Requirement: Numbers are system-assigned and immutable
A flight number SHALL come only from the allocator. A request that supplies a number for a new route, or changes an existing route's number, SHALL be rejected.

#### Scenario: Caller supplies a number
- **WHEN** a new route is submitted with an explicit outbound number
- **THEN** the request is rejected

#### Scenario: Caller edits a number
- **WHEN** a change to an existing route's outbound or return number is attempted
- **THEN** the change is rejected and the stored numbers are unchanged

### Requirement: Concurrent allocations never collide
Allocations that run at the same time SHALL never assign the same number to two routes.

#### Scenario: Two simultaneous spokes in one hub
- **WHEN** two KBJC spokes are allocated concurrently
- **THEN** they receive two different pairs and both pairs are in the ledger

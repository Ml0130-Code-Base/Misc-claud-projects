# Spec Delta

## Purpose

Encodes Cherry Air's route authority: additions and retirements start as pending proposals, and only an explicit, recorded approval changes the network.

## ADDED Requirements

### Requirement: Route changes start as proposals
Adding or retiring a route SHALL first be submitted as a proposal with status pending. An ADD proposal carries the route's kind, airports and notes, but no numbers. A RETIRE proposal identifies an existing active route by one of its numbers. A pending proposal SHALL NOT change the registry or the ledger.

#### Scenario: Submit an addition
- **WHEN** an ADD proposal for a new KBJC spoke is submitted
- **THEN** the proposal is stored as pending, and the route list and ledger are unchanged

#### Scenario: Retire an unknown route
- **WHEN** a RETIRE proposal names a number that no active route holds
- **THEN** the proposal is rejected at submission

### Requirement: Proposal preview
A pending ADD proposal SHALL show the pair it would receive if approved now. The preview reserves nothing. The pair actually assigned is decided at approval and can differ if other changes were approved in between.

#### Scenario: Preview does not reserve
- **WHEN** two pending ADD proposals for KVGT spokes both preview 1130/1129 and the first is approved
- **THEN** the first receives 1130/1129, and the second's preview becomes 1132/1131

### Requirement: Approval applies the change atomically
Approving a proposal SHALL record the approver's name and the time, and apply the change in one transaction. For ADD, the allocator assigns the numbers and the route becomes active. For RETIRE, the route's status becomes retired. If the change is invalid at approval time, approval SHALL fail, nothing SHALL change, and the proposal SHALL stay pending with the reason.

#### Scenario: Approve an addition
- **WHEN** a pending ADD proposal for a new KVGT spoke is approved against the v6 data
- **THEN** the route is active with 1130/1129, both numbers are in the ledger, and the proposal is approved with approver and time

#### Scenario: Became invalid while pending
- **WHEN** an ADD proposal duplicates a route that another approval created after it was submitted, and it is then approved
- **THEN** approval fails, no number is assigned, and the proposal stays pending with the duplicate reason

#### Scenario: Approver required
- **WHEN** approval is attempted without an approver name
- **THEN** it is refused and nothing changes

### Requirement: Rejection has no effect
Rejecting a proposal SHALL record the reason, the decider and the time. It SHALL NOT change the registry or the ledger.

#### Scenario: Reject an addition
- **WHEN** a pending ADD proposal is rejected
- **THEN** no route is created and no number is consumed

### Requirement: Decisions are final
An approved or rejected proposal SHALL NOT be approved, rejected or edited again. A new proposal is needed instead.

#### Scenario: Approve twice
- **WHEN** an already approved proposal is approved again
- **THEN** the request is refused and nothing changes

### Requirement: Only approval mutates routes
Outside the initial seed, routes SHALL be created or retired only by approving a proposal. No other operation may insert, retire, delete or renumber a route.

#### Scenario: Direct write attempt
- **WHEN** any registry operation other than seeding or approving a proposal tries to create, retire or change a route
- **THEN** no such operation exists, or it is refused

### Requirement: Applied changes are logged
Each approved proposal SHALL add a change-log entry naming the proposal, route, kind of change, numbers involved, approver and time. These entries are post-v6 records, distinct from the imported pre-v6 history.

#### Scenario: Log after approval
- **WHEN** a RETIRE proposal is approved
- **THEN** the change log gains one post-v6 entry naming the retired route, its numbers and the approver

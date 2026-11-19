# ADR 0005: Persist generation attempts around model calls

**Status:** Accepted

## Context

Model generation is nondeterministic, can outlive request cancellation, and can fail
after incurring provider work. Holding a database transaction open during a model call
would couple database resources to unpredictable network latency. Repeated submissions
and explicit retries must not create ambiguous or duplicate business records.

## Decision

PostgreSQL is the canonical store for support interactions and generation attempts.
Record a started attempt in a short transaction before generation, run the model with
no database transaction open, and record the terminal outcome in a second transaction.

Use a submission UUID as the authenticated request's idempotency key. Exact repeats
replay the stored outcome; conflicting reuse is rejected. A retry uses a new submission
UUID and names one eligible failed attempt. Store successful draft and evidence
provenance, but store only a stable category for failures rather than provider exception
details. Interactions become deletion-eligible 30 days after initial acceptance.

## Rationale

Separate transactions preserve evidence that work started while avoiding long-lived
locks and connections around external inference. Explicit idempotency and retry links
make repeated billable work distinguishable and recoverable. Safe failure categories
support operations without retaining provider or credential details, and a fixed
retention deadline gives cleanup a deterministic application-owned boundary.

# ADR 002 – Immutable Message Model

Date: 2026-02-28  
Status: Accepted

## Context

The platform is responsible for persisting and exposing messages emitted
by multiple systems.

An early design decision was whether messages should be mutable
(allowing updates or deletions) or treated as immutable records.

Supporting mutability would require:
- update and delete semantics
- concurrency control
- conflict resolution
- complex operational guarantees

These concerns would significantly increase system complexity
without being strictly required for the intended use cases.

## Decision

All messages handled by the platform are **immutable** and **append-only**.

Once a message is successfully accepted and persisted:
- it is never modified
- it is never deleted
- it remains available for retrieval as originally stored

Corrections or changes must be represented as **new messages**,
not as mutations of existing ones.

## Consequences

### Positive
- Simplifies consistency and correctness guarantees
- Enables straightforward idempotent ingestion
- Simplifies storage design and access patterns
- Makes operational behavior predictable and auditable
- Aligns with event-based and log-oriented platform services

### Negative
- Incorrect or malformed data cannot be corrected in place
- Consumers must handle superseding or compensating events
- Storage growth must be managed operationally

These trade-offs are accepted to prioritize system simplicity,
reliability and long-term operational clarity.

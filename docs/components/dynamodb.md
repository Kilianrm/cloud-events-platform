# Persistence Component – DynamoDB Implementation

## Overview

This document describes the DynamoDB-based implementation of the
**Persistence Component** defined in the system architecture.

The Persistence Component is responsible for providing durable, immutable,
append-only storage for all accepted messages and acts as the system’s
authoritative source of truth.

This document focuses exclusively on **implementation details** and
operational behavior.

---

## Table Design

A single DynamoDB table is used in the initial implementation.

### Primary Key
- **Partition Key**: `event_id`

No sort key is defined.

This design enforces a one-to-one mapping between an event identifier
and a persisted message.

---

## Access Patterns

### Write Event by Identifier
- A new event is written using a conditional `PutItem`.
- The operation succeeds only if the item does not already exist.

This enforces idempotent writes and prevents accidental overwrites.

### Read Event by Identifier
- Events are retrieved using a direct `GetItem` by primary key.
- No scan or query operations are supported.

No additional access patterns are supported.

---

## Idempotency Strategy

Idempotency is enforced at the storage layer using DynamoDB conditional writes.

- Writes use a `ConditionExpression` that asserts non-existence of the item.
- Duplicate writes with the same identifier result in a conditional check failure.
- The persistence layer never mutates existing items.

The mapping of storage-level errors to API responses is handled by the
ingestion Lambda.

---

## Consistency Model

Strongly consistent reads are used for direct lookups by primary key.

This guarantees read-after-write consistency for successfully accepted
messages and ensures that clients can immediately retrieve an event
after a successful write.

---

## Immutability Enforcement

Immutability is enforced through a combination of design and operational constraints:

- No update operations are implemented
- No delete operations are implemented
- IAM permissions restrict write access to `PutItem` only
- Application logic does not expose mutation paths

Once written, items are never modified or removed.

---

## Indexing Strategy

No secondary indexes are defined.

- No GSIs
- No LSIs

All supported access patterns are satisfied by the primary key.
Analytical or exploratory queries are explicitly out of scope.

---

## Limits & Constraints

- Maximum item size: DynamoDB limits apply
- No support for batch writes or reads
- Hot partition risks are considered acceptable due to the expected
  natural distribution of event identifiers
- No TTL-based expiration is configured

These constraints are intentional and aligned with the current system scope.

---

## Operational Considerations

- DynamoDB provides automatic scaling and high availability
- Point-in-time recovery (PITR) may be enabled for data protection
- Backup and restore behavior follows standard DynamoDB guarantees
- Failure modes are limited to write rejections or read failures

The persistence layer does not expose domain-specific metrics directly.

---

## Alternatives Considered

Alternative storage options considered include:
- Object storage (e.g. S3)
- Relational databases
- Event log–based systems

DynamoDB was selected due to its durability guarantees, scalability model,
and support for conditional writes.

Further rationale is documented in the relevant decision records.

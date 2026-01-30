# ADR 003 – Primary Storage Selection

Date: 2026-02-28  
Status: Accepted

## Context

The platform requires a primary persistence layer to store immutable,
append-only events and act as the system of record.

The storage solution must:
- support write-once semantics
- provide strong durability guarantees
- allow efficient retrieval by identifier
- enable idempotent ingestion without complex coordination
- align with a serverless, low-operations architecture

Advanced querying, analytics and bulk access patterns are explicitly
out of scope for the initial version.

## Decision

Amazon DynamoDB is selected as the primary persistence layer for the platform.

DynamoDB provides a fully managed, serverless key-value store that aligns
with the platform’s core requirements:
- immutable, append-only writes using conditional operations
- strong durability and availability guarantees
- efficient access by primary key
- native support for idempotent ingestion semantics

This choice allows the platform to deliver clear guarantees while keeping
the initial implementation simple and operationally lightweight.

## Consequences

### Positive
- Simple storage model with minimal operational overhead
- Clear alignment with idempotent ingestion semantics
- Predictable access patterns and performance
- Natural fit for a serverless architecture

### Negative
- Limited querying capabilities
- No native support for analytical workloads
- Storage growth must be managed intentionally

These limitations are accepted to preserve system simplicity
and focus on core guarantees.

## Alternatives Considered

- **Amazon S3**  
  Offers strong durability and low cost, but complicates synchronous
  ingestion flows and efficient retrieval by identifier.

- **Hybrid (DynamoDB + S3)**  
  Could support higher throughput and archival use cases, but is deferred to avoid unnecessary complexity.

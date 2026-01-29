# Service Contract

## Purpose

This service provides a centralized, platform-level capability to ingest
and retrieve immutable operational events emitted by multiple systems.

The service is intentionally designed with minimal business logic in order
to focus on infrastructure design, scalability, durability and operational
concerns.

It simulates an internal platform service in a real-world cloud environment.

---

## Event Definition

An event represents something that has occurred in a system and is recorded
without modification by this service.

An event MUST conform to the logical Event model defined in the
[Data Model documentation](data-model.md)




## Field Semantics (Service-Level Meaning)

- event_id  
  Globally unique identifier for the event.  
  Used to guarantee idempotent ingestion.

- event_type  
  Logical classification of the event
  (e.g. SERVICE_ERROR, JOB_FINISHED).

- source  
  Identifier of the emitting system
  (e.g. auth-service, billing-service).

- timestamp  
  Time at which the event actually occurred.  
  This is distinct from the ingestion time.

- payload  
  Arbitrary JSON object containing event-specific data.  
  The payload is not interpreted or modified by the service.

---

## Business Rules

### Validation

An event is considered valid if:

- All required fields are present
- The payload is valid JSON
- The total event size does not exceed the configured maximum
- The timestamp is not unreasonably far in the future

Invalid events are rejected and are not persisted.

---

### Idempotency

- Events are uniquely identified by event_id
- Submitting the same event_id multiple times does not create duplicate records
- Repeated submissions result in a consistent outcome

---

## Guarantees

If an event is accepted by the service:

- It is durably persisted
- It will not be modified or deleted
- It can be retrieved by its identifier
- Re-ingesting the same event_id will not create duplicates

The service provides at-least-once ingestion semantics.

The service does NOT guarantee event ordering.

---

## Non-Goals

The service explicitly does NOT provide:

- Payload enrichment or transformation
- Event correlation or aggregation
- Analytical or reporting capabilities
- Domain-specific authorization logic

These concerns are intentionally left out of scope to keep the core platform
simple and stable.

---

## Limits

- Maximum event size: 256 KB
- Payload must be JSON-serializable
- No guarantees are provided beyond the documented access patterns

---

## Supported Capabilities (v1)

- Accept immutable events
- Retrieve a single event by its identifier

Future capabilities may be added outside the core contract.

---

## Versioning

This document defines version v1 of the service contract.

Backward-incompatible changes will result in a new major version of the
service contract.

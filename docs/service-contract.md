# Service Contract

## Purpose

This service provides a centralized platform-level capability to ingest and query operational events emitted by multiple systems.

The service is intentionally designed with minimal business logic in order to focus on infrastructure design, deployment automation, scalability and operational concerns.

It simulates an internal platform service in a real-world cloud environment.

---

## Event Definition

An **event** represents something that has occurred in a system and is recorded without modification by this service.

### Required Fields

Each event must contain the following fields:

```json
{
  "event_id": "string",
  "event_type": "string",
  "source": "string",
  "timestamp": "ISO-8601 string",
  "payload": {}
}
```

### Field Semantics

- **event_id**
  - Globally unique identifier for the event.
  - Used to guarantee idempotency.

- **event_type**
  - Logical classification of the event (e.g. `SERVICE_ERROR`, `JOB_FINISHED`).

- **source**
  - Identifier of the emitting system (e.g. `auth-service`, `billing-service`).

- **timestamp**
  - Time at which the event actually occurred.
  - Not the ingestion time.

- **payload**
  - Arbitrary JSON object containing event-specific data.
  - Not interpreted or modified by the service.

---

## Business Rules

### Validation

- All required fields must be present.
- Payload must be valid JSON.
- Events exceeding the maximum allowed size are rejected.
- Timestamps significantly in the future are rejected.

Invalid events result in a **400 Bad Request** response.

---

### Idempotency

- Events are uniquely identified by `event_id`.
- Submitting the same `event_id` multiple times does not create duplicate records.
- Repeated submissions return a consistent response.

---

## Guarantees

- **Durability**: once an event is successfully accepted, it will not be lost.
- **At-least-once ingestion** semantics.
- The service does **not** guarantee event ordering.

---

## Non-Goals

The service explicitly does **not**:

- Perform authentication of end users.
- Enrich or transform event payloads.
- Correlate or aggregate events.
- Provide analytics or reporting capabilities.

These concerns are intentionally left out of scope to keep the service focused on platform responsibilities.

---

## Limits

- Maximum event size: **256 KB**
- Payload must be JSON-serializable.
- No guarantees are provided regarding query performance beyond documented access patterns.

---

## Supported Use Cases (MVP)

- Register a new event.
- Retrieve a single event by `event_id`.
- (Future) Query events by type or source.

---

## Versioning

This document describes the **v1.0 service contract**.

Changes to the contract will be documented and versioned as the service evolves.

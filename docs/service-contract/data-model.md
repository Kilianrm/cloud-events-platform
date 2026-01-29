# Data Model

## Overview

This document defines the logical data model for events accepted
by the platform in v1.

It describes the structure and meaning of the data exposed by the
service, independently of storage, infrastructure, or transport.

Behavioral guarantees are defined by the service contract.

---

## Event

An Event represents a single immutable message recorded by the platform.

---

## Identifiers

### event_id
- Type: string
- Scope: global

Unique identifier assigned by the event producer.
Used to reference the event across the platform.

---

## Attributes

### event_type
- Type: string

High-level classification of the event.

---

### source
- Type: string

Identifier of the system that emitted the event.

---

### timestamp
- Type: string (ISO-8601)

Time at which the event occurred at the source system.

---

### payload
- Type: JSON object (opaque)

Arbitrary, message-specific content.
The platform does not interpret the payload.

---

### ingestion_time
- Type: string (ISO-8601)

Timestamp assigned by the platform when the event is accepted.

This field is system-generated and read-only.

---

## Notes

- The data model does not impose any schema on the payload content
- No assumptions are made about relationships between events

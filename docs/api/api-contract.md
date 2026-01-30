# API Contract (HTTP)

## Overview

This document defines the HTTP API exposed by the service.

It specifies endpoints, request and response formats, status codes,
and error semantics for the HTTP interface.

This document complements the service-level contract.


---

## Base URL

All endpoints described in this document are under:

/

---

## Content Type

- Requests MUST use Content-Type: application/json
- Responses are returned as application/json

---

## Write API

### POST /events

Registers a new event for durable persistence.

The request body MUST conform to the event definition described
in the service contract.

---

### Request Body
```json
{
  "event_id": "string",
  "event_type": "string",
  "source": "string",
  "timestamp": "ISO-8601 string",
  "payload": {}
}
```

---

### Responses

#### ✅ 201 Created

The event was successfully accepted and persisted.
```json
{
  "event_id": "string",
  "status": "accepted"
}
```
---

#### ✅ 200 OK (Idempotent Write)

An event with the same event_id already exists.
No new record was created.
```json
{
  "event_id": "string",
  "status": "already_exists"
}
```
---

#### ❌ 400 Bad Request

The request is malformed or violates the service contract.

Example causes:
- Missing required fields
- Invalid JSON payload
- Invalid timestamp format
```json
{
  "error": "InvalidEvent",
  "message": "Missing required field: event_type"
}
```

---

#### ❌ 413 Payload Too Large

The request exceeds the maximum allowed size.

```json
{
  "error": "PayloadTooLarge",
  "message": "Event payload exceeds the maximum allowed size"
}
```

---

#### ❌ 500 Internal Server Error

An unexpected internal error occurred.

```json
{
  "error": "InternalError",
  "message": "An unexpected error occurred"
}
```

---

## Read API

### GET /events/{event_id}

Retrieves a previously accepted event by its identifier.

---

### Path Parameters

- event_id (string)  
  Globally unique identifier of the event.

---

### Responses

#### ✅ 200 OK

The event exists and is returned exactly as stored.

```json
{
  "event_id": "string",
  "event_type": "string",
  "source": "string",
  "timestamp": "2026-03-01T12:00:00Z",
  "payload": {},
  "ingestion_time": "2026-03-01T12:00:05Z"
}
```

---

#### ❌ 404 Not Found

No event exists with the given identifier.
```json
{
  "error": "EventNotFound",
  "message": "Event with the given identifier does not exist"
}
```

---

#### ❌ 500 Internal Server Error
```json
{
  "error": "InternalError",
  "message": "An unexpected error occurred"
}
```

---

## Error Model

All error responses follow a consistent structure:
```json
{
  "error": "string",
  "message": "string"
}
```

- error is a stable, machine-readable identifier
- message is intended for human readability

---

## Idempotency Semantics

- The API enforces idempotency based on event_id
- Repeated submissions with the same identifier do not create duplicates
- Idempotent writes return a successful response

---

## Limits

- Maximum request size: 256 KB
- Only JSON payloads are supported
- No bulk operations are supported

---

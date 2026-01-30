# Ingestion Lambda

## Overview

The Ingestion Lambda is responsible for handling incoming event
ingestion requests routed from the API Gateway.

It implements the service-level ingestion semantics defined in the
Service Contract and enforces validation, idempotency, and persistence
rules.

This component is stateless and does not maintain any internal state
between invocations.

---

## Responsibilities

The Ingestion Lambda is responsible for:

- Validating incoming events according to the Service Contract
- Enforcing idempotent ingestion semantics
- Persisting accepted events to the Persistence component
- Producing responses consistent with the API Contract

The Ingestion Lambda is NOT responsible for:

- Request routing or protocol handling
- Authentication or authorization
- Business logic beyond contract enforcement
- Event transformation or enrichment

---

## Input

The Lambda receives requests from the API Gateway using proxy integration.

The request payload represents an event submission as defined in the
API Contract.

---

## Processing Flow

For each invocation, the Ingestion Lambda performs the following steps:

1. Parse the incoming request body
2. Validate required event attributes and basic constraints
3. Enforce idempotency based on `event_id`
4. Persist the event to the Persistence component
5. Produce an appropriate success or error response

---

## Validation Rules

The following validations are performed:

- All required event attributes are present
- Payload is valid JSON
- Total event size does not exceed the configured limit
- Timestamp is not unreasonably far in the future

Validation failures result in the event being rejected
and not persisted.

---

## Idempotency Handling

- The Ingestion Lambda uses `event_id` as the idempotency key
- A conditional write is used when persisting the event
- If an event with the same `event_id` already exists:
  - No new record is created
  - A successful idempotent response is returned

Idempotency guarantees are defined by the Service Contract.

---

## Persistence Interaction

The Ingestion Lambda writes accepted events to the Persistence component.

- Writes are append-only
- No updates or deletes are performed
- The Lambda does not perform read-before-write checks

Persistence failures result in the request failing.

---

## Error Handling

The Ingestion Lambda distinguishes between:

- Validation errors
- Idempotent re-submissions
- Persistence or internal errors

All responses are returned according to the API Contract.

---

## Scaling and Concurrency

- The Lambda is designed to scale horizontally
- Concurrent invocations may process different events simultaneously
- Idempotency guarantees ensure correctness under concurrency

---

## Relationship to Other Components

- Invoked by: API Gateway
- Persists data to: Persistence component
- Implements: Service Contract ingestion semantics

# Read Lambda

## Overview

The Read Lambda is responsible for retrieving previously accepted
events from the Persistence component.

It implements the read semantics defined in the Service Contract
and exposes them through the API Gateway.

---

## Responsibilities

The Read Lambda is responsible for:

- Retrieving events by identifier
- Returning events exactly as stored
- Producing responses consistent with the API Contract

The Read Lambda is NOT responsible for:

- Querying or filtering events
- Aggregating or correlating data
- Performing business logic
- Modifying stored events

---

## Input

The Lambda receives requests from API Gateway using proxy integration.

The request includes the event identifier as a path parameter.

---

## Processing Flow

For each invocation, the Read Lambda performs the following steps:

1. Extract the event identifier from the request
2. Query the Persistence component by primary key
3. Return the event if found
4. Return a not-found response if no event exists

---

## Persistence Interaction

- Events are retrieved using a direct key lookup
- Strongly consistent reads are used
- No scans or secondary access patterns are performed

---

## Response Semantics

- If the event exists, it is returned exactly as stored
- If no event exists, a not-found response is returned
- No partial responses are supported

---

## Error Handling

The Read Lambda distinguishes between:

- Event not found
- Persistence or internal errors

All error responses are returned according to the API Contract.

---

## Observability

The Read Lambda emits:

- Structured logs for each invocation
- Metrics for successful and failed reads
- Error logs for persistence failures

---

## Scaling and Concurrency

- The Lambda scales horizontally with demand
- Read operations are independent and stateless

---

## Relationship to Other Components

- Invoked by: API Gateway
- Reads data from: Persistence component
- Implements: Service Contract read semantics

---

## Versioning

This document describes the Read Lambda behavior
for service version v1.

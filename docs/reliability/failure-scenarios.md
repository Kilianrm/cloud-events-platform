# Failure Scenarios – v1.3 Reliability & Failure Handling

## Purpose
This document defines the expected failure scenarios for the event ingestion and read platform and the corresponding system behavior.

The objective of version 1.3 is to make failure handling explicit, safe, and predictable without introducing unnecessary complexity.

Event processing involves two main Lambdas: 
- **Validation Lambda**: validates incoming event metadata and rejects invalid payloads.
- **Ingest Lambda**: enforces idempotency and performs minimal internal processing before persisting events.

Transient failures and retries are managed through **SQS queues** with configured retry policies, and unrecoverable events are sent to a **Dead Letter Queue (DLQ)**.

## 1. Timeout / Transient Failure

### Description
The consumer or downstream service cannot complete the operation within the expected time.

Examples:
- Lambda timeout
- Temporary network issues
- AWS service temporary unavailability

### Handling
- Retry enabled via SQS/Lambda configuration
- Maximum retries: 3 (exponential backoff with jitter)
- If retries are exhausted, event is automatically sent to **DLQ**
- Failures are logged in CloudWatch for operational monitoring

## 2. Invalid Payload

### Description
The received event does not meet minimal validation requirements.

Examples:
- Missing required fields (event_id, timestamp)
- Malformed JSON
- Incorrect field types

### Handling
- **Validation Lambda** rejects the event
- Event is **not retried**
- Event is **not sent to DLQ**
- Validation errors are logged in CloudWatch
- Alerts are triggered for operational visibility

## 3. Duplicate Event

### Description
The same event is delivered more than once due to retry semantics or at-least-once delivery guarantees.

### Handling
- **Ingest Lambda** checks idempotency using `event_id` in DynamoDB
- If already processed, the event is ignored
- Duplicate detection is logged for audit purposes
- No DLQ entry is created

## 4. Max Retries Exceeded

### Description
The event continues to fail after the maximum number of retries (configured in SQS/Lambda).

### Handling
- Stop retrying
- Event is automatically routed to **DLQ**
- Monitoring alert is triggered in CloudWatch to notify operations

## 5. Downstream Dependency Unavailable

### Description
A dependent service is temporarily unavailable during processing.

Examples:
- Database unavailable
- Queue access failure
- External API unavailable

### Handling
- Retry enabled via SQS/Lambda retry policy
- Maximum retries: 3
- If retries are exhausted, event is sent to **DLQ**
- Failures and retries are logged for monitoring and operational visibility

## Reliability Principles

The system follows the following principles:

- At-least-once delivery
- Idempotent event processing
- Explicit retry semantics managed via SQS/Lambda configuration
- Dead-letter queue for unrecoverable failures
- Minimal internal metadata (ingestion timestamp, processing status, Lambda ID) added for auditing
- All failures and retries are logged in CloudWatch for operational monitoring
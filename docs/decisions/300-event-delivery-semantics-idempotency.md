# 2026-04-04: Event Delivery Semantics & Idempotency

## Status
Accepted

## Context
The event ingestion and read platform must process events reliably, even when transient failures or retries occur.  
Challenges to address:

- Retries due to timeouts or transient failures may cause duplicate events.
- Invalid or failed messages need to go to a DLQ.
- Data consistency must be maintained without impacting performance.
- External consumers depend on predictable delivery semantics.

## Decision
The following strategy is adopted:

- **Delivery Semantics:** At-least-once  
  Each event may be delivered more than once, but no event will be lost.

- **Idempotency:**  
  Each consumer must validate the `event_id` and **ignore duplicate events**.

- **Retries:**  
  Maximum 3 attempts with **exponential backoff + jitter**.  
  If retries are exhausted, the event is sent to the DLQ.

- **DLQ Handling:**  
  Permanently failed messages are sent to the DLQ, and monitoring alerts are triggered.

## Consequences

- **Positive:**  
  - Prevents loss of critical events.  
  - Avoids duplicate processing in consumers.  
  - Makes retry and DLQ policies explicit.  
  - Improves traceability and monitoring.

- **Negatives / Trade-offs:**  
  - Requires temporary storage to record `event_id` for idempotency checks.  
  - Delivery is not exactly-once, which may be relevant in very strict financial scenarios (but at-least-once + idempotency is generally sufficient).

- **Operational:**  
  - Alerts for messages in DLQ are required.  
  - Clear documentation of delivery semantics is needed for any consumer.

## Alternatives Considered

1. **Exactly-once delivery:**  
   - Pros: completely avoids duplicates.  
   - Cons: high complexity, significant overhead, difficult in distributed systems like SQS/Lambda.

2. **At-most-once delivery:**  
   - Pros: simple, no duplicates.  
   - Cons: risk of lost events, does not tolerate transient failures.

**Rationale:**  
- At-least-once delivery combined with idempotent consumers balances reliability and complexity optimally for this version.
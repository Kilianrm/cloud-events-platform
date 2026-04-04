"""
# Reliability Flow – v1.3

## Failure Scenarios Mapping

| Scenario | Retry | Max Retries | DLQ | Idempotency Required | Notes |
|----------|-------|------------|-----|--------------------|-------|
| Timeout / Transient Failure | ✅ | 3 | ✅ (if retries exhausted) | ✅ | Exponential backoff + jitter |
| Invalid Payload | ❌ | 0 | ✅ | ❌ | Validation failure, cannot retry |
| Duplicate Event | ✅ (safe) | 0 | ❌ | ✅ | Already processed → ignore |
| Max Retries Exceeded | ❌ | 3 | ✅ | ✅ | Alert triggered |
| Downstream Dependency Unavailable | ✅ | 3 | ✅ (if retries exhausted) | ✅ | Handles temporary failures of DB/API |

---

## Event Processing Flow Diagram

```mermaid
flowchart TD
    A[Event received] --> B{Valid payload?}
    B -- No --> C[Send to DLQ & Log]
    B -- Yes --> D{Already processed?}
    D -- Yes --> E[Ignore & Log duplicate]
    D -- No --> F[Process event]
    F --> G{Success?}
    G -- Yes --> H[Ack / Done]
    G -- No --> I{Retries left?}
    I -- Yes --> J[Retry with backoff]
    I -- No --> K[Send to DLQ & Alert]
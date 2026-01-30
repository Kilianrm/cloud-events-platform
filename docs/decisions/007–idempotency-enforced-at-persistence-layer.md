## 2026-02-28 – Idempotency Enforced at Persistence Layer

**Decision**  
Enforce idempotent ingestion at the persistence layer using conditional writes.

**Reasoning**  
Idempotency is a correctness guarantee, not a transport concern.

By enforcing it at the storage layer:
- concurrent writes are handled safely
- retries do not introduce duplicates
- no read-before-write logic is required

This ensures correctness even under retries, timeouts or parallel invocations.

**Alternatives Considered**
- Idempotency handled at API Gateway
- Application-level read-before-write checks
- External locking mechanisms

All were rejected due to race conditions or unnecessary complexity.

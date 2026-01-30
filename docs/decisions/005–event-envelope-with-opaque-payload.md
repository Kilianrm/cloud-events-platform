## 2026-02-28 – Event Envelope with Opaque Payload

**Decision**  
Define a strict event envelope while treating the event payload as opaque data.

**Reasoning**  
The platform provides strong guarantees around ingestion, durability and
immutability without coupling itself to domain-specific schemas.

By fixing the envelope semantics and leaving the payload uninterpreted:
- the core system remains stable
- producers retain full flexibility
- schema evolution is pushed to the edges

This mirrors real-world internal platform services, where infrastructure
concerns are separated from domain concerns.

**Alternatives Considered**
- Enforcing payload schemas at the platform level
- Supporting multiple event shapes

Both alternatives were rejected to avoid premature coupling and complexity.

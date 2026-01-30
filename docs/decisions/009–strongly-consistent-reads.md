## 2026-02-28 – Strongly Consistent Reads

**Decision**  
Use strongly consistent reads when retrieving events.

**Reasoning**  
The platform guarantees that once an event is accepted, it can be immediately
retrieved.

Strong consistency:
- avoids surprising client behavior
- simplifies the mental model
- aligns with durability guarantees

The cost trade-off is acceptable given the limited access patterns.

**Alternatives Considered**
- Eventually consistent reads

Rejected due to weaker guarantees.

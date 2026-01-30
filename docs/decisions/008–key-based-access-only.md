## 2026-02-28 – Key-Based Access Only

**Decision**  
Restrict data access to direct lookups by event identifier.

**Reasoning**  
Supporting queries, scans or secondary access patterns would:
- complicate the data model
- introduce performance ambiguity
- expand the API surface prematurely

Limiting access patterns keeps system guarantees explicit and enforceable.

**Alternatives Considered**
- Secondary indexes for querying by type or source
- Search-oriented storage solutions

Deferred until concrete requirements emerge.

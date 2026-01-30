## 2026-02-28 – Synchronous HTTP API

**Decision**  
Expose the service via a synchronous HTTP API.

**Reasoning**  
Synchronous request/response semantics:
- simplify client integration
- make durability guarantees explicit
- reduce operational complexity

This approach provides clear feedback to clients on ingestion outcomes.

**Alternatives Considered**
- Asynchronous ingestion via queues or streams

Deferred until concrete throughput or latency constraints are observed.
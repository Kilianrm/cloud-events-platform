## 2026-02-28 – Separate Ingestion and Read Compute Paths

**Decision**  
Use separate Lambda functions for ingestion and read operations.

**Reasoning**  
Write and read paths have different responsibilities, failure modes and
scaling characteristics.

Separating them:
- simplifies each component’s logic
- avoids accidental coupling
- allows independent operational behavior

This separation improves clarity and mirrors production-grade service design.

**Alternatives Considered**
- Single Lambda handling all API operations

Rejected due to increasing complexity and mixed responsibilities.

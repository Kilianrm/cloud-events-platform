# Architectural Decisions

## 2026-02-28 – Project Scope Definition

**Decision**  
Focus on a platform-level service with minimal business logic.

**Reasoning**  
Allows deeper focus on cloud architecture, infrastructure, deployment automation and operations.

---

## 2026-02-28 – Immutable Message Model

**Decision**  
All messages handled by the platform are immutable and append-only.

**Reasoning**  
Immutability simplifies consistency guarantees, storage design and operational behavior,
while aligning with real-world internal platform services.

---
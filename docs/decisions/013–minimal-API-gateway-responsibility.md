## 2026-02-30 – Minimal API Gateway Responsibility

**Decision**  
Limit API Gateway responsibilities to routing and protocol handling.

**Reasoning**  
Keeping API Gateway thin:
- preserves clear system boundaries
- avoids hidden business logic
- keeps correctness and validation in compute components

This prevents tight coupling to gateway-specific features.

**Alternatives Considered**
- Request validation at gateway level
- Gateway-based transformations
- Early introduction of throttling or auth mechanisms

Deferred to future iterations if required.

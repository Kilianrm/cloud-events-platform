## 2026-02-28 – Primary API Gateway Strategy

**Decision**  
Use Amazon API Gateway HTTP API for v1.

**Reasoning**  
HTTP API provides a simpler and more cost-effective integration suitable for
the limited scope of v1.

Future iterations (v2) may migrate to REST API in order to explore advanced
gateway features and compare trade-offs.

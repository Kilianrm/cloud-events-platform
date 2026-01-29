## 2026-02-28 – Primary Storage Selection

**Decision**  
Use Amazon DynamoDB as the primary persistence layer for v1.

**Reasoning**  
DynamoDB provides a fully managed, serverless key-value store that aligns with the
platform’s core requirements:
- immutable, append-only writes
- strong durability guarantees
- efficient access by identifier
- native support for idempotent ingestion

It allows the platform to deliver clear guarantees while keeping the v1
implementation simple and cost-effective.

**Alternatives Considered**
- **Amazon S3**: offers strong durability and low cost but complicates synchronous
  ingestion and efficient lookups by identifier.
- **Hybrid (DynamoDB + S3)**: deferred to future iterations to avoid unnecessary
  complexity in v1.
## Cloud Mapping

This section describes how logical components are realized using AWS services.
These mappings are implementation choices and may evolve independently from
the logical architecture.

| Logical Component | AWS Service |
|------------------|-------------|
| Ingestion Interface      | API Gateway |
| Read Interface   | API Gateway + Lambda |
| Validation       | Lambda |
| Persistence      | DynamoDB |
| Observability    | CloudWatch |

---

### Persistence Component

The Persistence Component is implemented using Amazon DynamoDB.

DynamoDB is used to support the required durability, immutability and
idempotency guarantees of the persistence component.

Detailed storage design is documented in:
- [Persistence Component – DynamoDB](../components/dynamodb.md)


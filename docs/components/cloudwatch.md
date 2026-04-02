# Observability Component – CloudWatch

## Purpose
The Observability Component provides **monitoring, logging, and operational visibility** for the system.  
It allows the team to understand system behavior, detect failures, and track usage **without affecting business logic or data flows**.

## Responsibilities
- Capture **structured logs** from all Lambda functions and API Gateway  
- Maintain **log retention policies**  
- Derive **metrics from logs** via CloudWatch metric filters  
- Enable **request tracing** via `correlation_id` and `event_id`  

## Implementation
The component is implemented using **Amazon CloudWatch**, with the following elements:

### Logging
- Structured logs emitted from each Lambda function:
- Log groups per function:

| Lambda / Service        | Log Group Name |
|-------------------------|----------------|
| Ingestion Lambda        | `/aws/lambda/ingestion-${ENV}` |
| Read Lambda             | `/aws/lambda/read-${ENV}` |
| Authentication Lambda   | `/aws/lambda/authentication-${ENV}` |
| Authorization Lambda    | `/aws/lambda/authorization-${ENV}` |
| API Gateway             | `/api-gateways/api-gateway-${ENV}` |

- Retention: **7 days**  
- Log entries include at least:  
  - `message` (text description)  
  - `level` (info / warning / error)  
  - `correlation_id` (to trace requests across functions)  
  - `event_id` (if available)  
  - Optional: `method`, `path`, `client_id`, `effect`, `token_preview`  

### Metrics
CloudWatch metric filters extract metrics from logs. **All metrics use `Count` units**.  

Tracked metrics:

- **Ingestion Lambda**
  - `RequestsAccepted` → logs with `status = "accepted"`  
  - `RequestsRejected` → logs with `status = "rejected"`  

- **Read Lambda**
  - `RequestsAccepted` → logs with `status = "accepted"`  
  - `RequestsRejected` → logs with `status = "rejected"`  

- **Authentication Lambda**
  - `AuthenticationSuccess` → logs with `status = "validated"`  
  - `AuthenticationRejected` → logs with `status = "rejected"`  

- **Authorization Lambda**
  - `AuthorizationAllow` → logs with `status = "authorized"` and `effect = "Allow"`  
  - `AuthorizationDeny` → logs with `status = "denied"`  

These metrics are **available for dashboards and alerting**.

### Correlation
- `correlation_id` is propagated from **API Gateway** or generated per request  
- Enables **tracing of a request** across all logs and metrics  
- Can be used to **investigate issues** or analyze request flows end-to-end  

### Non-Goals
- Business logic execution  
- Payload validation or transformation  
- Event persistence (handled by DynamoDB)  
- API contract enforcement (handled by Lambda / API Gateway)  

### Trade-offs
- Slight increase in **log volume**  
- Additional **CloudWatch resources** (log groups, metrics)  
- Retention and metric costs are **minimal but non-zero**  
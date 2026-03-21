# Observability Component – CloudWatch

## Purpose
The Observability Component provides **monitoring, logging, and operational visibility** for the system.  
It allows the team to understand system behavior, detect failures, and track usage **without affecting business logic or data flows**.

## Responsibilities
- Capture structured logs from Lambda functions
- Maintain log retention policies
- Derive metrics from logs via CloudWatch metric filters
- Enable request tracing via `correlation_id` and `event_id`

## Implementation
The component is implemented using **Amazon CloudWatch**, with the following elements:

### Logging
- Structured logs emitted by Lambda functions (JSON format)
- Log groups per function:
  - `/aws/lambda/ingestion-lambda-${ENV}`
  - `/aws/lambda/read-lambda-${ENV}`
- Retention: 7 days
- Log entries include:
  - `message`
  - `level` (info / error)
  - `correlation_id`
  - `event_id` (when available)

### Metrics
- CloudWatch metric filters extract metrics from logs
- Tracked metrics:
  - Accepted requests
  - Rejected requests
- Metrics are available for dashboards and alerting

### Correlation
- `correlation_id` is propagated from API Gateway or generated per request
- Enables tracing of a request across all logs and metrics

## Non-Goals
- Business logic execution
- Payload validation or transformation
- Event persistence (handled by DynamoDB)
- API contract enforcement (handled by Lambda/API Gateway)

## Trade-offs
- Slight increase in log volume
- Additional CloudWatch resources (log groups, metrics)
- Retention and metric costs are minimal but non-zero

## Observability Flow
``` 
Request → ApiGateway -> Lambda → Structured Logs → CloudWatch Logs → Metric Filters
```
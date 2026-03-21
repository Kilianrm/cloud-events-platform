# [ADR] 2026-03-20 – Introduce Observability with CloudWatch

## Status
Accepted

## Context / Observed Problem
Once v1.0 of the system was deployed, it became clear that there was **no visibility into operational behavior**.  
Specifically, the system lacked insight into:

- Request behavior and flow
- Failure causes and error conditions
- Usage patterns and metrics

This made debugging, monitoring, and operational management difficult, slowing down issue resolution and reducing confidence in system reliability.

## Decision
Introduce an **Observability Component** implemented using **Amazon CloudWatch** to provide:

- Structured logging from all Lambda functions
- Metrics derived from logs via CloudWatch metric filters
- Dashboards and alerts for operational monitoring
- Correlation identifiers to trace requests end-to-end

The component is designed to **observe system behavior without modifying business logic**.

## Rationale
- CloudWatch is a fully managed AWS service, integrated with Lambda and API Gateway
- Provides structured logging, metrics, and alerting out-of-the-box
- Enables tracing with correlation IDs, improving debuggability
- Does not interfere with core system guarantees (immutability, durability, simplicity)
- Low operational overhead and minimal cost impact

## Consequences
- Increased log volume and additional CloudWatch resources (log groups, metrics)
- Log retention and metric costs are minimal but non-zero
- Improved operational visibility, faster debugging, and monitoring capabilities
- Future extensions (e.g., dashboards, alarms) can be added without impacting core logic

## Alternatives Considered
- **No observability** – rejected due to operational risks
- **Third-party monitoring service** – rejected to avoid additional dependencies and costs

## References
- [Observability Component – CloudWatch](../components/cloudwatch.md)
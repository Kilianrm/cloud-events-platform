# ADR 004 – API Gateway Strategy

Date: 2026-02-28  
Status: Accepted

## Context

The platform requires an HTTP entry point to expose a small number of
synchronous request/response operations.

The API layer must:
- integrate cleanly with AWS Lambda
- introduce minimal operational complexity
- keep costs proportional to low and predictable traffic
- avoid unnecessary features not required by the current scope

Advanced API management capabilities such as request modeling, usage plans,
API keys or complex authorization policies are not required at this stage.

## Decision

Amazon API Gateway **HTTP API** is selected as the API layer for the platform.

HTTP API provides:
- native Lambda proxy integration
- lower latency compared to REST API
- reduced cost and simpler configuration
- sufficient capabilities for the current request patterns

This choice aligns with the goal of keeping the v1 architecture minimal
and operationally lightweight.

## Consequences

### Positive
- Reduced cost and configuration complexity
- Faster request handling
- Clear separation between API boundary and business logic
- Simplified operational model

### Negative
- Limited support for advanced API management features
- Fewer built-in request validation and transformation capabilities

These limitations are accepted because they are not required
by the current service contract.

## Alternatives Considered

- **Amazon API Gateway – REST API**  
  Offers richer API management features, but introduces higher cost
  and configuration complexity that is not justified by the current scope.

- **Application Load Balancer (ALB)**  
  Considered but rejected due to increased operational overhead
  and weaker alignment with a fully serverless architecture.

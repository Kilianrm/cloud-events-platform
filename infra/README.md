## Infrastructure Overview

This Terraform project provisions:

- DynamoDB table for immutable event storage
- Two AWS Lambda functions:
  - ingestion: accepts and persists events
  - read: retrieves events by identifier
- HTTP API Gateway exposing:
  - POST /events
  - GET /events/{event_id}

### Design principles
- Minimal IAM permissions
- Immutable storage
- No mutation paths
- Strongly consistent reads

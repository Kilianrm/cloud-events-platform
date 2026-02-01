# Event Platform Service

Internal platform service providing a centralized capability to ingest,
persist, and expose immutable operational events.

## Overview

This repository contains the documentation and reference implementation of an
internal, serverless, cloud-native platform service used to collect and
retrieve immutable operational events emitted by multiple systems.

The service acts as an authoritative store for accepted events and is designed
to simulate a real-world internal platform deployed in a cloud environment.
Business logic and domain-specific processing are intentionally out of scope.

## Key Characteristics

- Event-centric ingestion model (events are immutable, append-only records)
- Explicit separation between write (ingestion) and read responsibilities
- Stateless HTTP APIs exposed through API Gateway
- DynamoDB used as a scalable, low-latency persistence layer
- Infrastructure fully defined and reproducible using Terraform
- Architectural decisions documented explicitly (ADRs)
- Small, intentionally limited API surface

## Project Scope

### Included in v1.0

- HTTP API for event ingestion
- HTTP API for reading stored events
- Persistence layer based on DynamoDB
- Infrastructure provisioning using Terraform
- Basic CI setup (linting, formatting, and test execution)
- Testing strategy with representative examples
- Architectural documentation and decision records (ADRs)

### Explicitly out of scope

- Production-grade deployment hardening
- Fully automated CI/CD pipelines
- Monitoring, alerting, and observability tooling
- Advanced scalability or performance tuning
- Multi-environment or multi-account AWS setups

## Repository Structure

```
infra/              # Infrastructure as Code (Terraform)
  envs/
    dev/            # Development environment entry point
    prod/           # Support production environment
docs/               # Architecture, API contracts, and design decisions
app/                # Application code (Lambda functions)
```

## Documentation

All project documentation is centralized under the `/docs` directory.

Start with [`docs/README.md`](docs/README.md), which provides a guided entry
point and links to all architecture, API, infrastructure, CI, testing, and
design decision documentation.


## Getting Started

This project can be deployed to AWS using Terraform.
The recommended entry point is the development environment.

### Prerequisites

- Terraform
- An AWS account
- AWS credentials configured locally

### Deploying the infrastructure

Initialize and apply the infrastructure from the development environment:

```
cd infra/envs/dev
terraform init
terraform apply
```

Once the deployment finishes, the following resources will be available:

- API Gateway endpoints for event ingestion and event reading
- DynamoDB table for event storage
- Associated IAM roles and permissions

Terraform outputs expose the relevant endpoints and resource identifiers.

From the `infra/envs/dev` directory, you can also validate the deployment by
running the provided test script:

```bash
../../../scripts/test_api.sh
```

The script sends a sample event, conforming to the expected event format, to
the ingestion API Gateway endpoint and then attempts to read it back through
the read API, validating the end-to-end ingestion and retrieval flow.

### Cleaning up

To remove all resources created in AWS:

```
cd infra/envs/dev
terraform destroy
```

## Versioning

The current stable version of the project is `v1.0.0`.

This release represents a closed and fully documented baseline of the system.
Future improvements and extensions are intentionally planned outside the scope
of this version.

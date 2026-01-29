# Documentation Overview

This directory contains the architectural, contractual and design
documentation for the platform.

The goal of this documentation is not only to describe *what* the system does,
but also *why* it is structured the way it is.

Although the implemented system is intentionally simple, the documentation
is designed to reflect how real-world platform services are specified,
reasoned about and evolved.

---

## Documentation Philosophy

The documentation is organized by **responsibility and abstraction level**.

Each document has a clear purpose:
- to define boundaries
- to avoid duplication
- to make future changes explicit
- to prevent implementation details from leaking into contracts

Documents are meant to be read **top-down**, from high-level architecture
to concrete components.

---

## How to Read This Documentation

### 1. Core Architecture (required)
- Architecture Overview
- Logical Components

### 2. Contracts and Guarantees
- Service Contract
- API Contract
- Data Model

### 3. Implementation Design (optional deep dive)
- Cloud Mapping
- API Gateway
- Ingestion Lambda
- Read Lambda
- Persistence (DynamoDB)


Note: Readers who are primarily interested in consuming the API may start directly from Section 2: Service Contract and Guarantees.


---

## Architecture

### Architecture Overview
High-level description of the system goals, principles, constraints
and explicit non-goals.

- [Architecture Overview](architecture/overview.md)

### Logical Components
Defines the system in terms of logical responsibilities, independently
of technology or implementation choices.

- [Logical Components](architecture/logical-components.md)

---

## Contracts

### Service Contract
Defines **what the service guarantees** and **what it explicitly does not**.

This document is authoritative for service behavior and semantics.

- [Service Contract](service-contract/service-contract.md)

### API Contract
Defines the HTTP interface exposed to clients:
endpoints, requests, responses and error semantics.

- [Api Contract](api/api-contract-v1.md)

### Data Model
Defines the **logical data model** exposed by the service contract,
independent of storage or infrastructure.

- [Data Model](service-contract/data-model.md)

---

## Component Design

### Boundary Components
Documents components that form system boundaries and interact
with external clients.


- [Api Gateway](components/api-gateway.md)

### Internal Components
Documents internal runtime components responsible for implementing
the service behavior.

- [Ingestion Lambda](components/ingestion-lambda.md)
- [Read Lambda](components/read-lambda.md)

### Storage Components
Documents persistence-related components and their design constraints.

- [DynamoDB](components/dynamodb.md)

---

## Cloud Mapping

### Cloud Mapping
Maps logical components to concrete AWS services.

This document captures **implementation choices**, not architectural constraints.

- [Cloud Mapping](architecture/cloud-mapping.md)

---

## Decisions

Decision Records (ADRs) document *why* certain
design choices were made.

These decisions provide historical context and guide future evolution.

- [Decisions](decisions)

---

## Infrastructure and Application Code

This documentation describes the system design.

Concrete implementation can be found in:
- `/infra` — Infrastructure as Code
- `/app` — Application runtime code

Those directories are expected to reflect the architecture
and contracts defined here.

---

## Intended Audience

This documentation is intended for:
- engineers implementing or extending the system
- reviewers evaluating architectural decisions
- readers interested in real-world cloud-native system design

It is also used as a learning and portfolio project to demonstrate
end-to-end system design thinking.

## Cloud Mapping

This section describes how logical components are realized using AWS services.
These mappings are implementation choices and may evolve independently from
the logical architecture.

| Logical Component | AWS Service |
|------------------|-------------|
| Ingestion Interface  | API Gateway + Lambda|
| Read Interface   | API Gateway + Lambda|
| Persistence      | DynamoDB |

---


## AWS System Architecture Map


```mermaid
flowchart LR
    Client["Client"]

    subgraph AWS["AWS Cloud"]
        APIGW["API Gateway"]
        
        subgraph Compute["Compute"]
            Ingest["Ingestion Lambda"]
            Read["Read Lambda"]
        end

        DB["DynamoDB"]
    end

    Client -->|HTTP| APIGW

    APIGW -->|POST /events| Ingest
    APIGW -->|GET /events| Read

    Ingest -->|write| DB
    Read -->|read| DB

```

## Persistence Mapping

The logical Persistence Component is mapped to Amazon DynamoDB.

DynamoDB is chosen to support the durability, immutability and
idempotency guarantees defined by the Service Contract.

This document does not describe table schemas or access patterns.

Detailed storage design is documented in:
- [Persistence Component – DynamoDB](../components/dynamodb.md)

---

## Ingestion Interface Mapping

The Ingestion Interface is implemented using AWS API Gateway
and an AWS Lambda function.

- [API Gateway](../components/api-gateway.md)
- [Ingestion Lambda](../components/ingestion-lambda.md)

## Read Interface Mapping

The Read Interface is implemented using AWS API Gateway
and an AWS Lambda function.

- [API Gateway](../components/api-gateway.md)
- [Read Lambda](../components/read-lambda.md)

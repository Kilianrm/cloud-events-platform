# Infrastructure

Infrastructure is defined using Terraform and targets AWS.  
The design follows a modular, multi-environment approach.

## Scope
- Lambda functions
- DynamoDB tables
- API Gateway
- CloudWatch

## Environments
The infrastructure is deployed to two isolated environments:
- `dev`
- `prod`

Each environment has its own Terraform state and configuration, allowing independent validation and deployment while sharing the same infrastructure definitions.

## Modules
The infrastructure is organized into reusable Terraform modules.

### `events`
The `events` module encapsulates all resources related to the event ingestion flow:
- API Gateway configuration
- Lambda ingestion function
- IAM roles and policies
- DynamoDB tables

This module is instantiated by each environment with environment-specific parameters.

## Validation
Infrastructure code is validated locally and in CI using non-destructive commands:
- `terraform fmt`
- `terraform validate`

No remote backend interaction is required during CI validation.

## Deployment
- Infrastructure is deployed manually using `terraform apply`
- Deployment requires valid AWS credentials
- Deployments are executed per environment (`dev` or `prod`)


# Testing Strategy

The project focuses testing efforts on the application layer.
Infrastructure is validated but not functionally tested.

## Application tests

### Unit tests
- Located under `app/tests/unit`
- Business logic is tested in isolation
- AWS services are mocked using `moto`
- No AWS credentials required

### Integration tests
- Validate ingestion and read flows at code level
- Lambda handlers are executed locally
- Still fully isolated from real AWS services

## Infrastructure validation

Infrastructure code is validated as part of CI but not executed.

- `terraform fmt` ensures consistent formatting
- `terraform validate` checks configuration correctness
- No infrastructure is deployed during CI
- No AWS credentials are required

## Environments

Both `dev` and `prod` environments use the same Terraform modules.
Validation applies equally to both environments.

## Rationale

- Application logic is the primary source of defects
- Terraform is declarative and validated structurally
- Avoids coupling CI to real cloud credentials
- Keeps the pipeline simple, reproducible, and safe

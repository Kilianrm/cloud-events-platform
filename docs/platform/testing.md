# Testing strategy

The project includes unit and integration tests for the application layer.

## Unit tests
- Located under app/tests/unit
- External services are mocked using moto
- No AWS credentials required

## Integration tests
- Validate ingestion flow end-to-end at code level
- Still fully isolated from real AWS services

## Local execution
Tests can be executed locally using pytest.
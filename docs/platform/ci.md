## CI Pipeline

The CI pipeline automates validation for application code and infrastructure.

### Automatic Pipeline
- **Triggers:** push to `main` and pull requests
- **Jobs:**
  - Unit tests (Python 3.11, pytest, boto3, moto, PyJWT)
  - Terraform validate & plan for `dev` and `prod` (init, fmt -check, validate)
- **Note:** No resources are deployed; validation is non-destructive.

### Manual 'CI Heavy / Integration' Workflow
- **Triggered manually** via workflow_dispatch
- **Inputs:** run_integration (yes/no), run_e2e (yes/no)
- **Job:** Integration and E2E tests
  - E2E tests run against the API Gateway defined in `tests/e2e/conftest.py`"
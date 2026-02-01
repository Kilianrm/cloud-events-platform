## CI pipeline

The CI pipeline automates validation and quality checks for both application code and infrastructure definitions.

### Jobs
- Application build and automated tests
- Infrastructure validation (formatting and static checks)

The CI pipeline does not deploy resources and does not interact with remote backends.  
Infrastructure code is validated using non-destructive commands (such as formatting and validation) to ensure consistency and correctness without requiring credentials.
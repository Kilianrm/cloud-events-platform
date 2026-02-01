## 2026-02-1 – Minimal CI Pipeline Scope

**Decision**  
Limit the CI pipeline to non-destructive validation and quality checks for
application and infrastructure code, without performing deployments or
interacting with remote backends.

**Reasoning**  
Keeping the CI pipeline intentionally simple:
- reduces operational complexity at early stages
- avoids the need for credentials and environment coupling
- focuses CI responsibilities on correctness and consistency checks
- preserves a clear separation between validation and deployment concerns

This aligns with the project's MVP scope and avoids premature automation
before deployment workflows and environments are fully defined.

**Alternatives Considered**
- Full CI/CD pipeline with automated deployments
- Infrastructure plan or apply steps against remote backends
- Environment-aware pipelines requiring AWS credentials

These alternatives were deferred to future iterations, once operational and
deployment requirements become explicit.

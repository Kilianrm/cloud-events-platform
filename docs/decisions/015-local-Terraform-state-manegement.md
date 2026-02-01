## 2026-02-30 – No Use of Terraform Cloud (HCP) for State and Execution

**Decision**  
Do not use Terraform Cloud (HCP) for managing Terraform state or executions.
State is managed using an AWS-native backend.

**Reasoning**  
For a single-contributor project, Terraform Cloud introduces additional
operational and cognitive overhead without providing proportional benefits.
Managing state directly allows:
- full control over execution flow
- simpler mental model while iterating quickly
- fewer external dependencies during early development

This keeps the infrastructure workflow transparent and easy to reason about.

**Alternatives Considered**
- Terraform Cloud with remote state and remote execution
- Hybrid model (HCP state + local execution)

Deferred to future iterations if collaboration or governance requirements
increase.

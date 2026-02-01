## 2026-01-30 – Explicit Environment Separation (dev / prod)

**Decision**  
Model infrastructure using two explicit environments: `dev` and `prod`,
each with its own Terraform configuration and isolated state.

**Reasoning**  
Although a single environment would be sufficient for the current scope,
introducing environment separation:
- enforces clear boundaries between stages
- prevents accidental cross-environment changes
- enables practicing realistic infrastructure patterns
- prepares the project for future growth and promotion workflows

The environments are modeled explicitly to favor clarity and predictability
over abstraction.

**Alternatives Considered**
- Single shared environment
- Terraform workspaces for environment separation
- Environment selection via variables

These approaches were deferred in favor of explicit directory-based separation.

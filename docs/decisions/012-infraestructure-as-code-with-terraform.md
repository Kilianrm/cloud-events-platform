## 2026-02-28 – Infrastructure as Code with Terraform

**Decision**  
Define all infrastructure using Terraform.

**Reasoning**  
Terraform enables:
- repeatable and auditable infrastructure
- clear separation between code and configuration
- controlled infrastructure evolution

This supports safe iteration and operational clarity.

**Alternatives Considered**
- Manual configuration
- CloudFormation

Rejected to maintain flexibility and consistency across environments.

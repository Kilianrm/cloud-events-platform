# Authorization Lambda

## Overview

The Authorization Lambda is responsible for handling authorization
requests routed from the API Gateway using a custom Lambda Authorizer.

It validates JSON Web Tokens (JWT), extracts identity and scope
information, and produces IAM policies that allow or deny access
to specific API Gateway resources.

This component is stateless and does not maintain any internal state
between invocations.

---

## Responsibilities

The Authorization Lambda is responsible for:

- Validating JWT tokens from incoming requests
- Verifying token signature and expiration
- Extracting identity (`sub`) and authorization data (`scope`)
- Determining access permissions based on token scope
- Generating IAM policies for API Gateway (Allow/Deny)

The Authorization Lambda is NOT responsible for:

- Request routing or protocol handling
- Authentication (credential validation or token issuance)
- Business logic beyond access control decisions
- Token persistence or session management

---

## Input

The Lambda receives requests from API Gateway as a Lambda Authorizer event.

The event typically includes:

- `Authorization`: Authorization header value (expected format: `Bearer <JWT>`)
- `methodArn`: ARN of the API Gateway method being invoked

---

## Processing Flow

For each invocation, the Authorization Lambda performs the following steps:

1. Extract the `authorization` from the event
2. Validate that the token follows the `Bearer <token>` format
3. Extract the JWT token from the header
4. Retrieve the JWT signing secret from Secrets Manager
5. Verify the JWT signature and decode the payload
6. Extract the `sub` claim as `principalId`
7. Evaluate the `scope` claim to determine access permissions
8. Generate an IAM policy (Allow or Deny) for the requested resource

---

## Validation Rules

The following validations are performed:

- Authorization header must be present
- Authorization header must start with `Bearer `
- JWT must be well-formed
- JWT signature must be valid
- JWT must not be expired

Validation failures result in access being denied.

---

## Token Verification

- The JWT is verified using a shared secret retrieved from Secrets Manager
- The verification process ensures:
  - Signature integrity (HS256)
  - Token expiration (`exp` claim)

If verification fails:
- Access is denied
- No further processing is performed

---

## Scope-Based Authorization

- The Lambda evaluates the `scope` claim from the JWT payload
- The `scope` can be a list of permissions (e.g. `["read", "write"]`)

Authorization logic:

- If the required scope (e.g. `read`) is present:
  - Effect = `Allow`
- Otherwise:
  - Effect = `Deny`

Scope evaluation is implemented in the authorization logic layer.

---

## Policy Generation

The Lambda returns an IAM policy document compatible with API Gateway.

The policy includes:

- `principalId`: Extracted from JWT `sub` claim
- `Effect`: `Allow` or `Deny`
- `Resource`: The requested `methodArn`

---

## Example Policy

```json
{
  "principalId": "client_123",
  "policyDocument": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "execute-api:Invoke",
        "Effect": "Allow",
        "Resource": "arn:aws:execute-api:region:account-id:api-id/stage/GET/resource"
      }
    ]
  }
}
```
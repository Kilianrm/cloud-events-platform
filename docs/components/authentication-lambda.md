# Authentication Lambda

## Overview

The Authentication Lambda is responsible for handling authentication
requests routed from the API Gateway.

It validates client credentials (`client_id` and `client_secret`)
against the configured secret store and issues JSON Web Tokens (JWT)
upon successful authentication.

This component is stateless and does not maintain any internal state
between invocations.

---

## Responsibilities

The Authentication Lambda is responsible for:

- Validating client credentials (`client_id` and `client_secret`)
- Retrieving and verifying credentials from the Secrets Manager
- Generating signed JWT tokens upon successful authentication
- Returning authentication responses consistent with the API Contract

The Authentication Lambda is NOT responsible for:

- Request routing or protocol handling
- Authorization or access control decisions
- Business logic unrelated to authentication
- Token persistence or session storage

---

## Input

The Lambda receives requests from the API Gateway using proxy integration.

The request payload represents an authentication request as defined in the
API Contract.

Typically, the payload includes:

- `client_id`
- `client_secret`

---

## Processing Flow

For each invocation, the Authentication Lambda performs the following steps:

1. Parse the incoming request body
2. Validate required authentication fields (`client_id`, `client_secret`)
3. Retrieve the expected credentials from the Secrets Manager
4. Compare provided credentials with stored values
5. Generate a signed JWT token if credentials are valid
6. Produce an appropriate success or error response

---

## Validation Rules

The following validations are performed:

- Required authentication fields are present
- Payload is valid JSON
- Credential values are non-empty

Validation failures result in the request being rejected.

---

## Credential Verification

- The Lambda retrieves credentials from the Secrets Manager
- The provided `client_id` and `client_secret` must match stored values
- If credentials do not match:
  - Authentication fails
  - No token is issued

The Secrets Manager acts as the source of truth for valid credentials.

---

## Token Generation

- A JWT token is generated upon successful authentication
- The token is signed using the configured signing key
- The token includes the following claims:

  - `sub`: Identifier of the client (`client_id`)
  - `scope`: Permissions or access scope granted to the client
  - `iat`: Issued-at timestamp (Unix time)
  - `exp`: Expiration timestamp (Unix time), calculated based on a configured TTL

- The expiration time is defined as:

  - `exp = iat + expire_seconds`

- The `scope` value is used by downstream components (e.g. Authorization Lambda)
  to determine access permissions

Token structure and claims are defined by the Service Contract.

---

## Example Token Payload

```json
{
  "sub": "client_123",
  "scope": ["write", "read"],
  "iat": 1710000000,
  "exp": 1710003600
}
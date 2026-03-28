# tests/test_integration_authorizer_moto.py

import pytest
import boto3
from moto import mock_aws
import os
from authorization.handler import handler
from shared.jwt_utils import generate_jwt

# --- Sample event ---
event_template = {
    "authorizationToken": "",
    "methodArn": "arn:aws:execute-api:region:account:id"
}

JWT_SECRET = "this_is_a_secure_test_secret_with_32_bytes! "
CLIENT_ID = "user123"
SCOPE = "events:read"

@pytest.fixture
def aws_env():
    """
    Prepares a mocked AWS environment using Moto for integration tests.
    Creates:
      - JWT secret in Secrets Manager
    Also sets JWT_SECRET environment variable.
    """
    os.environ["JWT_SECRET"] = JWT_SECRET
    with mock_aws():
        sm_client = boto3.client("secretsmanager")

        # JWT secret
        sm_client.create_secret(
            Name="auth/jwt_secret",
            SecretString=JWT_SECRET
        )

        yield


# --- Helper to create a JWT and event ---
def make_event(client_id, scope, secret, method_arn):
    token = generate_jwt(client_id, scope, secret)
    event = event_template.copy()
    event["authorizationToken"] = f"Bearer {token}"
    event["methodArn"] = method_arn
    return event


# --- Happy path: Allow access ---
def test_integration_allow_moto(aws_env):

    # Generate the event with a valid JWT
    event = make_event(CLIENT_ID, SCOPE, JWT_SECRET, event_template["methodArn"])

    # Call the Lambda handler (real get_jwt_secret hits moto)
    result = handler(event, None)

    # Assertions
    assert result["principalId"] == CLIENT_ID
    statement = result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Allow"
    assert statement["Resource"] == event_template["methodArn"]

# --- Deny access due to missing scope ---
def test_integration_deny_scope_moto(aws_env):
    # Use a scope that does NOT include 'events:read'
    invalid_scope = "read"

    # Generate the event with this JWT
    event = make_event(CLIENT_ID, invalid_scope, JWT_SECRET, event_template["methodArn"])

    # Call the Lambda handler
    result = handler(event, None)

    # Assertions
    assert result["principalId"] == CLIENT_ID
    statement = result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Deny"
    assert statement["Resource"] == event_template["methodArn"]

# --- Deny access due to expired JWT ---
def test_integration_expired_jwt_moto(aws_env):
    # Generate a JWT that expired 10 seconds ago
    expired_token = generate_jwt(
        client_id=CLIENT_ID,
        scope=SCOPE,
        secret_key=JWT_SECRET,
        expire_seconds=-10  # negative = already expired
    )

    # Build the event
    event = event_template.copy()
    event["authorizationToken"] = f"Bearer {expired_token}"
    event["methodArn"] = event_template["methodArn"]

    # Call the Lambda handler
    result = handler(event, None)

    # Assertions
    assert result["principalId"] == "unknown"  # default when JWT invalid
    statement = result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Deny"
    assert statement["Resource"] == event_template["methodArn"]

# --- Deny access due to invalid JWT format ---
def test_integration_invalid_jwt_format_moto(aws_env):
    # Build the event with an invalid JWT string
    event = event_template.copy()
    event["authorizationToken"] = "Bearer not-a-jwt"
    event["methodArn"] = event_template["methodArn"]

    # Call the Lambda handler
    result = handler(event, None)

    # Assertions
    assert result["principalId"] == "unknown"
    statement = result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Deny"
    assert statement["Resource"] == event_template["methodArn"]

# --- Deny access due to missing Authorization header ---
def test_integration_missing_header_moto(aws_env):
    # Build event with no Authorization header
    event = event_template.copy()
    event.pop("authorizationToken", None)  # Remove the key

    # Call the Lambda handler
    result = handler(event, None)

    # Assertions
    assert result["principalId"] == "unknown"
    statement = result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Deny"
    assert statement["Resource"] == event_template["methodArn"]


# --- Deny access due to invalid Authorization header format ---
def test_integration_invalid_header_format_moto(aws_env):
    # Header exists but is malformed
    event = event_template.copy()
    event["authorizationToken"] = "invalid_token_format"

    # Call the Lambda handler
    result = handler(event, None)

    # Assertions
    assert result["principalId"] == "unknown"
    statement = result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Deny"
    assert statement["Resource"] == event_template["methodArn"]

# --- Deny access due to missing JWT secret in Secrets Manager ---
def test_integration_missing_jwt_secret_moto():
    # Generate the event using make_event
    event = make_event(CLIENT_ID, SCOPE, JWT_SECRET, event_template["methodArn"])

    with mock_aws():  # moto intercepts boto3 calls
        # Call the Lambda handler
        result = handler(event, None)

    # Assertions
    assert result["principalId"] == "unknown"
    statement = result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Deny"
    assert statement["Resource"] == event_template["methodArn"]
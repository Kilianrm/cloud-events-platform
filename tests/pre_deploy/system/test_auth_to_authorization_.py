import pytest
import boto3
from moto import mock_aws
import os
from authentication.handler import handler as authentication_handler
from authorization.handler import handler as authorization_handler
import json

# Sample constants
JWT_SECRET = "this_is_a_long_secure_test_secret_32_bytes!!"
CLIENT_ID = "user123"
CLIENT_SECRET = "client-secret"
SCOPE = "read,write"

# -----------------------------
# Fixture
# -----------------------------
@pytest.fixture
def aws_env():
    os.environ["JWT_SECRET"] = JWT_SECRET

    with mock_aws():
        sm_client = boto3.client("secretsmanager")

        sm_client.create_secret(
            Name="auth/jwt_secret",
            SecretString=JWT_SECRET
        )

        sm_client.create_secret(
            Name=f"auth/client/{CLIENT_ID}",
            SecretString=json.dumps({
                "client_secret": CLIENT_SECRET,
                "scope": SCOPE
            })
        )

        yield


# -----------------------------
# Cross-service integration test: happy path
# -----------------------------
def test_auth_to_authorization_happy_path(aws_env):

    # 1. Authenticate user
    auth_event = {
        "body": json.dumps({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        })
    }

    auth_response = authentication_handler(auth_event, None)

    assert auth_response["statusCode"] == 200

    body = json.loads(auth_response["body"])
    jwt_token = body["access_token"]

    # 2. Authorize request using JWT
    authz_event = {
        "headers": {
            "authorization": f"Bearer {jwt_token}"
        },
        "httpMethod": "GET",
        "path": "/events"
    }

    authz_result = authorization_handler(authz_event, None)

    # 3. Assert allowed policy
    assert authz_result["principalId"] == CLIENT_ID
    statement = authz_result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Allow"


# -----------------------------
# Cross-service integration test: insufficient scope
# -----------------------------
def test_auth_to_authorization_insufficient_scope(aws_env):

    sm_client = boto3.client("secretsmanager")

    sm_client.update_secret(
        SecretId=f"auth/client/{CLIENT_ID}",
        SecretString=json.dumps({
            "client_secret": CLIENT_SECRET,
            "scope": "write"  # missing 'read'
        })
    )

    # 1. Authenticate user
    auth_event = {
        "body": json.dumps({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        })
    }

    auth_response = authentication_handler(auth_event, None)

    assert auth_response["statusCode"] == 200

    body = json.loads(auth_response["body"])
    jwt_token = body["access_token"]

    # 2. Authorize request
    authz_event = {
        "headers": {
            "authorization": f"Bearer {jwt_token}"
        },
        "httpMethod": "GET",
        "path": "/events"
    }

    authz_result = authorization_handler(authz_event, None)

    # 3. Assert denied policy
    assert authz_result["principalId"] == CLIENT_ID
    statement = authz_result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Deny"
# tests/e2e/test_authorization_flow_e2e.py

import pytest
import boto3
from moto import mock_aws
import os
from authentication.handler import handler as authentication_handler # your Authentication Lambda
from authorization.handler import handler as authorization_handler
from shared.jwt_utils import generate_jwt, verify_jwt
import json

# Sample constants
JWT_SECRET = "this_is_a_long_secure_test_secret_32_bytes!!"
CLIENT_ID = "user123"
CLIENT_SECRET = "client-secret"
SCOPE = "read,write"
METHOD_ARN = "arn:aws:execute-api:region:account:id"

# --- Fixture for AWS environment ---
@pytest.fixture
def aws_env():
    os.environ["JWT_SECRET"] = JWT_SECRET
    with mock_aws():
        sm_client = boto3.client("secretsmanager")

        # JWT secret
        sm_client.create_secret(Name="auth/jwt_secret", SecretString=JWT_SECRET)

        # Client/service secret
        sm_client.create_secret(
            Name=f"auth/client/{CLIENT_ID}",
            SecretString=json.dumps({
                "client_secret": CLIENT_SECRET,
                "scope": "read,write"
            })
        )


        yield

# --- E2E Test: happy path read ---
def test_e2e_happy_path_read(aws_env):

    # 1️⃣ Authenticate client → get JWT
    event = {
        "body": json.dumps({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        })
    }

    auth_response = authentication_handler(event, None)

    #Get jwt_token
    assert auth_response["statusCode"] == 200  # good practice

    body = json.loads(auth_response["body"])
    jwt_token = body["access_token"]

    # 2️⃣ Call Authorization Lambda,

    event = {
        "headers": {
            "authorization": f"Bearer {jwt_token}"
        },
        "httpMethod": "GET",
        "path": "/events"
    }
    authz_result = authorization_handler(event, None)

    # 3️⃣ Check IAM policy
    assert authz_result["principalId"] == CLIENT_ID
    statement = authz_result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Allow"

# --- E2E Test: valid authentication but insufficient scope → Deny ---
def test_e2e_insufficient_scope_deny(aws_env):
    # 1️⃣ Modify the client in Secrets Manager to have a different scope
    sm_client = boto3.client("secretsmanager")
    sm_client.update_secret(
        SecretId=f"auth/client/{CLIENT_ID}",
        SecretString=json.dumps({
            "client_secret": CLIENT_SECRET,
            "scope": "write"  # scope does NOT include 'read'
        })
    )

    # 2️⃣ Authenticate client → get JWT
    event = {
        "body": json.dumps({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        })
    }
    auth_response = authentication_handler(event, None)
    assert auth_response["statusCode"] == 200

    body = json.loads(auth_response["body"])
    jwt_token = body["access_token"]

    # 3️⃣ Call Authorization Lambda with this JWT
    event = {
        "headers": {
            "authorization": f"Bearer {jwt_token}"
        },
        "httpMethod": "GET",
        "path": "/events"
    }

    method = event.get("httpMethod")
    path = event.get("path")

    authz_result = authorization_handler(event, None)

    # 4️⃣ Assertions: policy should deny
    assert authz_result["principalId"] == CLIENT_ID
    statement = authz_result["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Deny"

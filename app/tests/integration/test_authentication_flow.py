import json
import pytest
import boto3
import os
from moto import mock_aws
from authentication.handler import handler

CLIENT_ID = "myclient"
CLIENT_SECRET = "secret123-2782o2374-improve-key"
JWT_SECRET = "this_is_a_long_secure_test_secret_32_bytes!!"


@pytest.fixture
def aws_env():
    """
    Prepares a mocked AWS environment using Moto for integration tests.
    Creates:
      - Client secret in Secrets Manager
      - JWT secret in Secrets Manager
    Also sets JWT_SECRET environment variable.
    """
    os.environ["JWT_SECRET"] = JWT_SECRET
    with mock_aws():
        sm_client = boto3.client("secretsmanager")

        # Client/service secret
        sm_client.create_secret(
            Name=f"auth/client/{CLIENT_ID}",
            SecretString=json.dumps({
                "client_secret": CLIENT_SECRET,
                "scope": "events:read"
            })
        )

        # JWT secret
        sm_client.create_secret(
            Name="auth/jwt_secret",
            SecretString=JWT_SECRET
        )

        yield


def test_lambda_success(aws_env):
    """
    Integration test: Valid client credentials should return 200 and a JWT token.
    """
    event = {
        "body": json.dumps({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        })
    }

    response = handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert "access_token" in body
    assert body["token_type"] == "Bearer"


def test_lambda_invalid_secret(aws_env):
    """
    Integration test: Invalid client_secret should return 401 and error.
    """
    event = {
        "client_id": CLIENT_ID,
        "client_secret": "wrongsecret"
    }

    response = handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 401
    assert body["error"] == "invalid_client"


def test_lambda_unknown_client(aws_env):
    """
    Integration test: Unknown client_id should return 401 and error.
    """
    event = {
        "client_id": "unknownclient",
        "client_secret": CLIENT_SECRET
    }

    response = handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 401
    assert body["error"] == "invalid_client"
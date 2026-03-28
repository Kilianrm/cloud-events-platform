import json
import pytest
from unittest.mock import patch
from authentication.handler import handler 

# --- Sample events for testing ---
event_valid = {
    "body": json.dumps({
        "client_id": "my-client",
        "client_secret": "secret123"
    })
}

event_invalid_body = {"body": "{}"}  # Event with empty JSON body
event_no_body = {}  # Event with no body at all

# --- Mock data ---
client_data_mock = {"scope": "read:items"}  # Mock client data returned from get_client_data
jwt_mock = "jwt-token-123"  # Mock JWT token returned from generate_jwt

# --- Unit test for successful authentication ---
@patch("authentication.handler.get_client_data")
@patch("authentication.handler.validate_client")
@patch("authentication.handler.generate_jwt")
@patch("authentication.handler.get_jwt_secret")
def test_handler_success(mock_get_jwt_secret, mock_generate_jwt, mock_validate_client, mock_get_client_data):
    # Arrange: define return values for the mocked functions
    mock_get_client_data.return_value = client_data_mock
    mock_validate_client.return_value = True
    mock_generate_jwt.return_value = jwt_mock
    mock_get_jwt_secret.return_value = "supersecret"

    # Act: call the handler with a valid event
    response = handler(event_valid, None)
    body = json.loads(response["body"])

    # Assert: check that the response is correct
    assert response["statusCode"] == 200
    assert body["access_token"] == jwt_mock
    assert body["token_type"] == "Bearer"

# --- Unit test for event with no body ---
def test_handler_no_body():
    response = handler(event_no_body, None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 401
    assert body["error"] == "invalid_client"

# --- Unit test for unknown client (Secrets Manager returns None) ---
@patch("authentication.handler.get_client_data")
def test_handler_client_not_found(mock_get_client_data):
    mock_get_client_data.return_value = None
    response = handler(event_valid, None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 401
    assert body["error"] == "invalid_client"

# --- Unit test for invalid credentials ---
@patch("authentication.handler.get_client_data")
@patch("authentication.handler.validate_client")
def test_handler_invalid_credentials(mock_validate_client, mock_get_client_data):
    # Arrange: get_client_data returns valid client data, but credentials are invalid
    mock_get_client_data.return_value = client_data_mock
    mock_validate_client.return_value = False

    # Act
    response = handler(event_valid, None)
    body = json.loads(response["body"])

    # Assert
    assert response["statusCode"] == 401
    assert body["error"] == "invalid_client"
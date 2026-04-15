import pytest
from unittest.mock import patch, MagicMock
from shared.secrets_service import get_client_data, get_jwt_secret

CLIENT_ID = "myclient"
CLIENT_SECRET = {"client_secret": "12345", "scope": "read:items"}
JWT_SECRET = "jwt-super-secret"

# --- get_client_data tests ---
@patch("shared.secrets_service.boto3.client")
def test_get_client_data_exists(mock_boto_client):
    # Arrange
    mock_sm = MagicMock()
    mock_sm.get_secret_value.return_value = {"SecretString": '{"client_secret": "12345", "scope": "read:items"}'}
    mock_boto_client.return_value = mock_sm

    # Act
    result = get_client_data(CLIENT_ID)

    # Assert
    assert result == CLIENT_SECRET
    mock_sm.get_secret_value.assert_called_once_with(SecretId=f"auth/client/{CLIENT_ID}")


@patch("shared.secrets_service.boto3.client")
def test_get_client_data_not_found(mock_boto_client):
    # Arrange
    mock_sm = MagicMock()
    # Simula que boto3 lanza ResourceNotFoundException
    mock_sm.exceptions.ResourceNotFoundException = Exception
    mock_sm.get_secret_value.side_effect = mock_sm.exceptions.ResourceNotFoundException
    mock_boto_client.return_value = mock_sm

    # Act
    result = get_client_data(CLIENT_ID)

    # Assert
    assert result is None
    mock_sm.get_secret_value.assert_called_once_with(SecretId=f"auth/client/{CLIENT_ID}")


# --- get_jwt_secret tests ---
@patch("shared.secrets_service.boto3.client")
def test_get_jwt_secret_exists(mock_boto_client):
    # Arrange
    mock_sm = MagicMock()
    mock_sm.get_secret_value.return_value = {"SecretString": JWT_SECRET}
    mock_boto_client.return_value = mock_sm

    # Act
    result = get_jwt_secret()

    # Assert
    assert result == JWT_SECRET
    mock_sm.get_secret_value.assert_called_once_with(SecretId="auth/jwt_secret")
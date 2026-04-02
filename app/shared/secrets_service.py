import boto3
import json


def get_secrets_client():
    """
    Creates and returns a boto3 Secrets Manager client.

    Returns:
        boto3.client: A Secrets Manager client instance.
    """
    return boto3.client("secretsmanager")


def get_client_data(client_id: str,client_secret_prefix="auth/client/") -> dict | None:
    """
    Retrieves client data from AWS Secrets Manager.

    The secret is expected to be stored under the key:
        auth/client/<client_id>

    Args:
        client_id (str): The ID of the client to retrieve.

    Returns:
        dict | None: The client data as a dictionary if found, or None if the secret does not exist.
    """
    sm_client = get_secrets_client()
    try:
        secret_response = sm_client.get_secret_value(
            SecretId=f"{client_secret_prefix}{client_id}"
        )
        return json.loads(secret_response["SecretString"])
    except sm_client.exceptions.ResourceNotFoundException:
        # Return None if the secret does not exist
        return None


def get_jwt_secret(SecretId="auth/jwt_secret") -> str:
    """
    Retrieves the JWT signing secret from AWS Secrets Manager.

    The secret is expected to be stored under the key:
        auth/jwt_secret

    Returns:
        str: The JWT secret as a string.

    Raises:
        botocore.exceptions.ClientError: If the secret does not exist or access is denied.
    """
    sm_client = get_secrets_client()
    secret_response = sm_client.get_secret_value(SecretId=SecretId)
    return secret_response["SecretString"]
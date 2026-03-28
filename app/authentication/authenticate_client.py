def validate_client(client_id: str, client_secret: str, client_data: dict) -> bool:
    """
    Validates that the provided client_secret matches the one stored in Secrets Manager.

    Args:
        client_id (str): ID of the client.
        client_secret (str): Secret provided by the client.
        client_data (dict): Client data retrieved from Secrets Manager.

    Returns:
        bool: True if the secret matches, False otherwise.
    """
    stored_secret = client_data.get("client_secret")
    return stored_secret == client_secret
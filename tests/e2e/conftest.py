import os
import pytest
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "https://fhvzgjgnye.execute-api.us-east-1.amazonaws.com")

CLIENTS = [
    {"client_id": "client1", "client_secret": "super-secret-pass1"},
    {"client_id": "client2", "client_secret": "super-secret-pass2"},
]

@pytest.fixture(scope="session")
def get_jwt_token():
    """Return a function that requests a JWT for given client credentials"""
    def _get(client_id, client_secret):
        resp = requests.post(f"{API_BASE_URL}/auth/token", json={
            "client_id": client_id,
            "client_secret": client_secret
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        return None
    return _get
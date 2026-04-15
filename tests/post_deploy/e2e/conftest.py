import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------
# ENV VARS (from Terraform outputs)
# -----------------------------------
API_BASE_URL = os.getenv("API_BASE_URL")
TABLE_NAME = os.getenv("TABLE_NAME")


if not API_BASE_URL:
    raise RuntimeError("API_BASE_URL is not set.")

if not TABLE_NAME:
    raise RuntimeError("TABLE_NAME is not set.")


# -----------------------------------
# JWT helper fixture
# -----------------------------------
@pytest.fixture(scope="session")
def get_jwt_token():
    """
    Helper to obtain JWT tokens from auth service.
    """

    def _get(client_id: str, client_secret: str):
        resp = requests.post(
            f"{API_BASE_URL}/auth/token",
            json={
                "client_id": client_id,
                "client_secret": client_secret
            },
            timeout=10
        )

        if resp.status_code == 200:
            return resp.json().get("access_token")

        raise RuntimeError(
            f"Failed to get JWT for {client_id}. "
            f"Status: {resp.status_code}, Body: {resp.text}"
        )

    return _get


# -----------------------------------
# API base URL fixture (optional but clean)
# -----------------------------------
@pytest.fixture(scope="session")
def api_base_url():
    return API_BASE_URL


# -----------------------------------
# DynamoDB table fixture (NEW)
# -----------------------------------
@pytest.fixture(scope="session")
def table_name():
    """
    DynamoDB table name coming from Terraform output.
    """
    return TABLE_NAME
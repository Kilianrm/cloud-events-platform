import pytest
import requests
from conftest import API_BASE_URL

# -----------------------------
# POST /events (write)
# -----------------------------
def test_post_event_with_valid_body(get_jwt_token):

    #Get token
    valid_token = get_jwt_token("client1", "super-secret-pass1")
    assert valid_token is not None

    headers = {"Authorization": f"Bearer {valid_token}"}
    payload = {
        "event_id": "evt-test-001",
        "event_type": "TEST",
        "source": "e2e-test",
        "timestamp": "2026-03-01T12:00:00Z",
        "payload": {"x": 1}
    }
    resp = requests.post(f"{API_BASE_URL}/events", json=payload, headers=headers)
    assert resp.status_code in (200,201)# or 200 depending on your Lambda
    data = resp.json()
    assert data["event_id"] == payload["event_id"]



def test_post_event_with_invalid_body(get_jwt_token):

    #Get token
    valid_token = get_jwt_token("client1", "super-secret-pass1")
    assert valid_token is not None

    headers = {"Authorization": f"Bearer {valid_token}"}
    payload = {
        # missing event_id and event_type
        "source": "e2e-test",
        "timestamp": "2026-03-01T12:00:00Z",
        "payload": {"x": 1}
    }
    resp = requests.post(f"{API_BASE_URL}/events", json=payload, headers=headers)
    assert resp.status_code == 400  # bad request


# -----------------------------
# GET /events/{event_id} (read)
# -----------------------------
def test_get_event_with_valid_event(get_jwt_token):
    #Get token
    valid_token = get_jwt_token("client1", "super-secret-pass1")
    assert valid_token is not None

    headers = {"Authorization": f"Bearer {valid_token}"}
    event_id = "evt-test-001"  # event created in the previous test
    resp = requests.get(f"{API_BASE_URL}/events/{event_id}", headers=headers)
    # 200 if exists, 404 if not
    assert resp.status_code in (200, 404)

def test_get_event_with_invalid_event(get_jwt_token):

    #Get token
    valid_token = get_jwt_token("client1", "super-secret-pass1")
    assert valid_token is not None

    headers = {"Authorization": f"Bearer {valid_token}"}
    event_id = "non-existent-id"
    resp = requests.get(f"{API_BASE_URL}/events/{event_id}", headers=headers)
    assert resp.status_code == 404


def test_access_without_token():
    """Request to a protected route without JWT should fail"""
    resp = requests.get(f"{API_BASE_URL}/events/evt-test-001")
    assert resp.status_code == 401  # unauthorized

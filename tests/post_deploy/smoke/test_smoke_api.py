import requests
import uuid
from datetime import datetime, timezone, timedelta

# -----------------------------
# SMOKE 1 — API + AUTH OK
# -----------------------------
def test_api_accepts_valid_event(get_jwt_token,api_base_url):
    token = get_jwt_token("client1", "super-secret-pass1")

    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "SMOKE",
        "source": "smoke-test",
        "timestamp": (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat(),
        "payload": {"x": 1}
    }
    

    resp = requests.post(f"{api_base_url}/events",json=payload,headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code in (200, 201, 202)


# -----------------------------
# SMOKE 2 — INVALID REQUEST FAILS
# -----------------------------
def test_api_rejects_invalid_event(get_jwt_token,api_base_url):
    token = get_jwt_token("client1", "super-secret-pass1")

    payload = {
        "source": "smoke-test"
    }

    resp = requests.post(
       f"{api_base_url}/events",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert resp.status_code == 400


# -----------------------------
# SMOKE 3 — AUTH REQUIRED
# -----------------------------
def test_api_requires_auth(api_base_url):
    resp = requests.get(f"{api_base_url}/events/smoke-1")

    assert resp.status_code == 401
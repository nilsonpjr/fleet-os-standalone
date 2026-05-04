import pytest
from fastapi.testclient import TestClient

def test_chat_workflow(http: TestClient, client_setup: tuple):
    token, tenant_id, client_id, user_id = client_setup
    # 1. Create a request
    resp = http.post(
        "/api/fleet/requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_description": "Chat Test",
            "urgency": "LOW",
            "vehicle_id": None
        }
    )
    assert resp.status_code == 201
    req_id = resp.json()["id"]

    # 2. Send a message
    resp = http.post(
        f"/api/fleet/requests/{req_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hello from Admin"}
    )
    assert resp.status_code == 200
    msg = resp.json()
    assert msg["message"] == "Hello from Admin"
    assert "user_name" in msg

    # 3. List messages
    resp = http.get(
        f"/api/fleet/requests/{req_id}/messages",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) == 1
    assert msgs[0]["message"] == "Hello from Admin"

def test_sustainability_calculation(http: TestClient, admin_token: tuple):
    token, tenant_id, user_id = admin_token
    # Reports should include total_co2
    resp = http.get(
        "/api/fleet/reports/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_co2" in data
    assert isinstance(data["total_co2"], (int, float))

def test_telemetry_webhook(http: TestClient, admin_token: tuple):
    token, tenant_id, user_id = admin_token
    # 1. Create a vehicle
    plate = "IOT-1234"
    http.post(
        "/api/fleet/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "plate": plate,
            "brand": "IoT Brand",
            "model": "Model X",
            "category": "CAR"
        }
    )

    # 2. Send telemetry
    resp = http.post(
        "/api/telemetry/hook",
        json={
            "device_id": plate,
            "lat": -23.5505,
            "lng": -46.6333,
            "mileage": 1500.5
        }
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # 3. Verify vehicle status
    resp = http.get(
        "/api/fleet/vehicles",
        headers={"Authorization": f"Bearer {token}"}
    )
    vehicles = resp.json()
    v = next(x for x in vehicles if x["plate"] == plate)
    assert v["last_lat"] == -23.5505
    assert v["mileage_current"] == 1500.5

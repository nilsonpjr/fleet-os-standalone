"""Tests for Workshop CRUD endpoints."""
import pytest

WORKSHOP_PAYLOAD = {
    "name": "Auto Center Premium",
    "cnpj": "12.345.678/0001-90",
    "phone": "(11) 99999-0000",
    "email": "oficina@autocenter.com",
    "address": "Rua das Flores, 123",
    "city": "São Paulo",
    "state": "SP",
    "contact_name": "João Silva",
    "specialties": ["Motor", "Suspensão", "Elétrica"],
    "vehicle_types": ["CAR", "TRUCK"],
    "max_concurrent_os": 8,
}


class TestWorkshopCRUD:
    def test_create_workshop(self, http, db, admin_token):
        token, _, _ = admin_token
        resp = http.post(
            "/api/fleet/workshops",
            json=WORKSHOP_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Auto Center Premium"
        assert "Motor" in data["specialties"]
        assert data["max_concurrent_os"] == 8

    def test_list_workshops(self, http, db, admin_token):
        token, _, _ = admin_token
        http.post("/api/fleet/workshops", json=WORKSHOP_PAYLOAD,
                  headers={"Authorization": f"Bearer {token}"})
        resp = http.get("/api/fleet/workshops",
                        headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_update_workshop_rating(self, http, db, admin_token):
        token, _, _ = admin_token
        wid = http.post("/api/fleet/workshops", json=WORKSHOP_PAYLOAD,
                        headers={"Authorization": f"Bearer {token}"}).json()["id"]
        resp = http.put(f"/api/fleet/workshops/{wid}",
                        json={"rating": 4.7},
                        headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["rating"] == 4.7

    def test_client_cannot_create_workshop(self, http, db, client_setup):
        token, _, _, _ = client_setup
        resp = http.post("/api/fleet/workshops", json=WORKSHOP_PAYLOAD,
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_workshop_not_found(self, http, db, admin_token):
        token, _, _ = admin_token
        resp = http.get("/api/fleet/workshops/9999",
                        headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

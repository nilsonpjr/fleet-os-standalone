"""Tests for Vehicle CRUD endpoints."""
import pytest
from fastapi.testclient import TestClient
from .conftest import _create_tenant, _create_user, _get_token
from backend_v2.modules.auth.models import UserRole


VEHICLE_PAYLOAD = {
    "plate": "ABC-1234",
    "brand": "Toyota",
    "model": "Hilux",
    "year_model": 2023,
    "year_manufacture": 2022,
    "color": "Branco",
    "fuel_type": "FLEX",
    "category": "TRUCK",
    "usage_type": "OPERACIONAL",
    "mileage_current": 15000,
    "ipva_value": 3500.00,
    "ipva_due_date": "2025-03-31",
    "licensing_year": 2025,
    "licensing_due_date": "2025-06-30",
    "licensing_paid": False,
    "insurance_policy": "POL-001",
    "insurance_company": "Bradesco Seguros",
    "insurance_expiry": "2025-12-31",
    "insurance_value": 55000.00,
}


class TestVehicleCRUD:
    def test_create_vehicle_as_admin(self, http, db, admin_token):
        token, tenant_id, _ = admin_token
        resp = http.post(
            "/api/fleet/vehicles",
            json=VEHICLE_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["plate"] == "ABC-1234"
        assert data["brand"] == "Toyota"
        assert data["ipva_value"] == 3500.00
        assert data["insurance_company"] == "Bradesco Seguros"

    def test_list_vehicles_returns_only_tenant(self, http, db, admin_token):
        token, tenant_id, _ = admin_token
        # Create vehicle
        http.post("/api/fleet/vehicles", json=VEHICLE_PAYLOAD,
                  headers={"Authorization": f"Bearer {token}"})
        # List
        resp = http.get("/api/fleet/vehicles",
                        headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        vehicles = resp.json()
        assert len(vehicles) == 1
        assert vehicles[0]["plate"] == "ABC-1234"

    def test_get_vehicle_by_id(self, http, db, admin_token):
        token, _, _ = admin_token
        create_resp = http.post("/api/fleet/vehicles", json=VEHICLE_PAYLOAD,
                                headers={"Authorization": f"Bearer {token}"})
        vid = create_resp.json()["id"]
        resp = http.get(f"/api/fleet/vehicles/{vid}",
                        headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == vid

    def test_update_vehicle_mileage(self, http, db, admin_token):
        token, _, _ = admin_token
        vid = http.post("/api/fleet/vehicles", json=VEHICLE_PAYLOAD,
                        headers={"Authorization": f"Bearer {token}"}).json()["id"]
        resp = http.put(f"/api/fleet/vehicles/{vid}",
                        json={"mileage_current": 20000},
                        headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["mileage_current"] == 20000

    def test_delete_vehicle_soft(self, http, db, admin_token):
        token, _, _ = admin_token
        vid = http.post("/api/fleet/vehicles", json=VEHICLE_PAYLOAD,
                        headers={"Authorization": f"Bearer {token}"}).json()["id"]
        resp = http.delete(f"/api/fleet/vehicles/{vid}",
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204
        # Should not appear in list (soft delete)
        vehicles = http.get("/api/fleet/vehicles",
                            headers={"Authorization": f"Bearer {token}"}).json()
        assert len(vehicles) == 0

    def test_client_cannot_create_vehicle(self, http, db, client_setup):
        token, _, _, _ = client_setup
        resp = http.post("/api/fleet/vehicles", json=VEHICLE_PAYLOAD,
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_vehicle_not_found_404(self, http, db, admin_token):
        token, _, _ = admin_token
        resp = http.get("/api/fleet/vehicles/9999",
                        headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

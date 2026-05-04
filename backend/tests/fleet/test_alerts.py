"""Tests for expiry alerts and boat regulatory."""
import pytest
from datetime import date, timedelta
from backend_v2.modules.fleet import crud
from backend_v2.modules.fleet.schemas import VehicleCreate, BoatRegulatoryCreate
from backend_v2.modules.fleet.models import RequestStatus
from .conftest import _create_tenant, _create_client
from backend_v2.modules.auth.models import UserRole


class TestExpiryAlerts:
    def test_vehicle_ipva_expiring_soon(self, db):
        tenant = _create_tenant(db)
        soon = (date.today() + timedelta(days=15)).isoformat()
        crud.create_vehicle(
            db,
            VehicleCreate(
                plate="EXP-001",
                brand="VW",
                model="Gol",
                ipva_due_date=soon,
                ipva_value=1000,
            ),
            tenant_id=tenant.id,
        )
        alerts = crud.get_expiry_alerts(db, tenant.id, days_ahead=30)
        ipva_alerts = [a for a in alerts if a.type == "IPVA"]
        assert len(ipva_alerts) == 1
        assert ipva_alerts[0].days_left == 15
        assert ipva_alerts[0].plate == "EXP-001"

    def test_vehicle_expired_shows_negative_days(self, db):
        tenant = _create_tenant(db)
        past = (date.today() - timedelta(days=5)).isoformat()
        crud.create_vehicle(
            db,
            VehicleCreate(plate="EXP-002", brand="Ford", model="Ka",
                          licensing_due_date=past, licensing_year=2024),
            tenant_id=tenant.id,
        )
        alerts = crud.get_expiry_alerts(db, tenant.id, days_ahead=30)
        lic_alerts = [a for a in alerts if a.type == "LICENCIAMENTO"]
        assert len(lic_alerts) == 1
        assert lic_alerts[0].days_left == -5

    def test_no_alerts_when_all_ok(self, db):
        tenant = _create_tenant(db)
        far = (date.today() + timedelta(days=90)).isoformat()
        crud.create_vehicle(
            db,
            VehicleCreate(plate="OK-001", brand="Fiat", model="Uno",
                          ipva_due_date=far, insurance_expiry=far),
            tenant_id=tenant.id,
        )
        alerts = crud.get_expiry_alerts(db, tenant.id, days_ahead=30)
        assert len(alerts) == 0

    def test_alerts_sorted_by_days_left(self, db):
        tenant = _create_tenant(db)
        day5  = (date.today() + timedelta(days=5)).isoformat()
        day20 = (date.today() + timedelta(days=20)).isoformat()
        crud.create_vehicle(
            db,
            VehicleCreate(plate="ALT-001", brand="GM", model="S10",
                          ipva_due_date=day20, insurance_expiry=day5),
            tenant_id=tenant.id,
        )
        alerts = crud.get_expiry_alerts(db, tenant.id, days_ahead=30)
        assert len(alerts) == 2
        assert alerts[0].days_left <= alerts[1].days_left

    def test_http_alerts_endpoint(self, http, db, admin_token):
        token, tenant_id, _ = admin_token
        soon = (date.today() + timedelta(days=10)).isoformat()
        http.post("/api/fleet/vehicles",
                  json={"plate": "A01", "brand": "X", "model": "Y",
                        "ipva_due_date": soon, "ipva_value": 500},
                  headers={"Authorization": f"Bearer {token}"})
        resp = http.get("/api/fleet/alerts",
                        headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestBoatRegulatory:
    def test_upsert_boat_regulatory(self, http, db, admin_token):
        # We can't create a boat via fleet module (uses existing boats module)
        # So we test CRUD layer directly
        from backend_v2.modules.boats.models import Boat
        from backend_v2.modules.fleet.crud import get_or_create_boat_regulatory

        tenant = _create_tenant(db)
        client = _create_client(db, tenant.id)
        boat = Boat(
            name="Barco Teste",
            tenant_id=tenant.id,
            client_id=client.id,
            hull_id="HULL-001",
            model="Fishing 21",
        )
        db.add(boat)
        db.commit()
        db.refresh(boat)

        br = get_or_create_boat_regulatory(
            db,
            BoatRegulatoryCreate(
                boat_id=boat.id,
                registration_number="PREF-001",
                registration_expiry="2025-12-31",
                tmc_number="TMC-999",
                max_passengers=8,
            ),
        )
        assert br.registration_number == "PREF-001"
        assert br.tmc_number == "TMC-999"
        assert br.boat_id == boat.id

        # Upsert (update)
        br2 = get_or_create_boat_regulatory(
            db,
            BoatRegulatoryCreate(boat_id=boat.id, registration_number="PREF-002"),
        )
        assert br2.registration_number == "PREF-002"
        assert br2.id == br.id  # same record

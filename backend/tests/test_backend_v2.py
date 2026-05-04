"""
Fase 2 — Testes automatizados do backend_v2 (sem banco de dados real).
Usa SQLite em memória para testar routers de forma isolada.

Run: cd backend && .\.venv\Scripts\pytest ..\backend_v2\tests\ -v
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory SQLite
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["ALGORITHM"] = "HS256"


from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, get_db
from main import app

from sqlalchemy.pool import StaticPool

# Override DB with in-memory SQLite
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
from sqlalchemy import event

@event.listens_for(TEST_ENGINE, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)
Base.metadata.create_all(bind=TEST_ENGINE)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _create_tenant_and_admin(db):
    from modules.auth.models import Tenant, User, UserRole
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"])
    tenant = Tenant(name="Teste Tenant", subdomain="teste", plan="BASIC")
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        name="Admin Teste",
        email="admin@teste.com",
        hashed_password=pwd.hash("senha123"),
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.commit()
    return tenant, user


def _get_token(email="admin@teste.com", password="senha123") -> str:
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


# ─── Tests: Health ──────────────────────────────────────────────────────────

def test_root_returns_200():
    resp = client.get("/")
    assert resp.status_code in (200, 404)  # 404 if no dist


# ─── Tests: Auth ────────────────────────────────────────────────────────────

class TestAuth:
    def setup_method(self):
        Base.metadata.drop_all(bind=TEST_ENGINE)
        Base.metadata.create_all(bind=TEST_ENGINE)
        db = TestSession()
        _create_tenant_and_admin(db)
        db.close()

    def test_login_success(self):
        resp = client.post("/api/auth/login", data={"username": "admin@teste.com", "password": "senha123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self):
        resp = client.post("/api/auth/login", data={"username": "admin@teste.com", "password": "errada"})
        assert resp.status_code == 401

    def test_me_requires_auth(self):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_token(self):
        token = _get_token()
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "admin@teste.com"


# ─── Tests: Clients ─────────────────────────────────────────────────────────

class TestClients:
    def setup_method(self):
        Base.metadata.drop_all(bind=TEST_ENGINE)
        Base.metadata.create_all(bind=TEST_ENGINE)
        db = TestSession()
        _create_tenant_and_admin(db)
        db.close()
        self.token = _get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_clients_empty(self):
        resp = client.get("/api/clients", headers=self.headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_client(self):
        payload = {"name": "João Silva", "document": "123.456.789-00", "phone": "11999999999", "type": "PARTICULAR"}
        resp = client.post("/api/clients", json=payload, headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "João Silva"
        assert data["document"] == "123.456.789-00"

    def test_get_client_not_found(self):
        resp = client.get("/api/clients/9999", headers=self.headers)
        assert resp.status_code == 404


# ─── Tests: Boats ───────────────────────────────────────────────────────────

class TestBoats:
    def setup_method(self):
        Base.metadata.drop_all(bind=TEST_ENGINE)
        Base.metadata.create_all(bind=TEST_ENGINE)
        db = TestSession()
        _create_tenant_and_admin(db)
        db.close()
        self.token = _get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_boats_empty(self):
        resp = client.get("/api/boats", headers=self.headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_boat_requires_valid_client(self):
        payload = {"name": "Barco Teste", "hull_id": "HULL-001", "client_id": 999}
        resp = client.post("/api/boats", json=payload, headers=self.headers)
        # Should fail (no client 999) — handled by DB constraint or 404
        assert resp.status_code in (404, 422, 500), f"Got {resp.status_code}: {resp.text}"


# ─── Tests: Inventory ───────────────────────────────────────────────────────

class TestInventory:
    def setup_method(self):
        Base.metadata.drop_all(bind=TEST_ENGINE)
        Base.metadata.create_all(bind=TEST_ENGINE)
        db = TestSession()
        _create_tenant_and_admin(db)
        db.close()
        self.token = _get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_parts_empty(self):
        resp = client.get("/api/inventory/parts", headers=self.headers)
        assert resp.status_code == 200

    def test_create_part(self):
        payload = {"sku": "P-001", "name": "Filtro de Óleo", "price": 49.90, "cost": 20.00}
        resp = client.post("/api/inventory/parts", json=payload, headers=self.headers)
        assert resp.status_code == 200
        assert resp.json()["sku"] == "P-001"

    def test_create_part_duplicate_sku(self):
        payload = {"sku": "P-DUP", "name": "Peça A", "price": 10.0}
        client.post("/api/inventory/parts", json=payload, headers=self.headers)
        resp = client.post("/api/inventory/parts", json=payload, headers=self.headers)
        assert resp.status_code == 400


# ─── Tests: LGPD ────────────────────────────────────────────────────────────

class TestLGPD:
    def setup_method(self):
        Base.metadata.drop_all(bind=TEST_ENGINE)
        Base.metadata.create_all(bind=TEST_ENGINE)
        db = TestSession()
        _create_tenant_and_admin(db)
        db.close()
        self.token = _get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def _create_client(self):
        payload = {"name": "Maria Costa", "document": "987.654.321-00", "phone": "11988888888", "type": "PARTICULAR"}
        resp = client.post("/api/clients", json=payload, headers=self.headers)
        return resp.json()["id"]

    def test_data_processing_info(self):
        resp = client.get("/api/lgpd/data-processing-info", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "purposes" in data
        assert "data_subject_rights" in data
        assert len(data["data_subject_rights"]) >= 5  # At least 5 rights implemented

    def test_data_export(self):
        cid = self._create_client()
        resp = client.get(f"/api/lgpd/data-export/{cid}", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "personal_data" in data
        assert data["personal_data"]["name"] == "Maria Costa"

    def test_portability_csv(self):
        cid = self._create_client()
        resp = client.get(f"/api/lgpd/portability/{cid}", headers=self.headers)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    def test_erasure_request_flow(self):
        cid = self._create_client()
        # 1. Request erasure
        resp = client.post(f"/api/lgpd/erase/{cid}", json={"reason": "Não desejo mais ser cadastrado"}, headers=self.headers)
        assert resp.status_code == 201
        req_id = resp.json()["id"]
        assert resp.json()["status"] == "PENDING"

        # 2. Admin reviews and approves
        resp = client.put(f"/api/lgpd/erase/{req_id}/review", json={"approved": True}, headers=self.headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "APPROVED"

        # 3. Execute anonymization
        resp = client.post(f"/api/lgpd/erase/{req_id}/execute", headers=self.headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "EXECUTED"

        # 4. Verify client is anonymized
        resp = client.get(f"/api/clients/{cid}", headers=self.headers)
        assert resp.status_code == 200
        assert "ANONIMIZADO" in resp.json()["name"]
        assert resp.json()["phone"] is None

    def test_consent_registration(self):
        cid = self._create_client()
        payload = {
            "client_id": cid,
            "source": "ERP_MANUAL",
            "purpose": "SERVICE_CONTRACT",
            "consent_text": "Autorizo o tratamento de dados para execução do serviço.",
        }
        resp = client.post("/api/lgpd/consent", json=payload, headers=self.headers)
        assert resp.status_code == 201
        assert resp.json()["is_active"] is True

    def test_audit_log_recorded(self):
        cid = self._create_client()
        client.get(f"/api/lgpd/data-export/{cid}", headers=self.headers)
        resp = client.get("/api/lgpd/audit-log", headers=self.headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        assert resp.json()[0]["action"] == "DATA_EXPORT"

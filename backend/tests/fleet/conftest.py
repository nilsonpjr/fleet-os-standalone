"""Shared test fixtures for fleet module."""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from core.database import Base, get_db
from modules.auth.models import User, UserRole, Tenant
from modules.auth.crud import get_password_hash
from modules.clients.models import Client
from main import app

# ── Shared in-memory SQLite DB ────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def override_db_dependency():
    """
    Isolates dependency override for this test package.
    Prevents interference from other test files that also override get_db.
    """
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Recreate tables before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def _create_tenant(db) -> Tenant:
    suffix = uuid.uuid4().hex[:8]
    t = Tenant(name=f"Frota Teste {suffix}", subdomain=f"frota-teste-{suffix}")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _create_user(db, tenant_id: int, role: UserRole, email: str = None) -> User:
    u = User(
        name="Teste User",
        email=email or f"user_{role.value.lower()}@test.com",
        hashed_password=get_password_hash("senha123"),
        role=role,
        tenant_id=tenant_id,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_client(db, tenant_id: int) -> Client:
    c = Client(
        name="Cliente Frota SA",
        document="12.345.678/0001-99",
        tenant_id=tenant_id,
        is_active=True,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _get_token(client: TestClient, email: str, password: str = "senha123") -> str:
    resp = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    return resp.json()["access_token"]


@pytest.fixture
def http():
    return TestClient(app)


@pytest.fixture
def admin_token(http, db):
    t = _create_tenant(db)
    u = _create_user(db, t.id, UserRole.ADMIN, "admin@fleet.test")
    return _get_token(http, "admin@fleet.test"), t.id, u.id


@pytest.fixture
def client_setup(http, db):
    t = _create_tenant(db)
    cli = _create_client(db, t.id)
    u = _create_user(db, t.id, UserRole.CLIENT, "client@fleet.test")
    u.client_id = cli.id
    db.commit()
    token = _get_token(http, "client@fleet.test")
    return token, t.id, cli.id, u.id

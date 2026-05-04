"""
Auth module — User, Tenant and authentication models.
Tables: users, tenants
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend_v2.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN      = "ADMIN"
    MANAGER    = "MANAGER"
    TECHNICIAN = "TECHNICIAN"
    CLIENT     = "CLIENT"
    PARTNER    = "PARTNER"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    cnpj = Column(String(50))
    subdomain = Column(String(100), unique=True)
    plan = Column(String(50), default="START")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("workshops.id"), nullable=True)
    preferences = Column(JSON, default={})

    client = relationship("Client", back_populates="user", foreign_keys=[client_id])
    tenant = relationship("Tenant", back_populates="users")

    @property
    def tenant_plan(self) -> str:
        return self.tenant.plan if self.tenant else "START"

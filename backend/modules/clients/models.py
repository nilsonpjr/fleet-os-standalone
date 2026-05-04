"""
Clients module — Client and Marina models.
Tables: clients, marinas
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    document = Column(String(50), nullable=False)
    phone = Column(String(50))
    email = Column(String(200))
    address = Column(Text)
    type = Column(String(50))
    telegram_id = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)

    boats = relationship("Boat", back_populates="owner")
    user = relationship("User", back_populates="client", uselist=False,
                        foreign_keys="User.client_id")


class Marina(Base):
    __tablename__ = "marinas"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    address = Column(Text)
    contact_name = Column(String(200))
    phone = Column(String(50))
    coordinates = Column(String(100))
    operating_hours = Column(String(200))

    boats = relationship("Boat", back_populates="marina")

"""
Boats module — Boat and Engine models.
Tables: boats, engines
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from backend_v2.core.database import Base


class Engine(Base):
    __tablename__ = "engines"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    boat_id = Column(Integer, ForeignKey("boats.id"), nullable=False)
    serial_number = Column(String(100), nullable=False)
    motor_number = Column(String(100))
    model = Column(String(200), nullable=False)
    sale_date = Column(String(50))
    warranty_status = Column(String(100))
    warranty_validity = Column(String(50))
    client_name = Column(String(200))
    hours = Column(Integer, default=0)
    year = Column(Integer)

    boat = relationship("Boat", back_populates="engines")


class Boat(Base):
    __tablename__ = "boats"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    marina_id = Column(Integer, ForeignKey("marinas.id"), nullable=True)
    name = Column(String(200), nullable=False)
    hull_id = Column(String(100), nullable=False)
    usage_type = Column(String(50))
    model = Column(String(200))

    owner = relationship("Client", back_populates="boats")
    marina = relationship("Marina", back_populates="boats")
    engines = relationship("Engine", back_populates="boat", cascade="all, delete-orphan")
    service_orders = relationship("ServiceOrder", back_populates="boat")

"""
Orders module — ServiceOrder, ServiceItem, OrderNote, TechnicalDelivery models.
Tables: service_orders, service_items, order_notes, technical_deliveries
"""
from __future__ import annotations
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from backend_v2.core.database import Base


class OSStatus(str, enum.Enum):
    PENDING = "Pendente"
    QUOTATION = "Em Orçamento"
    APPROVED = "Aprovado"
    IN_PROGRESS = "Em Execução"
    COMPLETED = "Concluído"
    CANCELED = "Cancelado"


class ItemType(str, enum.Enum):
    PART = "PART"
    LABOR = "LABOR"


class DeliveryType(str, enum.Enum):
    OUTBOARD = "OUTBOARD"
    STERNDRIVE = "STERNDRIVE"


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    boat_id = Column(Integer, ForeignKey("boats.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    engine_id = Column(Integer, ForeignKey("engines.id"), nullable=True)
    description = Column(Text, nullable=False)
    diagnosis = Column(Text)
    status = Column(Enum(OSStatus), default=OSStatus.PENDING)
    total_value = Column(Float, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    requester = Column(String(200))
    technician_name = Column(String(200))
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    estimated_duration = Column(Integer, nullable=True)
    checklist = Column(JSON, default=[])

    boat = relationship("Boat", back_populates="service_orders")
    client = relationship("Client")
    items = relationship("ServiceItem", back_populates="order", cascade="all, delete-orphan")
    notes = relationship("OrderNote", back_populates="order", cascade="all, delete-orphan")
    fiscal_invoices = relationship("FiscalInvoice", back_populates="service_order")
    technical_delivery = relationship(
        "TechnicalDelivery", back_populates="service_order",
        uselist=False, cascade="all, delete-orphan"
    )
    assigned_technician = relationship("User", foreign_keys=[technician_id])

    @property
    def boat_name(self) -> str | None:
        return self.boat.name if self.boat else None

    @property
    def client_name(self) -> str | None:
        if self.client:
            return self.client.name
        return self.boat.owner.name if self.boat and self.boat.owner else None

    @property
    def client_phone(self) -> str | None:
        if self.client:
            return self.client.phone
        return self.boat.owner.phone if self.boat and self.boat.owner else None

    @property
    def client_email(self) -> str | None:
        if self.client:
            return self.client.email
        return self.boat.owner.email if self.boat and self.boat.owner else None

    @property
    def client_telegram_id(self) -> str | None:
        if self.client:
            return self.client.telegram_id
        return self.boat.owner.telegram_id if self.boat and self.boat.owner else None

    @property
    def email(self) -> str | None:
        return self.client_email

    @property
    def phone(self) -> str | None:
        return self.client_phone


class ServiceItem(Base):
    __tablename__ = "service_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    type = Column(Enum(ItemType), nullable=False)
    description = Column(String(200), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=True)
    quantity = Column(Float, default=1)
    unit_cost = Column(Float, default=0)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)

    order = relationship("ServiceOrder", back_populates="items")
    part = relationship("Part", back_populates="service_items")


class OrderNote(Base):
    __tablename__ = "order_notes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_name = Column(String(200))

    order = relationship("ServiceOrder", back_populates="notes")


class TechnicalDelivery(Base):
    __tablename__ = "technical_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False, unique=True)
    delivery_type = Column(Enum(DeliveryType))
    checklist_data = Column(JSON, default={})
    observations = Column(Text)
    client_signature = Column(Text, nullable=True)
    technician_signature = Column(Text, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    service_order = relationship("ServiceOrder", back_populates="technical_delivery")

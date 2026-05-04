"""
Partners module — Partner, PartnerQuote, Inspection models.
Tables: partners, partner_quotes, inspections
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship

from backend_v2.core.database import Base


class PartnerType(str, enum.Enum):
    ELECTRICIAN = "Eletricista"
    UPHOLSTERER = "Capoteiro"
    PAINTER = "Pintor"
    MECHANIC = "Mecânico"
    REFRIGERATION = "Refrigeração"
    ELECTRONICS = "Eletrônica"
    FIBERGLASS = "Fibra de Vidro"
    OTHER = "Outro"


class QuoteStatus(str, enum.Enum):
    REQUESTED = "Solicitado"
    RECEIVED = "Recebido"
    APPROVED = "Aprovado"
    REJECTED = "Rejeitado"
    COMPLETED = "Concluído"


class InspectionStatus(str, enum.Enum):
    SCHEDULED = "Agendada"
    IN_PROGRESS = "Em Andamento"
    COMPLETED = "Concluída"
    CANCELED = "Cancelada"


class ChecklistItemSeverity(str, enum.Enum):
    OK = "OK"
    ATTENTION = "Atenção"
    URGENT = "Urgente"
    CRITICAL = "Crítico"


class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(200), nullable=False)
    company_name = Column(String(200), nullable=True)
    document = Column(String(20), nullable=True)
    partner_type = Column(Enum(PartnerType), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    rating = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    quotes = relationship("PartnerQuote", back_populates="partner", cascade="all, delete-orphan")


class PartnerQuote(Base):
    __tablename__ = "partner_quotes"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=True)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=True)
    status = Column(Enum(QuoteStatus), default=QuoteStatus.REQUESTED)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    partner = relationship("Partner", back_populates="quotes")
    service_order = relationship("ServiceOrder")


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=True)
    boat_id = Column(Integer, ForeignKey("boats.id"), nullable=True)
    inspector_name = Column(String(200))
    status = Column(Enum(InspectionStatus), default=InspectionStatus.SCHEDULED)
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    checklist_data = Column(JSON, default={})
    observations = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

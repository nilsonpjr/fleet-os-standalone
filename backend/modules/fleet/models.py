"""
Fleet module — Vehicle, BoatRegulatory, Workshop, FleetRequest,
WorkshopQuote, QuoteItem, WorkshopExecution models.

Additive only: no existing tables are modified.
"""
from __future__ import annotations
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    Enum, JSON, ForeignKey
)
from sqlalchemy.orm import relationship

from backend_v2.core.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────

class VehicleCategory(str, enum.Enum):
    CAR         = "CAR"
    MOTORCYCLE  = "MOTORCYCLE"
    TRUCK       = "TRUCK"
    VAN         = "VAN"
    OTHER       = "OTHER"


class FuelType(str, enum.Enum):
    GASOLINE = "GASOLINE"
    ETHANOL  = "ETHANOL"
    FLEX     = "FLEX"
    DIESEL   = "DIESEL"
    ELECTRIC = "ELECTRIC"
    HYBRID   = "HYBRID"
    GNV      = "GNV"


class RequestStatus(str, enum.Enum):
    OPEN                = "OPEN"
    ASSIGNED            = "ASSIGNED"
    QUOTED              = "QUOTED"
    ADMIN_APPROVED      = "ADMIN_APPROVED"
    CLIENT_APPROVED     = "CLIENT_APPROVED"
    REVISION_REQUESTED  = "REVISION_REQUESTED"
    IN_PROGRESS         = "IN_PROGRESS"
    AWAITING_CLOSURE    = "AWAITING_CLOSURE"
    ADMIN_CLOSED        = "ADMIN_CLOSED"
    CLIENT_CLOSED       = "CLIENT_CLOSED"
    DONE                = "DONE"
    CANCELED            = "CANCELED"


class Urgency(str, enum.Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class QuoteStatus(str, enum.Enum):
    DRAFT              = "DRAFT"
    SUBMITTED          = "SUBMITTED"
    APPROVED           = "APPROVED"
    REJECTED           = "REJECTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"


class QuoteItemType(str, enum.Enum):
    PART   = "PART"
    LABOR  = "LABOR"
    OTHER  = "OTHER"


class ExecutionApprovalStatus(str, enum.Enum):
    PENDING         = "PENDING"
    ADMIN_APPROVED  = "ADMIN_APPROVED"
    CLIENT_APPROVED = "CLIENT_APPROVED"
    APPROVED        = "APPROVED"
    DISPUTED        = "DISPUTED"


# ── Vehicle (Automóvel) ────────────────────────────────────────────────────

class Vehicle(Base):
    __tablename__ = "vehicles"

    id                   = Column(Integer, primary_key=True, index=True)
    tenant_id            = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    client_id            = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Identification
    plate                = Column(String(20), nullable=False, index=True)
    renavam              = Column(String(20), nullable=True)
    chassis              = Column(String(50), nullable=True)
    brand                = Column(String(100), nullable=False)
    model                = Column(String(100), nullable=False)
    year_model           = Column(Integer, nullable=True)
    year_manufacture     = Column(Integer, nullable=True)
    color                = Column(String(50), nullable=True)
    fuel_type            = Column(Enum(FuelType), nullable=True)
    category             = Column(Enum(VehicleCategory), default=VehicleCategory.CAR)
    usage_type           = Column(String(50), nullable=True)   # FROTA / EXECUTIVO / OPERACIONAL

    # Operation
    mileage_current      = Column(Float, default=0)
    mileage_last_maint   = Column(Float, nullable=True)

    # IPVA
    ipva_value           = Column(Float, nullable=True)
    ipva_due_date        = Column(String(20), nullable=True)   # ISO date string

    # Licensing
    licensing_year       = Column(Integer, nullable=True)
    licensing_due_date   = Column(String(20), nullable=True)
    licensing_paid       = Column(Boolean, default=False)
    dpvat_value          = Column(Float, nullable=True)

    # Insurance
    insurance_policy     = Column(String(100), nullable=True)
    insurance_company    = Column(String(200), nullable=True)
    insurance_expiry     = Column(String(20), nullable=True)
    insurance_value      = Column(Float, nullable=True)

    is_active            = Column(Boolean, default=True)
    notes                = Column(Text, nullable=True)

    # Telemetry
    last_lat             = Column(Float, nullable=True)
    last_lng             = Column(Float, nullable=True)
    last_sync_at         = Column(DateTime, nullable=True)

    created_at           = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at           = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                  onupdate=lambda: datetime.now(timezone.utc))

    client               = relationship("Client")
    fleet_requests       = relationship("FleetRequest", back_populates="vehicle",
                                        foreign_keys="FleetRequest.vehicle_id")
    maintenance_schedules = relationship("MaintenanceSchedule", back_populates="vehicle",
                                         foreign_keys="MaintenanceSchedule.vehicle_id")


# ── BoatRegulatory (Dados Legais da Embarcação) ───────────────────────────

class BoatRegulatory(Base):
    __tablename__ = "boat_regulatory"

    id                      = Column(Integer, primary_key=True, index=True)
    boat_id                 = Column(Integer, ForeignKey("boats.id"), nullable=False, unique=True)

    registration_number     = Column(String(100), nullable=True)
    registration_authority  = Column(String(100), nullable=True)
    registration_expiry     = Column(String(20), nullable=True)
    registration_value      = Column(Float, nullable=True)

    insurance_policy        = Column(String(100), nullable=True)
    insurance_company       = Column(String(200), nullable=True)
    insurance_expiry        = Column(String(20), nullable=True)
    insurance_value         = Column(Float, nullable=True)

    tmc_number              = Column(String(50), nullable=True)
    tmc_expiry              = Column(String(20), nullable=True)
    antf_number             = Column(String(50), nullable=True)
    nav_category            = Column(String(50), nullable=True)
    max_passengers          = Column(Integer, nullable=True)
    gross_tonnage           = Column(Float, nullable=True)
    overall_length          = Column(Float, nullable=True)
    notes                   = Column(Text, nullable=True)
    updated_at              = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                     onupdate=lambda: datetime.now(timezone.utc))

    boat                    = relationship("Boat")


# ── Workshop (Oficina) ─────────────────────────────────────────────────────

class Workshop(Base):
    __tablename__ = "workshops"

    id                  = Column(Integer, primary_key=True, index=True)
    tenant_id           = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    partner_id          = Column(Integer, ForeignKey("partners.id"), nullable=True)

    name                = Column(String(200), nullable=False)
    cnpj                = Column(String(20), nullable=True)
    ie                  = Column(String(50), nullable=True)
    phone               = Column(String(50), nullable=True)
    email               = Column(String(200), nullable=True)
    address             = Column(Text, nullable=True)
    city                = Column(String(100), nullable=True)
    state               = Column(String(10), nullable=True)
    zip_code            = Column(String(20), nullable=True)
    contact_name        = Column(String(200), nullable=True)

    # JSON list of specialties e vehicle types
    specialties         = Column(JSON, default=[])
    vehicle_types       = Column(JSON, default=[])

    rating              = Column(Float, nullable=True)
    max_concurrent_os   = Column(Integer, default=5)
    is_active           = Column(Boolean, default=True)
    notes               = Column(Text, nullable=True)

    # Telemetry
    last_lat            = Column(Float, nullable=True)
    last_lng            = Column(Float, nullable=True)
    last_sync_at        = Column(DateTime, nullable=True)

    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    quotes              = relationship("WorkshopQuote", back_populates="workshop")


# ── FleetRequest (Solicitação de Serviço) ─────────────────────────────────

class FleetRequest(Base):
    __tablename__ = "fleet_requests"

    id                      = Column(Integer, primary_key=True, index=True)
    tenant_id               = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    client_id               = Column(Integer, ForeignKey("clients.id"), nullable=False)
    vehicle_id              = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    boat_id                 = Column(Integer, ForeignKey("boats.id"), nullable=True)

    problem_description     = Column(Text, nullable=False)
    urgency                 = Column(Enum(Urgency), default=Urgency.MEDIUM)
    preferred_date          = Column(String(20), nullable=True)
    photos                  = Column(JSON, default=[])
    status                  = Column(Enum(RequestStatus), default=RequestStatus.OPEN)

    # Assigned workshops (JSON list of workshop IDs, supports multi-quote)
    assigned_workshop_ids   = Column(JSON, default=[])

    # Double approval tracking
    admin_approved_at       = Column(DateTime, nullable=True)
    client_approved_at      = Column(DateTime, nullable=True)

    created_at              = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at              = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                     onupdate=lambda: datetime.now(timezone.utc))

    client                  = relationship("Client")
    vehicle                 = relationship("Vehicle", back_populates="fleet_requests",
                                           foreign_keys=[vehicle_id])
    boat                    = relationship("Boat")
    quotes                  = relationship("WorkshopQuote", back_populates="request",
                                           cascade="all, delete-orphan")
    messages                = relationship("RequestMessage", back_populates="request",
                                           cascade="all, delete-orphan")


# ── WorkshopQuote (Orçamento da Oficina) ──────────────────────────────────

class WorkshopQuote(Base):
    __tablename__ = "workshop_quotes"

    id                  = Column(Integer, primary_key=True, index=True)
    fleet_request_id    = Column(Integer, ForeignKey("fleet_requests.id"), nullable=False)
    workshop_id         = Column(Integer, ForeignKey("workshops.id"), nullable=False)

    technician_name     = Column(String(200), nullable=True)
    diagnosis           = Column(Text, nullable=True)
    estimated_days      = Column(Integer, nullable=True)
    validity_days       = Column(Integer, default=7)

    subtotal_parts      = Column(Float, default=0)
    subtotal_labor      = Column(Float, default=0)
    total_value         = Column(Float, default=0)

    status              = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT)
    rejection_reason    = Column(Text, nullable=True)
    revision_notes      = Column(Text, nullable=True)

    photos_before       = Column(JSON, default=[])
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    submitted_at        = Column(DateTime, nullable=True)

    request             = relationship("FleetRequest", back_populates="quotes")
    workshop            = relationship("Workshop", back_populates="quotes")
    items               = relationship("WorkshopQuoteItem", back_populates="quote",
                                       cascade="all, delete-orphan")
    execution           = relationship("WorkshopExecution", back_populates="quote",
                                       uselist=False, cascade="all, delete-orphan")


# ── WorkshopQuoteItem (Itens do Orçamento) ────────────────────────────────

class WorkshopQuoteItem(Base):
    __tablename__ = "workshop_quote_items"

    id          = Column(Integer, primary_key=True, index=True)
    quote_id    = Column(Integer, ForeignKey("workshop_quotes.id"), nullable=False)
    type        = Column(Enum(QuoteItemType), nullable=False)
    description = Column(String(300), nullable=False)
    part_sku    = Column(String(100), nullable=True)
    quantity    = Column(Float, default=1)
    unit_price  = Column(Float, nullable=False)
    total       = Column(Float, nullable=False)
    notes       = Column(String(300), nullable=True)

    quote       = relationship("WorkshopQuote", back_populates="items")


# ── WorkshopExecution (Execução) ──────────────────────────────────────────

class WorkshopExecution(Base):
    __tablename__ = "workshop_executions"

    id                  = Column(Integer, primary_key=True, index=True)
    quote_id            = Column(Integer, ForeignKey("workshop_quotes.id"), nullable=False, unique=True)
    fleet_request_id    = Column(Integer, ForeignKey("fleet_requests.id"), nullable=False)
    workshop_id         = Column(Integer, ForeignKey("workshops.id"), nullable=False)

    started_at          = Column(DateTime, nullable=True)
    completed_at        = Column(DateTime, nullable=True)

    technician_notes    = Column(Text, nullable=True)
    photos_during       = Column(JSON, default=[])
    photos_after        = Column(JSON, default=[])
    parts_used          = Column(JSON, default=[])  # list of {description, sku, qty, price}
    labor_hours         = Column(Float, nullable=True)
    total_executed      = Column(Float, nullable=True)

    # Double closure approval
    approval_status     = Column(Enum(ExecutionApprovalStatus), default=ExecutionApprovalStatus.PENDING)
    admin_approved_at   = Column(DateTime, nullable=True)
    client_approved_at  = Column(DateTime, nullable=True)
    dispute_reason      = Column(Text, nullable=True)
    closed_at           = Column(DateTime, nullable=True)

    quote               = relationship("WorkshopQuote", back_populates="execution")


# ── FleetClientDetail (Dados Fiscais do Cliente PJ) ───────────────────────

class FleetClientDetail(Base):
    __tablename__ = "fleet_client_details"

    id                  = Column(Integer, primary_key=True, index=True)
    client_id           = Column(Integer, ForeignKey("clients.id"), nullable=False, unique=True)

    company_name        = Column(String(200), nullable=True)
    cnpj                = Column(String(20), nullable=True)
    ie                  = Column(String(50), nullable=True)
    im                  = Column(String(50), nullable=True)
    crt                 = Column(String(10), nullable=True)     # 1=Simples, 2=Presumido, 3=Real

    billing_address     = Column(Text, nullable=True)
    billing_city        = Column(String(100), nullable=True)
    billing_state       = Column(String(10), nullable=True)
    billing_zip         = Column(String(20), nullable=True)

    fleet_size_estimated = Column(Integer, nullable=True)
    contract_type       = Column(String(100), nullable=True)   # MENSAL / AVULSO / ANUAL
    contract_value      = Column(Float, nullable=True)
    contract_start      = Column(String(20), nullable=True)
    contract_end        = Column(String(20), nullable=True)
    payment_terms       = Column(String(200), nullable=True)
    account_manager     = Column(String(200), nullable=True)

    client              = relationship("Client")


# ── MaintenanceSchedule (Plano Preventivo) ────────────────────────────────

class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id              = Column(Integer, primary_key=True, index=True)
    tenant_id       = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    vehicle_id      = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    boat_id         = Column(Integer, ForeignKey("boats.id"), nullable=True)

    service_type    = Column(String(200), nullable=False)    # "Troca de Óleo", "Correia"…
    interval_km     = Column(Float, nullable=True)
    interval_days   = Column(Integer, nullable=True)
    last_done_at    = Column(String(20), nullable=True)
    last_done_km    = Column(Float, nullable=True)
    next_due_at     = Column(String(20), nullable=True)
    next_due_km     = Column(Float, nullable=True)
    status          = Column(String(20), default="OK")       # OK / DUE_SOON / OVERDUE
    notes           = Column(Text, nullable=True)

    vehicle         = relationship("Vehicle", back_populates="maintenance_schedules",
                                   foreign_keys=[vehicle_id])


class RequestMessage(Base):
    __tablename__ = "fleet_request_messages"

    id = Column(Integer, primary_key=True, index=True)
    fleet_request_id = Column(Integer, ForeignKey("fleet_requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    request = relationship("FleetRequest", back_populates="messages")
    user = relationship("User")

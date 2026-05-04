"""Fleet module — Pydantic schemas."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from modules.fleet.models import (
    VehicleCategory, FuelType, RequestStatus, Urgency,
    QuoteStatus, QuoteItemType, ExecutionApprovalStatus,
)


# ── Vehicle ───────────────────────────────────────────────────────────────

class VehicleBase(BaseModel):
    plate: str
    renavam: Optional[str] = None
    chassis: Optional[str] = None
    brand: str
    model: str
    year_model: Optional[int] = None
    year_manufacture: Optional[int] = None
    color: Optional[str] = None
    fuel_type: Optional[FuelType] = None
    category: Optional[VehicleCategory] = VehicleCategory.CAR
    usage_type: Optional[str] = None
    mileage_current: Optional[float] = 0
    mileage_last_maint: Optional[float] = None
    ipva_value: Optional[float] = None
    ipva_due_date: Optional[str] = None
    licensing_year: Optional[int] = None
    licensing_due_date: Optional[str] = None
    licensing_paid: Optional[bool] = False
    dpvat_value: Optional[float] = None
    insurance_policy: Optional[str] = None
    insurance_company: Optional[str] = None
    insurance_expiry: Optional[str] = None
    insurance_value: Optional[float] = None
    notes: Optional[str] = None


class VehicleCreate(VehicleBase):
    client_id: Optional[int] = None


class VehicleUpdate(BaseModel):
    plate: Optional[str] = None
    renavam: Optional[str] = None
    chassis: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year_model: Optional[int] = None
    year_manufacture: Optional[int] = None
    color: Optional[str] = None
    fuel_type: Optional[FuelType] = None
    category: Optional[VehicleCategory] = None
    usage_type: Optional[str] = None
    mileage_current: Optional[float] = None
    mileage_last_maint: Optional[float] = None
    ipva_value: Optional[float] = None
    ipva_due_date: Optional[str] = None
    licensing_year: Optional[int] = None
    licensing_due_date: Optional[str] = None
    licensing_paid: Optional[bool] = None
    dpvat_value: Optional[float] = None
    insurance_policy: Optional[str] = None
    insurance_company: Optional[str] = None
    insurance_expiry: Optional[str] = None
    insurance_value: Optional[float] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class VehicleRead(VehicleBase):
    id: int
    client_id: Optional[int] = None
    last_lat: Optional[float] = None
    last_lng: Optional[float] = None
    last_sync_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── BoatRegulatory ────────────────────────────────────────────────────────

class BoatRegulatoryCreate(BaseModel):
    boat_id: int
    registration_number: Optional[str] = None
    registration_authority: Optional[str] = None
    registration_expiry: Optional[str] = None
    registration_value: Optional[float] = None
    insurance_policy: Optional[str] = None
    insurance_company: Optional[str] = None
    insurance_expiry: Optional[str] = None
    insurance_value: Optional[float] = None
    tmc_number: Optional[str] = None
    tmc_expiry: Optional[str] = None
    antf_number: Optional[str] = None
    nav_category: Optional[str] = None
    max_passengers: Optional[int] = None
    gross_tonnage: Optional[float] = None
    overall_length: Optional[float] = None
    notes: Optional[str] = None


class BoatRegulatoryRead(BoatRegulatoryCreate):
    id: int
    model_config = {"from_attributes": True}


# ── Workshop ──────────────────────────────────────────────────────────────

class WorkshopCreate(BaseModel):
    name: str
    cnpj: Optional[str] = None
    ie: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    contact_name: Optional[str] = None
    specialties: Optional[List[str]] = Field(default_factory=list)
    vehicle_types: Optional[List[str]] = Field(default_factory=list)
    rating: Optional[float] = None
    max_concurrent_os: Optional[int] = 5
    notes: Optional[str] = None
    partner_id: Optional[int] = None


class WorkshopUpdate(BaseModel):
    name: Optional[str] = None
    cnpj: Optional[str] = None
    ie: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    contact_name: Optional[str] = None
    specialties: Optional[List[str]] = None
    vehicle_types: Optional[List[str]] = None
    rating: Optional[float] = None
    max_concurrent_os: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class WorkshopRead(WorkshopCreate):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── FleetRequest ──────────────────────────────────────────────────────────

class FleetRequestCreate(BaseModel):
    vehicle_id: Optional[int] = None
    boat_id: Optional[int] = None
    problem_description: str
    urgency: Optional[Urgency] = Urgency.MEDIUM
    preferred_date: Optional[str] = None
    photos: Optional[List[str]] = Field(default_factory=list)


class FleetRequestAssign(BaseModel):
    workshop_ids: List[int] = Field(..., min_length=1)


class FleetRequestUpdate(BaseModel):
    problem_description: Optional[str] = None
    urgency: Optional[Urgency] = None
    preferred_date: Optional[str] = None
    status: Optional[RequestStatus] = None


class FleetRequestRead(BaseModel):
    id: int
    tenant_id: int
    client_id: int
    vehicle_id: Optional[int] = None
    boat_id: Optional[int] = None
    problem_description: str
    urgency: Urgency
    preferred_date: Optional[str] = None
    photos: List[str] = []
    status: RequestStatus
    assigned_workshop_ids: List[int] = []
    admin_approved_at: Optional[datetime] = None
    client_approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── WorkshopQuoteItem ─────────────────────────────────────────────────────

class QuoteItemCreate(BaseModel):
    type: QuoteItemType
    description: str
    part_sku: Optional[str] = None
    quantity: float = 1
    unit_price: float
    total: float
    notes: Optional[str] = None


class QuoteItemRead(QuoteItemCreate):
    id: int
    model_config = {"from_attributes": True}


# ── WorkshopQuote ─────────────────────────────────────────────────────────

class WorkshopQuoteCreate(BaseModel):
    technician_name: Optional[str] = None
    diagnosis: Optional[str] = None
    estimated_days: Optional[int] = None
    validity_days: Optional[int] = 7
    photos_before: Optional[List[str]] = Field(default_factory=list)
    items: Optional[List[QuoteItemCreate]] = Field(default_factory=list)


class WorkshopQuoteUpdate(BaseModel):
    technician_name: Optional[str] = None
    diagnosis: Optional[str] = None
    estimated_days: Optional[int] = None
    validity_days: Optional[int] = None
    photos_before: Optional[List[str]] = None
    items: Optional[List[QuoteItemCreate]] = None


class WorkshopQuoteRead(BaseModel):
    id: int
    fleet_request_id: int
    workshop_id: int
    technician_name: Optional[str] = None
    diagnosis: Optional[str] = None
    estimated_days: Optional[int] = None
    validity_days: Optional[int] = None
    subtotal_parts: float
    subtotal_labor: float
    total_value: float
    status: QuoteStatus
    rejection_reason: Optional[str] = None
    revision_notes: Optional[str] = None
    photos_before: List[str] = []
    items: List[QuoteItemRead] = []
    created_at: datetime
    submitted_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── WorkshopExecution ─────────────────────────────────────────────────────

class ExecutionUpdate(BaseModel):
    technician_notes: Optional[str] = None
    photos_during: Optional[List[str]] = None
    photos_after: Optional[List[str]] = None
    parts_used: Optional[List[dict]] = None
    labor_hours: Optional[float] = None
    total_executed: Optional[float] = None


class ExecutionRead(BaseModel):
    id: int
    quote_id: int
    fleet_request_id: int
    workshop_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    technician_notes: Optional[str] = None
    photos_during: List[str] = []
    photos_after: List[str] = []
    parts_used: List[dict] = []
    labor_hours: Optional[float] = None
    total_executed: Optional[float] = None
    approval_status: ExecutionApprovalStatus
    admin_approved_at: Optional[datetime] = None
    client_approved_at: Optional[datetime] = None
    dispute_reason: Optional[str] = None
    closed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── FleetClientDetail ─────────────────────────────────────────────────────

class FleetClientDetailCreate(BaseModel):
    company_name: Optional[str] = None
    cnpj: Optional[str] = None
    ie: Optional[str] = None
    im: Optional[str] = None
    crt: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_zip: Optional[str] = None
    fleet_size_estimated: Optional[int] = None
    contract_type: Optional[str] = None
    contract_value: Optional[float] = None
    contract_start: Optional[str] = None
    contract_end: Optional[str] = None
    payment_terms: Optional[str] = None
    account_manager: Optional[str] = None


class FleetClientDetailRead(FleetClientDetailCreate):
    id: int
    client_id: int
    model_config = {"from_attributes": True}


# ── MaintenanceSchedule ───────────────────────────────────────────────────

class MaintenanceScheduleCreate(BaseModel):
    vehicle_id: Optional[int] = None
    boat_id: Optional[int] = None
    service_type: str
    interval_km: Optional[float] = None
    interval_days: Optional[int] = None
    last_done_at: Optional[str] = None
    last_done_km: Optional[float] = None
    next_due_at: Optional[str] = None
    next_due_km: Optional[float] = None
    notes: Optional[str] = None


class MaintenanceScheduleRead(MaintenanceScheduleCreate):
    id: int
    status: str
    model_config = {"from_attributes": True}


# ── Expiry Alert (computed, no DB) ────────────────────────────────────────

class ExpiryAlert(BaseModel):
    type: str  # IPVA, LICENSING, INSURANCE, REGULATORY
    asset_id: int
    asset_name: str
    asset_type: str  # vehicle, boat
    due_date: Optional[str] = None
    days_left: int
    plate: Optional[str] = None


# ── RequestMessage (Chat) ─────────────────────────────────────────────────

class RequestMessageCreate(BaseModel):
    message: str


class RequestMessageRead(BaseModel):
    id: int
    fleet_request_id: int
    user_id: int
    user_name: Optional[str] = None
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}

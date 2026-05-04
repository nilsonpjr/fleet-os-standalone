"""LGPD module schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class ConsentCreate(BaseModel):
    client_id: Optional[int] = None
    email: Optional[str] = None
    source: str
    purpose: str
    consent_text: Optional[str] = None
    ip_address: Optional[str] = None


class ConsentRead(ConsentCreate):
    id: int
    given_at: datetime
    revoked_at: Optional[datetime] = None
    is_active: bool

    model_config = {"from_attributes": True}


class ErasureRequestCreate(BaseModel):
    reason: Optional[str] = None


class ErasureRequestRead(BaseModel):
    id: int
    tenant_id: int
    client_id: int
    status: str
    reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    requested_at: datetime
    sla_deadline: Optional[datetime] = None
    executed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ErasureReview(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


class AuditLogRead(BaseModel):
    id: int
    actor_email: Optional[str] = None
    action: str
    subject_email: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DataExportResponse(BaseModel):
    exported_at: str
    lgpd_basis: str
    personal_data: dict
    boats: list
    service_orders: list


class DataProcessingInfo(BaseModel):
    """Art. 9º LGPD — Information about data processing."""
    controller: str
    controller_contact: str
    dpo_contact: str
    purposes: list[dict]
    third_parties: list[dict]
    retention_policies: list[dict]
    data_subject_rights: list[str]

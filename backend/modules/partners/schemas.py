"""Partners module schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class PartnerBase(BaseModel):
    name: str
    partner_type: str
    company_name: Optional[str] = None
    document: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    rating: Optional[float] = None
    notes: Optional[str] = None


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    partner_type: Optional[str] = None
    company_name: Optional[str] = None
    document: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    rating: Optional[float] = None
    notes: Optional[str] = None


class PartnerRead(PartnerBase):
    id: int
    tenant_id: int
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PartnerQuoteCreate(BaseModel):
    partner_id: int
    service_order_id: Optional[int] = None
    description: str
    amount: Optional[float] = None
    notes: Optional[str] = None


class PartnerQuoteRead(PartnerQuoteCreate):
    id: int
    tenant_id: int
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

"""Orders module schemas."""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


class ServiceItemBase(BaseModel):
    type: str
    description: str
    part_id: Optional[int] = None
    quantity: float = 1
    unit_cost: float = 0
    unit_price: float
    total: float
    category: Optional[str] = None
    subcategory: Optional[str] = None


class ServiceItemCreate(ServiceItemBase):
    pass


class ServiceItemUpdate(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    part_id: Optional[int] = None
    quantity: Optional[float] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None


class ServiceItemRead(ServiceItemBase):
    id: int
    order_id: int

    model_config = {"from_attributes": True}


class OrderNoteCreate(BaseModel):
    text: str


class OrderNoteRead(BaseModel):
    id: int
    order_id: int
    text: str
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ServiceOrderBase(BaseModel):
    boat_id: int
    description: str
    client_id: Optional[int] = None
    engine_id: Optional[int] = None
    diagnosis: Optional[str] = None
    requester: Optional[str] = None
    technician_name: Optional[str] = None
    technician_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    checklist: Optional[Any] = []


class ServiceOrderCreate(ServiceOrderBase):
    items: Optional[List[ServiceItemCreate]] = []


class ServiceOrderUpdate(BaseModel):
    description: Optional[str] = None
    diagnosis: Optional[str] = None
    status: Optional[str] = None
    requester: Optional[str] = None
    technician_name: Optional[str] = None
    technician_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    checklist: Optional[Any] = None


class ServiceOrderRead(ServiceOrderBase):
    id: int
    tenant_id: int
    status: str
    total_value: float
    created_at: Optional[datetime] = None
    items: List[ServiceItemRead] = []
    notes: List[OrderNoteRead] = []
    # Computed properties proxied from relationships
    boat_name: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None

    model_config = {"from_attributes": True}


class TechnicalDeliveryCreate(BaseModel):
    service_order_id: int
    delivery_type: Optional[str] = None
    checklist_data: Optional[Any] = {}
    observations: Optional[str] = None
    client_signature: Optional[str] = None
    technician_signature: Optional[str] = None
    delivered_at: Optional[datetime] = None


class TechnicalDeliveryRead(TechnicalDeliveryCreate):
    id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

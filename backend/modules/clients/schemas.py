"""Clients module schemas."""
from typing import Optional
from pydantic import BaseModel


class ClientBase(BaseModel):
    name: str
    document: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    type: Optional[str] = None
    telegram_id: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    document: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    type: Optional[str] = None
    telegram_id: Optional[str] = None
    is_active: Optional[bool] = None


class ClientRead(ClientBase):
    id: int
    tenant_id: int
    is_active: bool

    model_config = {"from_attributes": True}


class MarinaBase(BaseModel):
    name: str
    address: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    coordinates: Optional[str] = None
    operating_hours: Optional[str] = None


class MarinaCreate(MarinaBase):
    pass


class MarinaRead(MarinaBase):
    id: int
    tenant_id: int

    model_config = {"from_attributes": True}

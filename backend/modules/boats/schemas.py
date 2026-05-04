"""Boats module schemas."""
from typing import Optional, List
from backend_v2.core.schemas import CamelModel


class EngineBase(CamelModel):
    serial_number: str
    motor_number: Optional[str] = None
    model: str
    sale_date: Optional[str] = None
    warranty_status: Optional[str] = None
    warranty_validity: Optional[str] = None
    client_name: Optional[str] = None
    hours: int = 0
    year: Optional[int] = None


class EngineCreate(EngineBase):
    pass


class EngineUpdate(CamelModel):
    id: Optional[int] = None
    serial_number: Optional[str] = None
    motor_number: Optional[str] = None
    model: Optional[str] = None
    sale_date: Optional[str] = None
    warranty_status: Optional[str] = None
    warranty_validity: Optional[str] = None
    client_name: Optional[str] = None
    hours: Optional[int] = None
    year: Optional[int] = None


class EngineRead(EngineBase):
    id: int
    tenant_id: int
    boat_id: int


class BoatBase(CamelModel):
    name: str
    hull_id: str
    client_id: int
    marina_id: Optional[int] = None
    usage_type: Optional[str] = None
    model: Optional[str] = None


class BoatCreate(BoatBase):
    engines: List[EngineCreate] = []


class BoatUpdate(CamelModel):
    name: Optional[str] = None
    hull_id: Optional[str] = None
    client_id: Optional[int] = None
    marina_id: Optional[int] = None
    usage_type: Optional[str] = None
    model: Optional[str] = None
    engines: List[EngineUpdate] = []


class BoatRead(BoatBase):
    id: int
    tenant_id: int
    engines: List[EngineRead] = []

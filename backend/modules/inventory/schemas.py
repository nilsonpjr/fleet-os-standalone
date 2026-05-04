"""Inventory module schemas."""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


class PartBase(BaseModel):
    sku: str
    name: str
    barcode: Optional[str] = None
    quantity: Optional[float] = 0
    cost: Optional[float] = 0
    price: Optional[float] = 0
    min_stock: Optional[float] = 0
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    group: Optional[str] = None
    subgroup: Optional[str] = None
    compatibility: Optional[Any] = None


class PartCreate(PartBase):
    is_published: Optional[bool] = False
    public_title: Optional[str] = None
    public_description: Optional[str] = None
    public_price: Optional[float] = None
    public_compare_at_price: Optional[float] = None
    public_image_url: Optional[str] = None
    public_category: Optional[str] = None
    public_slug: Optional[str] = None
    is_featured: Optional[bool] = False
    show_stock_publicly: Optional[bool] = False
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None


class PartUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    barcode: Optional[str] = None
    quantity: Optional[float] = None
    cost: Optional[float] = None
    price: Optional[float] = None
    min_stock: Optional[float] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    group: Optional[str] = None
    subgroup: Optional[str] = None
    compatibility: Optional[Any] = None
    is_published: Optional[bool] = None
    public_title: Optional[str] = None
    public_description: Optional[str] = None
    public_price: Optional[float] = None
    public_compare_at_price: Optional[float] = None
    public_image_url: Optional[str] = None
    public_category: Optional[str] = None
    public_slug: Optional[str] = None
    is_featured: Optional[bool] = None
    show_stock_publicly: Optional[bool] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None


class PartRead(PartCreate):
    id: int
    tenant_id: int
    last_price_updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StockMovementBase(BaseModel):
    part_id: int
    type: str
    quantity: float
    description: str
    reference_id: Optional[str] = None


class StockMovementCreate(StockMovementBase):
    pass


class StockMovementRead(StockMovementBase):
    id: int
    tenant_id: int
    date: Optional[datetime] = None
    user: Optional[str] = None

    model_config = {"from_attributes": True}


class BulkPublishRequest(BaseModel):
    part_ids: List[int]
    is_published: bool


class QuickSaleItem(BaseModel):
    part_id: int
    quantity: float
    discount_percent: float = 0.0


class QuickSaleRequest(BaseModel):
    items: List[QuickSaleItem]
    payment_method: Optional[str] = None
    client_name: Optional[str] = None
    client_doc: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceKitItemBase(BaseModel):
    type: str
    part_id: Optional[int] = None
    item_description: str
    quantity: float = 1
    unit_price: float = 0


class MaintenanceKitBase(BaseModel):
    name: str
    brand: Optional[str] = None
    engine_model: Optional[str] = None
    interval_hours: Optional[int] = None
    description: Optional[str] = None


class MaintenanceKitCreate(MaintenanceKitBase):
    items: Optional[List[MaintenanceKitItemBase]] = []


class MaintenanceKitRead(MaintenanceKitBase):
    id: int
    tenant_id: int
    items: List[MaintenanceKitItemBase] = []

    model_config = {"from_attributes": True}

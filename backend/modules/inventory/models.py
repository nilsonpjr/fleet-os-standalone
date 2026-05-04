"""
Inventory module — Part, StockMovement, MaintenanceKit, Invoice models.
Tables: parts, stock_movements, maintenance_kits, maintenance_kit_items, invoices
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class MovementType(str, enum.Enum):
    IN_INVOICE = "IN_INVOICE"
    OUT_OS = "OUT_OS"
    ADJUSTMENT_PLUS = "ADJUSTMENT_PLUS"
    ADJUSTMENT_MINUS = "ADJUSTMENT_MINUS"
    RETURN_OS = "RETURN_OS"
    SALE_DIRECT = "SALE_DIRECT"


class ItemType(str, enum.Enum):
    PART = "PART"
    LABOR = "LABOR"


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    sku = Column(String(100), index=True, nullable=False)
    barcode = Column(String(100), nullable=True)
    name = Column(String(200), nullable=False)
    quantity = Column(Float, default=0)
    cost = Column(Float, default=0)
    price = Column(Float, default=0)
    min_stock = Column(Float, default=0)
    location = Column(String(100))
    manufacturer = Column(String(100))
    group = Column(String(100))
    subgroup = Column(String(100))
    compatibility = Column(JSON)
    last_price_updated_at = Column(DateTime, nullable=True)
    # Public catalog fields
    is_published = Column(Boolean, default=False)
    public_title = Column(String(200), nullable=True)
    public_description = Column(Text, nullable=True)
    public_price = Column(Float, nullable=True)
    public_compare_at_price = Column(Float, nullable=True)
    public_image_url = Column(String(500), nullable=True)
    public_category = Column(String(100), nullable=True)
    public_slug = Column(String(200), nullable=True, index=True)
    is_featured = Column(Boolean, default=False)
    show_stock_publicly = Column(Boolean, default=False)
    seo_title = Column(String(200), nullable=True)
    seo_description = Column(Text, nullable=True)

    movements = relationship("StockMovement", back_populates="part")
    service_items = relationship("ServiceItem", back_populates="part")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Float, nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reference_id = Column(String(100))
    description = Column(String(200), nullable=False)
    user = Column(String(200))

    part = relationship("Part", back_populates="movements")


class Invoice(Base):
    """Nota fiscal de entrada (compra de peças)."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    number = Column(String(100), nullable=False)
    supplier = Column(String(200), nullable=False)
    date = Column(DateTime, nullable=False)
    total_value = Column(Float, default=0)
    xml_key = Column(String(200), nullable=True)
    imported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MaintenanceKit(Base):
    __tablename__ = "maintenance_kits"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    brand = Column(String(100))
    engine_model = Column(String(100))
    interval_hours = Column(Integer, nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship("MaintenanceKitItem", back_populates="kit", cascade="all, delete-orphan")


class MaintenanceKitItem(Base):
    __tablename__ = "maintenance_kit_items"

    id = Column(Integer, primary_key=True, index=True)
    kit_id = Column(Integer, ForeignKey("maintenance_kits.id"), nullable=False)
    type = Column(Enum(ItemType), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=True)
    item_description = Column(String(200), nullable=False)
    quantity = Column(Float, default=1)
    unit_price = Column(Float, default=0)

    kit = relationship("MaintenanceKit", back_populates="items")
    part = relationship("Part")

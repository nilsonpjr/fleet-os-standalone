"""Inventory module CRUD."""
import re
from typing import Optional
from unicodedata import normalize
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend_v2.modules.inventory.models import Part, StockMovement, MovementType, MaintenanceKit, MaintenanceKitItem, ItemType
from backend_v2.modules.inventory.schemas import PartCreate, PartUpdate, StockMovementCreate, MaintenanceKitCreate


# --- Parts ---

def get_parts(db: Session, tenant_id: int) -> list[Part]:
    return db.query(Part).filter(Part.tenant_id == tenant_id).all()


def get_part(db: Session, part_id: int, tenant_id: int, lock: bool = False) -> Optional[Part]:
    q = db.query(Part).filter(Part.id == part_id, Part.tenant_id == tenant_id)
    if lock:
        q = q.with_for_update()
    return q.first()


def get_part_by_sku(db: Session, sku: str, tenant_id: int) -> Optional[Part]:
    return db.query(Part).filter(Part.sku == sku, Part.tenant_id == tenant_id).first()


def create_part(db: Session, part: PartCreate, tenant_id: int) -> Part:
    db_part = Part(**part.model_dump(), tenant_id=tenant_id)
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part


def update_part(db: Session, part_id: int, tenant_id: int, part_update: PartUpdate) -> Optional[Part]:
    db_part = get_part(db, part_id, tenant_id)
    if not db_part:
        return None
    for key, value in part_update.model_dump(exclude_unset=True).items():
        setattr(db_part, key, value)
    db.commit()
    db.refresh(db_part)
    return db_part


def delete_part(db: Session, part_id: int, tenant_id: int) -> bool:
    db_part = get_part(db, part_id, tenant_id)
    if not db_part:
        return False
    db.delete(db_part)
    db.commit()
    return True


def bulk_publish_parts(db: Session, part_ids: list[int], is_published: bool, tenant_id: int) -> int:
    parts = db.query(Part).filter(Part.id.in_(part_ids), Part.tenant_id == tenant_id).all()
    for part in parts:
        part.is_published = is_published
        if is_published:
            if not part.public_price or part.public_price == 0:
                part.public_price = part.price
            if not part.public_title:
                part.public_title = part.name
            if not part.public_slug:
                slug = normalize("NFKD", part.name).encode("ascii", "ignore").decode("ascii").lower()
                slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
                part.public_slug = f"{slug}-{part.sku.lower()}"
    db.commit()
    return len(parts)


# --- Stock Movements ---

def get_movements(db: Session, tenant_id: int, part_id: Optional[int] = None) -> list[StockMovement]:
    q = db.query(StockMovement).filter(StockMovement.tenant_id == tenant_id)
    if part_id:
        q = q.filter(StockMovement.part_id == part_id)
    return q.order_by(StockMovement.date.desc()).all()


def create_stock_movement(
    db: Session,
    movement: StockMovementCreate,
    user_name: str,
    tenant_id: int,
    commit: bool = True,
) -> StockMovement:
    part = db.query(Part).filter(Part.id == movement.part_id, Part.tenant_id == tenant_id).first()
    if not part:
        raise ValueError(f"Peça ID {movement.part_id} não encontrada.")

    # Update stock quantity
    mov_type = MovementType(movement.type)
    if mov_type in (MovementType.IN_INVOICE, MovementType.ADJUSTMENT_PLUS, MovementType.RETURN_OS):
        part.quantity += movement.quantity
    else:
        part.quantity = max(0.0, part.quantity - movement.quantity)

    db_mov = StockMovement(
        tenant_id=tenant_id,
        part_id=movement.part_id,
        type=mov_type,
        quantity=movement.quantity,
        description=movement.description,
        reference_id=movement.reference_id,
        user=user_name,
        date=datetime.now(timezone.utc),
    )
    db.add(db_mov)
    if commit:
        db.commit()
        db.refresh(db_mov)
    return db_mov


# --- Maintenance Kits ---

def get_kits(db: Session, tenant_id: int) -> list[MaintenanceKit]:
    return db.query(MaintenanceKit).filter(MaintenanceKit.tenant_id == tenant_id).all()


def create_kit(db: Session, kit: MaintenanceKitCreate, tenant_id: int) -> MaintenanceKit:
    kit_data = kit.model_dump(exclude={"items"})
    db_kit = MaintenanceKit(**kit_data, tenant_id=tenant_id)
    db.add(db_kit)
    db.flush()
    for item_data in (kit.items or []):
        item = MaintenanceKitItem(
            **item_data.model_dump(),
            kit_id=db_kit.id,
        )
        db.add(item)
    db.commit()
    db.refresh(db_kit)
    return db_kit

"""Orders module CRUD."""
from typing import Optional
from sqlalchemy.orm import Session

from modules.orders.models import ServiceOrder, ServiceItem, OrderNote, TechnicalDelivery, OSStatus
from modules.inventory.models import StockMovement, MovementType
from modules.finance.models import Transaction
from modules.orders.schemas import (
    ServiceOrderCreate, ServiceOrderUpdate,
    ServiceItemCreate, OrderNoteCreate,
    TechnicalDeliveryCreate,
)
from datetime import datetime, timezone


def get_orders(db: Session, tenant_id: int, status: Optional[str] = None) -> list[ServiceOrder]:
    q = db.query(ServiceOrder).filter(ServiceOrder.tenant_id == tenant_id)
    if status:
        q = q.filter(ServiceOrder.status == status)
    return q.order_by(ServiceOrder.created_at.desc()).all()


def get_order(db: Session, order_id: int, tenant_id: int) -> Optional[ServiceOrder]:
    return db.query(ServiceOrder).filter(
        ServiceOrder.id == order_id, ServiceOrder.tenant_id == tenant_id
    ).first()


def create_order(db: Session, order: ServiceOrderCreate, tenant_id: int) -> ServiceOrder:
    order_data = order.model_dump(exclude={"items"})
    db_order = ServiceOrder(**order_data, tenant_id=tenant_id)
    db.add(db_order)
    db.flush()
    total = 0.0
    for item_data in (order.items or []):
        item = ServiceItem(**item_data.model_dump(), order_id=db_order.id)
        db.add(item)
        total += item_data.total
    db_order.total_value = total
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order(
    db: Session, order_id: int, tenant_id: int, order_update: ServiceOrderUpdate
) -> Optional[ServiceOrder]:
    db_order = get_order(db, order_id, tenant_id)
    if not db_order:
        return None
    for key, value in order_update.model_dump(exclude_unset=True).items():
        setattr(db_order, key, value)
    db.commit()
    db.refresh(db_order)
    return db_order


def add_order_item(
    db: Session, order_id: int, tenant_id: int, item: ServiceItemCreate
) -> Optional[ServiceOrder]:
    db_order = get_order(db, order_id, tenant_id)
    if not db_order:
        return None
    db_item = ServiceItem(**item.model_dump(), order_id=order_id)
    db.add(db_item)
    db_order.total_value = (db_order.total_value or 0) + item.total
    db.commit()
    db.refresh(db_order)
    return db_order


def remove_order_item(
    db: Session, order_id: int, tenant_id: int, item_id: int
) -> Optional[ServiceOrder]:
    db_order = get_order(db, order_id, tenant_id)
    if not db_order:
        return None
    item = db.query(ServiceItem).filter(
        ServiceItem.id == item_id, ServiceItem.order_id == order_id
    ).first()
    if not item:
        return None
    db_order.total_value = max(0.0, (db_order.total_value or 0) - item.total)
    db.delete(item)
    db.commit()
    db.refresh(db_order)
    return db_order


def add_order_note(
    db: Session, order_id: int, tenant_id: int, note: OrderNoteCreate, user_name: str = ""
) -> Optional[OrderNote]:
    if not get_order(db, order_id, tenant_id):
        return None
    db_note = OrderNote(
        order_id=order_id,
        text=note.text,
        user_name=user_name,
        created_at=datetime.now(timezone.utc),
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def complete_order(db: Session, order_id: int, tenant_id: int) -> Optional[ServiceOrder]:
    db_order = get_order(db, order_id, tenant_id)
    if not db_order or db_order.status == OSStatus.COMPLETED:
        return None

    # Deduct stock for part items
    for item in db_order.items:
        if item.part_id and item.type == "PART":
            from modules.inventory.models import Part
            part = db.query(Part).filter(Part.id == item.part_id).first()
            if part:
                part.quantity = max(0.0, part.quantity - item.quantity)
                mov = StockMovement(
                    tenant_id=tenant_id,
                    part_id=item.part_id,
                    type=MovementType.OUT_OS,
                    quantity=item.quantity,
                    description=f"Saída por OS #{order_id}",
                    reference_id=str(order_id),
                    date=datetime.now(timezone.utc),
                )
                db.add(mov)

    # Generate income transaction
    if (db_order.total_value or 0) > 0:
        txn = Transaction(
            tenant_id=tenant_id,
            description=f"Receita OS #{order_id} - {db_order.boat_name or ''}",
            amount=db_order.total_value,
            type="INCOME",
            category="SERVICOS",
            date=datetime.now(timezone.utc),
            status="PAID",
            order_id=order_id,
        )
        db.add(txn)

    db_order.status = OSStatus.COMPLETED
    db.commit()
    db.refresh(db_order)
    return db_order


def reopen_order(db: Session, order_id: int, tenant_id: int) -> Optional[ServiceOrder]:
    db_order = get_order(db, order_id, tenant_id)
    if not db_order or db_order.status != OSStatus.COMPLETED:
        return None

    # Return parts to stock
    for item in db_order.items:
        if item.part_id and item.type == "PART":
            from modules.inventory.models import Part
            part = db.query(Part).filter(Part.id == item.part_id).first()
            if part:
                part.quantity += item.quantity
                mov = StockMovement(
                    tenant_id=tenant_id,
                    part_id=item.part_id,
                    type=MovementType.RETURN_OS,
                    quantity=item.quantity,
                    description=f"Devolução por reabertura OS #{order_id}",
                    reference_id=str(order_id),
                    date=datetime.now(timezone.utc),
                )
                db.add(mov)

    db_order.status = OSStatus.PENDING
    db.commit()
    db.refresh(db_order)
    return db_order


def get_technical_delivery(
    db: Session, order_id: int, tenant_id: Optional[int] = None
) -> Optional[TechnicalDelivery]:
    return db.query(TechnicalDelivery).filter(
        TechnicalDelivery.service_order_id == order_id
    ).first()


def create_technical_delivery(
    db: Session,
    delivery: TechnicalDeliveryCreate,
    technician_id: int,
    tenant_id: int,
) -> TechnicalDelivery:
    db_delivery = TechnicalDelivery(**delivery.model_dump())
    db.add(db_delivery)
    db.commit()
    db.refresh(db_delivery)
    return db_delivery

"""Orders module router — /orders endpoints."""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.logger import get_logger
from core.auth import create_access_token, verify_token
from modules.auth.models import User, UserRole
from modules.orders.models import ServiceOrder, OSStatus
from modules.orders.schemas import (
    ServiceOrderRead, ServiceOrderCreate, ServiceOrderUpdate,
    ServiceItemCreate, ServiceItemUpdate,
    OrderNoteCreate, OrderNoteRead,
    TechnicalDeliveryCreate, TechnicalDeliveryRead,
)
from modules.orders.crud import (
    get_orders, get_order, create_order, update_order,
    add_order_item, remove_order_item, add_order_note,
    complete_order, reopen_order,
    get_technical_delivery, create_technical_delivery,
)

logger = get_logger("orders_router")
router = APIRouter(prefix="/api/orders", tags=["Ordens de Serviço"])


def _create_approval_token(order_id: int, tenant_id: int) -> str:
    """Creates a short-lived JWT for remote order approval."""
    return create_access_token(
        data={"order_id": order_id, "tenant_id": tenant_id, "purpose": "remote_approval"},
        expires_delta=timedelta(hours=48),
    )


@router.get("", response_model=List[ServiceOrderRead])
def list_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_orders(db, tenant_id=current_user.tenant_id, status=status)


@router.get("/{order_id}", response_model=ServiceOrderRead)
def get_single_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = get_order(db, order_id, tenant_id=current_user.tenant_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada.")
    return order


@router.post("", response_model=ServiceOrderRead)
def create_new_order(
    order: ServiceOrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_order(db, order, tenant_id=current_user.tenant_id)


@router.put("/{order_id}", response_model=ServiceOrderRead)
def update_existing_order(
    order_id: int,
    order_update: ServiceOrderUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = update_order(db, order_id, tenant_id=current_user.tenant_id, order_update=order_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada.")
    return updated


@router.post("/{order_id}/items", response_model=ServiceOrderRead)
def add_item(
    order_id: int,
    item: ServiceItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = add_order_item(db, order_id, tenant_id=current_user.tenant_id, item=item)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada.")
    return order


@router.delete("/{order_id}/items/{item_id}", response_model=ServiceOrderRead)
def delete_item(
    order_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = remove_order_item(db, order_id, tenant_id=current_user.tenant_id, item_id=item_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return updated


@router.put("/{order_id}/items/{item_id}", response_model=ServiceOrderRead)
def update_item(
    order_id: int,
    item_id: int,
    item_update: ServiceItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from modules.orders.models import ServiceItem
    db_item = (
        db.query(ServiceItem)
        .join(ServiceOrder)
        .filter(
            ServiceItem.id == item_id,
            ServiceItem.order_id == order_id,
            ServiceOrder.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not db_item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    for key, value in item_update.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    db.commit()
    updated = get_order(db, order_id, current_user.tenant_id)
    if updated:
        updated.total_value = sum(i.total for i in updated.items)
        db.commit()
        db.refresh(updated)
    return updated


@router.post("/{order_id}/notes", response_model=OrderNoteRead)
def add_note(
    order_id: int,
    note: OrderNoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_note = add_order_note(db, order_id, tenant_id=current_user.tenant_id, note=note, user_name=current_user.name)
    if not new_note:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada.")
    return new_note


@router.put("/{order_id}/complete", response_model=ServiceOrderRead)
def complete_order_endpoint(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"COMPLETE ORDER - user={current_user.email} order={order_id}")
    order = complete_order(db, order_id, tenant_id=current_user.tenant_id)
    if not order:
        raise HTTPException(status_code=400, detail="Não foi possível completar a OS.")
    return order


@router.put("/{order_id}/reopen", response_model=ServiceOrderRead)
def reopen_order_endpoint(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"REOPEN ORDER - user={current_user.email} order={order_id}")
    order = reopen_order(db, order_id, tenant_id=current_user.tenant_id)
    if not order:
        raise HTTPException(status_code=400, detail="Não foi possível reabrir a OS.")
    return order


@router.post("/{order_id}/send-quotation", response_model=ServiceOrderRead)
def send_quotation(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = get_order(db, order_id, tenant_id=current_user.tenant_id)
    if not order:
        raise HTTPException(status_code=404, detail="OS não encontrada.")
    if order.status != OSStatus.QUOTATION:
        order = update_order(db, order_id, current_user.tenant_id, ServiceOrderUpdate(status=OSStatus.QUOTATION.value))
    return order


@router.put("/{order_id}/approve", response_model=ServiceOrderRead)
def approve_remotely(order_id: int, token: str, db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload or payload.get("purpose") != "remote_approval":
        raise HTTPException(status_code=401, detail="Link de aprovação inválido ou expirado.")
    if payload.get("order_id") != order_id:
        raise HTTPException(status_code=403, detail="Token não pertence a esta OS.")
    tenant_id = payload.get("tenant_id")
    order = get_order(db, order_id, tenant_id=tenant_id)
    if not order:
        raise HTTPException(status_code=404, detail="OS não encontrada.")
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    tech = (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.role == UserRole.TECHNICIAN)
        .first()
    )
    updated = update_order(
        db, order_id, tenant_id,
        ServiceOrderUpdate(
            status=OSStatus.APPROVED.value,
            scheduled_at=tomorrow,
            technician_id=tech.id if tech else None,
            technician_name=tech.name if tech else "Técnico Automático (Remoto)",
        ),
    )
    return updated


@router.post("/{order_id}/technical-delivery", response_model=TechnicalDeliveryRead)
def create_delivery(
    order_id: int,
    delivery: TechnicalDeliveryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = get_order(db, order_id, tenant_id=current_user.tenant_id)
    if not order:
        raise HTTPException(status_code=404, detail="OS não encontrada.")
    if get_technical_delivery(db, order_id):
        raise HTTPException(status_code=400, detail="Entrega técnica já existe para esta OS.")
    delivery.service_order_id = order_id
    return create_technical_delivery(db, delivery, technician_id=current_user.id, tenant_id=current_user.tenant_id)

"""Inventory module router — /inventory endpoints."""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.logger import get_logger
from modules.auth.models import User, UserRole
from modules.inventory.models import Part, MovementType
from modules.finance.models import Transaction
from modules.inventory.schemas import (
    PartRead, PartCreate, PartUpdate,
    StockMovementRead, StockMovementCreate,
    BulkPublishRequest, QuickSaleRequest,
    MaintenanceKitRead, MaintenanceKitCreate,
)
from modules.inventory.crud import (
    get_parts, get_part, get_part_by_sku,
    create_part, update_part, delete_part, bulk_publish_parts,
    get_movements, create_stock_movement,
    get_kits, create_kit,
)

logger = get_logger("inventory_router")
router = APIRouter(prefix="/api/inventory", tags=["Inventário"])


# --- Parts ---

@router.get("/parts", response_model=List[PartRead])
def list_parts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_parts(db, tenant_id=current_user.tenant_id)


@router.get("/parts/{part_id}", response_model=PartRead)
def get_single_part(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    part = get_part(db, part_id, tenant_id=current_user.tenant_id)
    if not part:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")
    return part


@router.post("/parts", response_model=PartRead)
def create_new_part(
    part: PartCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if get_part_by_sku(db, part.sku, tenant_id=current_user.tenant_id):
        raise HTTPException(status_code=400, detail="SKU já existe.")
    return create_part(db, part, tenant_id=current_user.tenant_id)


@router.put("/parts/{part_id}", response_model=PartRead)
def update_existing_part(
    part_id: int,
    part_update: PartUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if part_update.sku:
        existing = get_part_by_sku(db, part_update.sku, tenant_id=current_user.tenant_id)
        if existing and existing.id != part_id:
            raise HTTPException(status_code=400, detail="SKU já existe neste inventário.")
    updated = update_part(db, part_id, tenant_id=current_user.tenant_id, part_update=part_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")
    return updated


@router.delete("/parts/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_part(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not delete_part(db, part_id, tenant_id=current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Peça não encontrada.")
    return None


@router.post("/parts/bulk-publish")
def bulk_publish(
    payload: BulkPublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = bulk_publish_parts(db, payload.part_ids, payload.is_published, tenant_id=current_user.tenant_id)
    return {"status": "success", "updated_count": count}


# --- Stock Movements ---

@router.get("/movements", response_model=List[StockMovementRead])
def list_movements(
    part_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_movements(db, tenant_id=current_user.tenant_id, part_id=part_id)


@router.post("/movements", response_model=StockMovementRead)
def create_movement(
    movement: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_stock_movement(db, movement, user_name=current_user.name, tenant_id=current_user.tenant_id)


# --- Quick Sale (PDV) ---

@router.post("/quick-sale")
def process_quick_sale(
    sale: QuickSaleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Technician discount limit
    if current_user.role == UserRole.TECHNICIAN:
        for item in sale.items:
            if item.discount_percent > 10:
                raise HTTPException(status_code=403, detail="Técnicos podem dar até 10% de desconto.")

    # Pre-validate stock
    for item in sale.items:
        part = get_part(db, item.part_id, tenant_id=current_user.tenant_id)
        if not part:
            raise HTTPException(status_code=404, detail=f"Peça ID {item.part_id} não encontrada.")
        if part.quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente para {part.name}.")

    total = 0.0
    items_summary = []

    try:
        for item in sale.items:
            part = get_part(db, item.part_id, tenant_id=current_user.tenant_id, lock=True)
            if part.quantity < item.quantity:
                raise HTTPException(status_code=400, detail=f"Estoque insuficiente (concorrência) para {part.name}.")
            final_price = part.price * (1 - item.discount_percent / 100)
            total += final_price * item.quantity
            mov = StockMovementCreate(
                part_id=part.id,
                type=MovementType.SALE_DIRECT.value,
                quantity=item.quantity,
                description=f"Venda Direta PDV - Desconto: {item.discount_percent}%",
            )
            create_stock_movement(db, mov, user_name=current_user.name, tenant_id=current_user.tenant_id, commit=False)
            items_summary.append(f"{item.quantity}x {part.name}")

        if total > 0:
            txn = Transaction(
                tenant_id=current_user.tenant_id,
                description=f"Venda Balcão ({sale.payment_method or 'DINHEIRO'}): {', '.join(items_summary)[:100]}",
                amount=total,
                type="INCOME",
                category="VENDAS_PECAS",
                date=datetime.now(timezone.utc),
            )
            db.add(txn)

        db.commit()
        return {"status": "success", "total_value": total, "items_count": len(sale.items)}

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro na venda: {exc}")


# --- Maintenance Kits ---

@router.get("/kits", response_model=List[MaintenanceKitRead])
def list_kits(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_kits(db, tenant_id=current_user.tenant_id)


@router.post("/kits", response_model=MaintenanceKitRead)
def create_new_kit(
    kit: MaintenanceKitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_kit(db, kit, tenant_id=current_user.tenant_id)

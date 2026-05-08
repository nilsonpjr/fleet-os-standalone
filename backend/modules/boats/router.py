"""Boats module router — /boats endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from modules.auth.models import User
from modules.boats.schemas import BoatRead, BoatCreate, BoatUpdate
from schemas import Manufacturer, Model
from modules.boats.crud import get_boats, get_boat, create_boat, update_boat, delete_boat
from crud import get_manufacturers, get_models
from modules.config.crud import get_company_info
from core.integrations import trigger_n8n_event

router = APIRouter(prefix="/api/boats", tags=["Embarcações"])


@router.get("", response_model=List[BoatRead])
def list_boats(
    client_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from modules.auth.models import UserRole
    if current_user.role == UserRole.CLIENT:
        client_id = current_user.client_id
    return get_boats(db, tenant_id=current_user.tenant_id, client_id=client_id)


@router.post("", response_model=BoatRead)
def create_new_boat(
    boat: BoatCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_boat = create_boat(db, boat, tenant_id=current_user.tenant_id)
    
    # --- N8N INTEGRATION ---
    company = get_company_info(db, tenant_id=current_user.tenant_id)
    if company and company.n8n_webhook_url:
        boat_data = BoatRead.model_validate(new_boat).model_dump(mode='json')
        background_tasks.add_task(trigger_n8n_event, company.n8n_webhook_url, "boat_created", boat_data)
        
    return new_boat


@router.get("/{boat_id}", response_model=BoatRead)
def get_single_boat(
    boat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    boat = get_boat(db, boat_id, tenant_id=current_user.tenant_id)
    if not boat:
        raise HTTPException(status_code=404, detail="Embarcação não encontrada.")
    return boat


@router.put("/{boat_id}", response_model=BoatRead)
def update_existing_boat(
    boat_id: int,
    boat: BoatUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = update_boat(db, boat_id, tenant_id=current_user.tenant_id, boat_update=boat)
    if not updated:
        raise HTTPException(status_code=404, detail="Embarcação não encontrada.")
        
    # --- N8N INTEGRATION ---
    company = get_company_info(db, tenant_id=current_user.tenant_id)
    if company and company.n8n_webhook_url:
        boat_data = BoatRead.model_validate(updated).model_dump(mode='json')
        background_tasks.add_task(trigger_n8n_event, company.n8n_webhook_url, "boat_updated", boat_data)
        
    return updated


@router.delete("/{boat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_boat(
    boat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not delete_boat(db, boat_id, tenant_id=current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Embarcação não encontrada.")
    return None


@router.get("/catalog/manufacturers", response_model=List[Manufacturer])
def list_engine_manufacturers(
    type: Optional[str] = "ENGINE",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna fabricantes de motores/barcos."""
    return get_manufacturers(db, tenant_id=current_user.tenant_id, type=type)


@router.get("/catalog/manufacturers/{manufacturer_id}/models", response_model=List[Model])
def list_manufacturer_models(
    manufacturer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna modelos de um fabricante específico."""
    return get_models(db, manufacturer_id=manufacturer_id)

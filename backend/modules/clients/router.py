"""Clients module router — /clients and /marinas endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from modules.auth.models import User
from modules.clients.schemas import ClientRead, ClientCreate, ClientUpdate, MarinaRead, MarinaCreate
from modules.clients.crud import (
    get_clients, get_client, create_client, update_client, delete_client,
    get_marinas, create_marina, get_client_by_phone,
)

router = APIRouter(prefix="/api/clients", tags=["Clientes"])


@router.get("", response_model=List[ClientRead])
def list_clients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_clients(db, tenant_id=current_user.tenant_id)


@router.post("", response_model=ClientRead)
def create_new_client(
    client: ClientCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_client(db, client, tenant_id=current_user.tenant_id)


@router.get("/{client_id}", response_model=ClientRead)
def get_single_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = get_client(db, client_id, tenant_id=current_user.tenant_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return client


@router.put("/{client_id}", response_model=ClientRead)
def update_existing_client(
    client_id: int,
    client: ClientUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = update_client(db, client_id, tenant_id=current_user.tenant_id, client_update=client)
    if not updated:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return updated


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = delete_client(db, client_id, tenant_id=current_user.tenant_id)
        if not result:
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    except ValueError as e:
        if str(e) == "SOFT_DELETE":
            raise HTTPException(
                status_code=400,
                detail="Cliente possui barcos/OS. Cadastro desativado (soft-delete).",
            )
        raise
    return None


@router.put("/bind-telegram", response_model=ClientRead)
def bind_telegram(
    phone: str,
    telegram_id: str,
    tenant_id: int,
    db: Session = Depends(get_db),
):
    clean = "".join(filter(str.isdigit, phone))
    client = get_client_by_phone(db, clean[-8:], tenant_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado com este telefone.")
    client.telegram_id = telegram_id
    db.commit()
    db.refresh(client)
    return client


# --- Marinas ---
marina_router = APIRouter(prefix="/api/marinas", tags=["Marinas"])


@marina_router.get("", response_model=List[MarinaRead])
def list_marinas(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_marinas(db, tenant_id=current_user.tenant_id)


@marina_router.post("", response_model=MarinaRead)
def create_new_marina(
    marina: MarinaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_marina(db, marina, tenant_id=current_user.tenant_id)


# Merge marina_router into the module-level router object imported by main.py
router.include_router(marina_router)

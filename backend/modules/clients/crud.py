"""Clients module CRUD."""
from typing import Optional
from sqlalchemy.orm import Session

from modules.clients.models import Client, Marina
from modules.clients.schemas import ClientCreate, ClientUpdate, MarinaCreate


def get_clients(db: Session, tenant_id: int) -> list[Client]:
    return db.query(Client).filter(Client.tenant_id == tenant_id, Client.is_active == True).all()


def get_client(db: Session, client_id: int, tenant_id: int) -> Optional[Client]:
    return db.query(Client).filter(Client.id == client_id, Client.tenant_id == tenant_id).first()


def get_client_by_phone(db: Session, phone_suffix: str, tenant_id: int) -> Optional[Client]:
    return (
        db.query(Client)
        .filter(Client.tenant_id == tenant_id, Client.phone.like(f"%{phone_suffix}"))
        .first()
    )


def create_client(db: Session, client: ClientCreate, tenant_id: int) -> Client:
    db_client = Client(**client.model_dump(), tenant_id=tenant_id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def update_client(
    db: Session, client_id: int, tenant_id: int, client_update: ClientUpdate
) -> Optional[Client]:
    db_client = get_client(db, client_id, tenant_id)
    if not db_client:
        return None
    for key, value in client_update.model_dump(exclude_unset=True).items():
        setattr(db_client, key, value)
    db.commit()
    db.refresh(db_client)
    return db_client


def delete_client(db: Session, client_id: int, tenant_id: int) -> Optional[Client]:
    db_client = get_client(db, client_id, tenant_id)
    if not db_client:
        return None
    # Soft delete if the client has boats or orders
    if db_client.boats:
        db_client.is_active = False
        db.commit()
        raise ValueError("SOFT_DELETE")
    db.delete(db_client)
    db.commit()
    return db_client


# --- Marinas ---

def get_marinas(db: Session, tenant_id: int) -> list[Marina]:
    return db.query(Marina).filter(Marina.tenant_id == tenant_id).all()


def create_marina(db: Session, marina: MarinaCreate, tenant_id: int) -> Marina:
    db_marina = Marina(**marina.model_dump(), tenant_id=tenant_id)
    db.add(db_marina)
    db.commit()
    db.refresh(db_marina)
    return db_marina

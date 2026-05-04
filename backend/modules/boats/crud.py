"""Boats module CRUD."""
from typing import Optional, List
from sqlalchemy.orm import Session

from backend_v2.modules.boats.models import Boat, Engine
from backend_v2.modules.boats.schemas import BoatCreate, BoatUpdate
from backend_v2.modules.orders.models import ServiceOrder


def get_boats(db: Session, tenant_id: int, client_id: Optional[int] = None) -> List[Boat]:
    query = db.query(Boat).filter(Boat.tenant_id == tenant_id)
    if client_id:
        query = query.filter(Boat.client_id == client_id)
    return query.all()


def get_boat(db: Session, boat_id: int, tenant_id: int) -> Optional[Boat]:
    return db.query(Boat).filter(Boat.id == boat_id, Boat.tenant_id == tenant_id).first()


def create_boat(db: Session, boat: BoatCreate, tenant_id: int) -> Boat:
    boat_data = boat.model_dump(exclude={"engines"})
    db_boat = Boat(**boat_data, tenant_id=tenant_id)
    db.add(db_boat)
    db.commit()
    db.refresh(db_boat)
    
    for engine_data in (boat.engines or []):
        db_engine = Engine(**engine_data.model_dump(), boat_id=db_boat.id, tenant_id=tenant_id)
        db.add(db_engine)
    
    if boat.engines:
        db.commit()
        db.refresh(db_boat)
        
    return db_boat


def update_boat(db: Session, boat_id: int, tenant_id: int, boat_update: BoatUpdate) -> Optional[Boat]:
    db_boat = get_boat(db, boat_id, tenant_id)
    if not db_boat:
        return None

    update_data = boat_update.model_dump(exclude_unset=True, exclude={'engines'})
    for key, value in update_data.items():
        setattr(db_boat, key, value)

    if boat_update.engines is not None:
        existing_engine_ids = {engine.id for engine in db_boat.engines}
        incoming_engine_ids = {engine.id for engine in boat_update.engines if engine.id}

        # Deleta motores sumidos apenas quando eles nao possuem historico
        # em ordens de servico. Isso evita quebrar chaves estrangeiras ao
        # editar um barco que ja teve OS vinculada a um motor antigo.
        for eng_id in existing_engine_ids - incoming_engine_ids:
            engine_to_delete = db.query(Engine).filter(
                Engine.id == eng_id,
                Engine.tenant_id == tenant_id
            ).first()
            if engine_to_delete:
                has_service_orders = db.query(ServiceOrder.id).filter(
                    ServiceOrder.engine_id == eng_id,
                    ServiceOrder.tenant_id == tenant_id
                ).first() is not None

                if not has_service_orders:
                    db.delete(engine_to_delete)

        # Atualiza ou cria
        for engine_data in boat_update.engines:
            if engine_data.id:
                db_engine = db.query(Engine).filter(
                    Engine.id == engine_data.id,
                    Engine.tenant_id == tenant_id
                ).first()
                if db_engine:
                    for key, value in engine_data.model_dump(exclude_unset=True).items():
                        setattr(db_engine, key, value)
            else:
                new_engine = Engine(**engine_data.model_dump(exclude={'id'}), boat_id=db_boat.id, tenant_id=tenant_id)
                db.add(new_engine)

    db.commit()
    db.refresh(db_boat)
    return db_boat


def delete_boat(db: Session, boat_id: int, tenant_id: int) -> bool:
    db_boat = get_boat(db, boat_id, tenant_id)
    if not db_boat:
        return False
    
    db.delete(db_boat)
    db.commit()
    return True

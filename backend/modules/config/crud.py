"""Config module CRUD."""
from typing import Optional
from sqlalchemy.orm import Session
from modules.config.models import CompanyInfo, ServiceDefinition
from modules.config.schemas import CompanyInfoUpdate, ServiceDefCreate


def get_company_info(db: Session, tenant_id: int) -> Optional[CompanyInfo]:
    return db.query(CompanyInfo).filter(CompanyInfo.tenant_id == tenant_id).first()


def upsert_company_info(db: Session, tenant_id: int, info: CompanyInfoUpdate) -> CompanyInfo:
    db_info = get_company_info(db, tenant_id)
    if not db_info:
        db_info = CompanyInfo(tenant_id=tenant_id)
        db.add(db_info)
    for k, v in info.model_dump(exclude_unset=True).items():
        setattr(db_info, k, v)
    db.commit()
    db.refresh(db_info)
    return db_info


def get_service_definitions(db: Session, tenant_id: int) -> list[ServiceDefinition]:
    return db.query(ServiceDefinition).filter(ServiceDefinition.tenant_id == tenant_id).all()


def create_service_definition(db: Session, sdef: ServiceDefCreate, tenant_id: int) -> ServiceDefinition:
    db_sdef = ServiceDefinition(**sdef.model_dump(), tenant_id=tenant_id)
    db.add(db_sdef)
    db.commit()
    db.refresh(db_sdef)
    return db_sdef

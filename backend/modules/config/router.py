"""Config module router — /config and /service-definitions endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user, require_admin
from modules.auth.models import User
from modules.config.schemas import CompanyInfoRead, CompanyInfoUpdate, ServiceDefRead, ServiceDefCreate
from modules.config.crud import get_company_info, upsert_company_info, get_service_definitions, create_service_definition

router = APIRouter(prefix="/api/config", tags=["Configurações"])


@router.get("/company", response_model=Optional[CompanyInfoRead])
def get_company(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_company_info(db, tenant_id=current_user.tenant_id)


@router.put("/company", response_model=CompanyInfoRead)
def update_company(
    info: CompanyInfoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return upsert_company_info(db, tenant_id=current_user.tenant_id, info=info)


@router.get("/service-definitions", response_model=List[ServiceDefRead])
def list_service_definitions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_service_definitions(db, tenant_id=current_user.tenant_id)


@router.post("/service-definitions", response_model=ServiceDefRead)
def create_sdef(
    sdef: ServiceDefCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return create_service_definition(db, sdef, tenant_id=current_user.tenant_id)

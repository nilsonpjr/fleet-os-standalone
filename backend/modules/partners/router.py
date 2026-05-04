"""Partners module router — /partners endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend_v2.core.database import get_db
from backend_v2.core.dependencies import get_current_user
from backend_v2.modules.auth.models import User
from backend_v2.modules.partners.schemas import PartnerRead, PartnerCreate, PartnerUpdate, PartnerQuoteRead, PartnerQuoteCreate
from backend_v2.modules.partners.crud import get_partners, get_partner, create_partner, update_partner, get_quotes, create_quote

router = APIRouter(prefix="/api/partners", tags=["Parceiros"])


@router.get("", response_model=List[PartnerRead])
def list_partners(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_partners(db, tenant_id=current_user.tenant_id)


@router.post("", response_model=PartnerRead)
def create_new_partner(
    partner: PartnerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_partner(db, partner, tenant_id=current_user.tenant_id)


@router.get("/{partner_id}", response_model=PartnerRead)
def get_single_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = get_partner(db, partner_id, tenant_id=current_user.tenant_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado.")
    return p


@router.put("/{partner_id}", response_model=PartnerRead)
def update_existing_partner(
    partner_id: int,
    partner: PartnerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = update_partner(db, partner_id, tenant_id=current_user.tenant_id, partner_update=partner)
    if not updated:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado.")
    return updated


@router.get("/quotes", response_model=List[PartnerQuoteRead])
def list_quotes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_quotes(db, tenant_id=current_user.tenant_id)


@router.post("/quotes", response_model=PartnerQuoteRead)
def create_new_quote(
    quote: PartnerQuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_quote(db, quote, tenant_id=current_user.tenant_id)

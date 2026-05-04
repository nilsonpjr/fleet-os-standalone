"""Fiscal module router — /fiscal endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from modules.auth.models import User
from modules.fiscal.schemas import FiscalInvoiceRead, FiscalInvoiceCreate
from modules.fiscal.crud import get_invoices, get_invoice, create_invoice

router = APIRouter(prefix="/api/fiscal", tags=["Fiscal"])


@router.get("/invoices", response_model=List[FiscalInvoiceRead])
def list_invoices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_invoices(db, tenant_id=current_user.tenant_id)


@router.post("/invoices", response_model=FiscalInvoiceRead)
def create_new_invoice(
    invoice: FiscalInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_invoice(db, invoice, tenant_id=current_user.tenant_id)


@router.get("/invoices/{invoice_id}", response_model=FiscalInvoiceRead)
def get_single_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = get_invoice(db, invoice_id, tenant_id=current_user.tenant_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada.")
    return inv

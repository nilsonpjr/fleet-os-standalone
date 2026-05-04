"""Fiscal module CRUD."""
from typing import Optional
from sqlalchemy.orm import Session
from modules.fiscal.models import FiscalInvoice
from modules.fiscal.schemas import FiscalInvoiceCreate


def get_invoices(db: Session, tenant_id: int) -> list[FiscalInvoice]:
    return db.query(FiscalInvoice).filter(FiscalInvoice.tenant_id == tenant_id).all()


def get_invoice(db: Session, invoice_id: int, tenant_id: int) -> Optional[FiscalInvoice]:
    return db.query(FiscalInvoice).filter(
        FiscalInvoice.id == invoice_id, FiscalInvoice.tenant_id == tenant_id
    ).first()


def create_invoice(db: Session, invoice: FiscalInvoiceCreate, tenant_id: int) -> FiscalInvoice:
    db_inv = FiscalInvoice(**invoice.model_dump(), tenant_id=tenant_id)
    db.add(db_inv)
    db.commit()
    db.refresh(db_inv)
    return db_inv

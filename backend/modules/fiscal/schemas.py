"""Fiscal module schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class FiscalInvoiceBase(BaseModel):
    invoice_type: str
    client_id: int
    total_value: float
    net_value: float
    tax_value: Optional[float] = 0
    service_order_id: Optional[int] = None
    transaction_id: Optional[int] = None
    serie: Optional[str] = "1"


class FiscalInvoiceCreate(FiscalInvoiceBase):
    pass


class FiscalInvoiceRead(FiscalInvoiceBase):
    id: int
    tenant_id: int
    invoice_number: Optional[str] = None
    status: str
    issue_date: Optional[datetime] = None
    authorization_date: Optional[datetime] = None
    access_key: Optional[str] = None
    pdf_url: Optional[str] = None

    model_config = {"from_attributes": True}

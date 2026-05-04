"""Finance module schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TransactionBase(BaseModel):
    type: str
    category: str
    description: str
    amount: float
    date: datetime
    status: Optional[str] = "PENDING"
    order_id: Optional[int] = None
    document_number: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    tenant_id: int

    model_config = {"from_attributes": True}

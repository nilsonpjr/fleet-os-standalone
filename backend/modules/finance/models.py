"""
Finance module — Transaction model.
Tables: transactions
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from datetime import datetime, timezone

from core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)       # INCOME | EXPENSE
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String(50), default="PENDING")   # PAID | PENDING | CANCELED
    order_id = Column(Integer, nullable=True)
    document_number = Column(String(100))

"""
Fiscal module — FiscalInvoice model.
Tables: fiscal_invoices
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship

from backend_v2.core.database import Base


class InvoiceType(str, enum.Enum):
    NFE = "NFE"
    NFSE = "NFSE"
    NFCE = "NFCE"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "Rascunho"
    PROCESSING = "Processando"
    AUTHORIZED = "Autorizada"
    CANCELED = "Cancelada"
    REJECTED = "Rejeitada"
    ERROR = "Erro"


class FiscalInvoice(Base):
    __tablename__ = "fiscal_invoices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    invoice_type = Column(Enum(InvoiceType), nullable=False)
    invoice_number = Column(String(50), nullable=True)
    serie = Column(String(10), default="1")
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    total_value = Column(Float, nullable=False)
    tax_value = Column(Float, default=0)
    net_value = Column(Float, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    issue_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    authorization_date = Column(DateTime, nullable=True)
    api_provider = Column(String(50), nullable=True)
    api_reference = Column(String(100), nullable=True)
    access_key = Column(String(44), nullable=True)
    xml_content = Column(Text, nullable=True)
    pdf_url = Column(String(500), nullable=True)
    authorization_protocol = Column(String(100), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tenant = relationship("Tenant")
    service_order = relationship("ServiceOrder", back_populates="fiscal_invoices")
    transaction = relationship("Transaction")
    client = relationship("Client")

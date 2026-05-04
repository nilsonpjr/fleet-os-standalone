"""
LGPD module models — Mare Alta ERP
Implements:
- ConsentRecord: tracks consent for each data subject
- AuditLog: immutable trail of personal data access/modification
- ErasureRequest: formal erasure requests with 15-day SLA
- DataRetentionPolicy: configurable retention periods per data category
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey
from backend_v2.core.database import Base


class ConsentSource(str, enum.Enum):
    ERP_MANUAL = "ERP_MANUAL"         # Consent registered by ERP operator
    PUBLIC_SITE = "PUBLIC_SITE"       # Consent from public website form
    N8N_AUTOMATION = "N8N_AUTOMATION" # Consent via automation webhook
    IMPORT = "IMPORT"                 # Consent from data import


class ConsentPurpose(str, enum.Enum):
    SERVICE_CONTRACT = "SERVICE_CONTRACT"   # Execution of service contract
    MARKETING = "MARKETING"                 # Marketing / newsletter
    ANALYTICS = "ANALYTICS"                 # Usage analytics
    THIRD_PARTY = "THIRD_PARTY"             # Sharing with third parties


class ErasureStatus(str, enum.Enum):
    PENDING = "PENDING"       # Request received, awaiting review
    APPROVED = "APPROVED"     # Approved, awaiting execution
    EXECUTED = "EXECUTED"     # Anonymization completed
    REJECTED = "REJECTED"     # Rejected (legal retention obligation applies)


class AuditAction(str, enum.Enum):
    DATA_EXPORT = "DATA_EXPORT"           # Titular accessed their data
    PORTABILITY = "PORTABILITY"           # Portability request
    ERASURE_REQUESTED = "ERASURE_REQUESTED"
    ERASURE_EXECUTED = "ERASURE_EXECUTED"
    CONSENT_GIVEN = "CONSENT_GIVEN"
    CONSENT_REVOKED = "CONSENT_REVOKED"
    DATA_ACCESSED = "DATA_ACCESSED"       # Admin/operator accessed PII
    DATA_CORRECTED = "DATA_CORRECTED"     # Correction of personal data


class ConsentRecord(Base):
    """
    Tracks consent given by a data subject (titular).
    Art. 7º, I and Art. 9º, LGPD.
    """
    __tablename__ = "lgpd_consent_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    email = Column(String(200), index=True)           # If client not yet in DB
    source = Column(Enum(ConsentSource), nullable=False)
    purpose = Column(Enum(ConsentPurpose), nullable=False)
    consent_text = Column(Text)                        # Exact text shown to user
    ip_address = Column(String(50))
    given_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)


class AuditLog(Base):
    """
    Immutable audit trail of all operations involving personal data.
    Art. 37 and Art. 46, LGPD.
    """
    __tablename__ = "lgpd_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who performed action
    actor_email = Column(String(200))                 # Denormalized for immutability
    action = Column(Enum(AuditAction), nullable=False)
    subject_client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    subject_email = Column(String(200))               # Denormalized for immutability
    details = Column(Text)                            # JSON or description
    ip_address = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ErasureRequest(Base):
    """
    Formal request to erase / anonymize personal data.
    Art. 18, IV, LGPD — 15-day SLA.
    """
    __tablename__ = "lgpd_erasure_requests"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    status = Column(Enum(ErasureStatus), default=ErasureStatus.PENDING)
    reason = Column(Text)                             # Reason from the titular
    rejection_reason = Column(Text, nullable=True)    # Reason if rejected
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=True) # requested_at + 15 days

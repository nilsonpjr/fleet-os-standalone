"""LGPD module CRUD."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from backend_v2.modules.lgpd.models import (
    ConsentRecord, AuditLog, ErasureRequest,
    ConsentSource, ConsentPurpose, AuditAction, ErasureStatus,
)
from backend_v2.modules.lgpd.schemas import ConsentCreate, ErasureRequestCreate


ERASURE_SLA_DAYS = 15


def record_consent(db: Session, tenant_id: int, data: ConsentCreate) -> ConsentRecord:
    record = ConsentRecord(
        tenant_id=tenant_id,
        client_id=data.client_id,
        email=data.email,
        source=ConsentSource(data.source),
        purpose=ConsentPurpose(data.purpose),
        consent_text=data.consent_text,
        ip_address=data.ip_address,
        given_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def revoke_consent(db: Session, client_id: int, tenant_id: int) -> int:
    """Revokes all active consents for a client. Returns count revoked."""
    records = db.query(ConsentRecord).filter(
        ConsentRecord.client_id == client_id,
        ConsentRecord.tenant_id == tenant_id,
        ConsentRecord.is_active == True,  # noqa: E712
    ).all()
    for r in records:
        r.is_active = False
        r.revoked_at = datetime.now(timezone.utc)
        db.add(r)
    db.commit()
    return len(records)


def log_audit(
    db: Session,
    tenant_id: int,
    action: AuditAction,
    actor_user_id: Optional[int] = None,
    actor_email: Optional[str] = None,
    subject_client_id: Optional[int] = None,
    subject_email: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        action=action,
        subject_client_id=subject_client_id,
        subject_email=subject_email,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_audit_logs(db: Session, tenant_id: int, limit: int = 100) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )


def create_erasure_request(
    db: Session,
    tenant_id: int,
    client_id: int,
    data: ErasureRequestCreate,
) -> ErasureRequest:
    now = datetime.now(timezone.utc)
    req = ErasureRequest(
        tenant_id=tenant_id,
        client_id=client_id,
        reason=data.reason,
        status=ErasureStatus.PENDING,
        requested_at=now,
        sla_deadline=now + timedelta(days=ERASURE_SLA_DAYS),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_erasure_requests(db: Session, tenant_id: int) -> list[ErasureRequest]:
    return (
        db.query(ErasureRequest)
        .filter(ErasureRequest.tenant_id == tenant_id)
        .order_by(ErasureRequest.requested_at.desc())
        .all()
    )


def review_erasure_request(
    db: Session,
    request_id: int,
    tenant_id: int,
    reviewer_id: int,
    approved: bool,
    rejection_reason: Optional[str] = None,
) -> Optional[ErasureRequest]:
    req = db.query(ErasureRequest).filter(
        ErasureRequest.id == request_id,
        ErasureRequest.tenant_id == tenant_id,
        ErasureRequest.status == ErasureStatus.PENDING,
    ).first()
    if not req:
        return None
    now = datetime.now(timezone.utc)
    req.reviewed_by_user_id = reviewer_id
    req.reviewed_at = now
    if approved:
        req.status = ErasureStatus.APPROVED
    else:
        req.status = ErasureStatus.REJECTED
        req.rejection_reason = rejection_reason
    db.commit()
    db.refresh(req)
    return req


def execute_erasure(
    db: Session,
    request_id: int,
    tenant_id: int,
) -> Optional[ErasureRequest]:
    """Executes anonymization after approval."""
    from backend_v2.modules.lgpd.anonymizer import anonymize_client

    req = db.query(ErasureRequest).filter(
        ErasureRequest.id == request_id,
        ErasureRequest.tenant_id == tenant_id,
        ErasureRequest.status == ErasureStatus.APPROVED,
    ).first()
    if not req:
        return None

    success = anonymize_client(db, req.client_id, tenant_id)
    if success:
        req.status = ErasureStatus.EXECUTED
        req.executed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(req)
    return req

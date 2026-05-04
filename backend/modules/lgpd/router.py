"""
LGPD module router — /lgpd endpoints.

Implements Art. 18 LGPD — Rights of Data Subjects:
  I   — Confirmation of processing
  II  — Access to personal data
  III — Correction of inaccurate data (handled by existing PUT /clients/{id})
  IV  — Anonymization / blocking
  V   — Portability
  VIII — Information about sharing
  IX  — Revocation of consent

All sensitive operations are logged to AuditLog.
"""
import json
import csv
import io
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user, require_admin
from core.logger import get_logger
from modules.auth.models import User
from modules.lgpd.schemas import (
    ConsentCreate, ConsentRead,
    ErasureRequestCreate, ErasureRequestRead, ErasureReview,
    AuditLogRead, DataProcessingInfo,
)
from modules.lgpd.crud import (
    record_consent, revoke_consent, log_audit,
    get_audit_logs, create_erasure_request,
    get_erasure_requests, review_erasure_request, execute_erasure,
)
from modules.lgpd.models import AuditAction
from modules.lgpd.anonymizer import build_data_export

logger = get_logger("lgpd_router")
router = APIRouter(prefix="/lgpd", tags=["LGPD — Privacidade"])


# ─── Art. 18, II — Access / Data Export ────────────────────────────────────

@router.get("/data-export/{client_id}")
def export_client_data(
    client_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all personal data held about a client (JSON).
    Fulfills right of access — Art. 18, II, LGPD.
    """
    data = build_data_export(db, client_id, tenant_id=current_user.tenant_id)
    if not data:
        raise HTTPException(status_code=404, detail="Titular não encontrado.")

    log_audit(
        db,
        tenant_id=current_user.tenant_id,
        action=AuditAction.DATA_EXPORT,
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        subject_client_id=client_id,
        details="Data export requested via API",
        ip_address=request.client.host if request.client else None,
    )
    logger.info(f"LGPD DATA EXPORT: user={current_user.email} client={client_id}")
    return data


# ─── Art. 18, V — Portability (CSV) ────────────────────────────────────────

@router.get("/portability/{client_id}")
def export_portability_csv(
    client_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns personal data as a downloadable CSV file.
    Fulfills right of portability — Art. 18, V, LGPD.
    """
    data = build_data_export(db, client_id, tenant_id=current_user.tenant_id)
    if not data:
        raise HTTPException(status_code=404, detail="Titular não encontrado.")

    log_audit(
        db,
        tenant_id=current_user.tenant_id,
        action=AuditAction.PORTABILITY,
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        subject_client_id=client_id,
        ip_address=request.client.host if request.client else None,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["campo", "valor"])
    for key, value in data.get("personal_data", {}).items():
        writer.writerow([key, value])
    writer.writerow([])
    writer.writerow(["embarcacoes", json.dumps(data.get("boats", []), ensure_ascii=False)])
    writer.writerow(["ordens_servico", json.dumps(data.get("service_orders", []), ensure_ascii=False)])
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=lgpd_portabilidade_cliente_{client_id}.csv"},
    )


# ─── Art. 18, IV — Erasure Request ─────────────────────────────────────────

@router.post("/erase/{client_id}", response_model=ErasureRequestRead, status_code=201)
def request_erasure(
    client_id: int,
    data: ErasureRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a formal erasure / anonymization request with 15-day SLA.
    Art. 18, IV, LGPD.
    """
    # Verify client belongs to tenant
    from modules.clients.models import Client
    client = db.query(Client).filter(
        Client.id == client_id, Client.tenant_id == current_user.tenant_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Titular não encontrado.")

    req = create_erasure_request(db, tenant_id=current_user.tenant_id, client_id=client_id, data=data)
    log_audit(
        db,
        tenant_id=current_user.tenant_id,
        action=AuditAction.ERASURE_REQUESTED,
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        subject_client_id=client_id,
        subject_email=client.email,
        details=f"Erasure request #{req.id} created. Reason: {data.reason or 'N/A'}",
        ip_address=request.client.host if request.client else None,
    )
    logger.info(f"LGPD ERASURE REQUEST: user={current_user.email} client={client_id} request={req.id}")
    return req


@router.get("/erase", response_model=List[ErasureRequestRead])
def list_erasure_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Lists all pending/completed erasure requests (admin only)."""
    return get_erasure_requests(db, tenant_id=current_user.tenant_id)


@router.put("/erase/{request_id}/review", response_model=ErasureRequestRead)
def review_erasure(
    request_id: int,
    review: ErasureReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin reviews (approves or rejects) an erasure request."""
    req = review_erasure_request(
        db, request_id,
        tenant_id=current_user.tenant_id,
        reviewer_id=current_user.id,
        approved=review.approved,
        rejection_reason=review.rejection_reason,
    )
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada ou já processada.")
    logger.info(f"LGPD ERASURE REVIEW: request={request_id} approved={review.approved} by={current_user.email}")
    return req


@router.post("/erase/{request_id}/execute", response_model=ErasureRequestRead)
def execute_erasure_endpoint(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Executes anonymization after approved erasure request.
    Irreversible operation — protected by admin role.
    """
    req = execute_erasure(db, request_id, tenant_id=current_user.tenant_id)
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada ou não aprovada.")

    log_audit(
        db,
        tenant_id=current_user.tenant_id,
        action=AuditAction.ERASURE_EXECUTED,
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        subject_client_id=req.client_id,
        details=f"Erasure request #{request_id} executed. Client anonymized.",
        ip_address=request.client.host if request.client else None,
    )
    logger.info(f"LGPD ERASURE EXECUTED: request={request_id} client={req.client_id} by={current_user.email}")
    return req


# ─── Consent (Art. 7º, I) ───────────────────────────────────────────────────

@router.post("/consent", response_model=ConsentRead, status_code=201)
def register_consent(
    data: ConsentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Records explicit consent from a data subject."""
    if not data.ip_address and request.client:
        data.ip_address = request.client.host
    record = record_consent(db, tenant_id=current_user.tenant_id, data=data)
    log_audit(
        db,
        tenant_id=current_user.tenant_id,
        action=AuditAction.CONSENT_GIVEN,
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        subject_client_id=data.client_id,
        subject_email=data.email,
        details=f"Consent for purpose={data.purpose} source={data.source}",
    )
    return record


@router.post("/consent/revoke/{client_id}")
def revoke_client_consent(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revokes all active consents for a client. Art. 18, IX, LGPD."""
    count = revoke_consent(db, client_id=client_id, tenant_id=current_user.tenant_id)
    log_audit(
        db,
        tenant_id=current_user.tenant_id,
        action=AuditAction.CONSENT_REVOKED,
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        subject_client_id=client_id,
        details=f"{count} consent record(s) revoked.",
    )
    return {"status": "success", "revoked_count": count}


# ─── Art. 9º — Data Processing Info ────────────────────────────────────────

@router.get("/data-processing-info", response_model=DataProcessingInfo)
def get_data_processing_info(current_user: User = Depends(get_current_user)):
    """
    Returns information about data processing activities.
    Art. 9º, LGPD — the controller must inform purposes, bases, third parties.
    """
    return {
        "controller": "Mare Alta Náutica (via Viverdi ERP)",
        "controller_contact": "contato@marealta.com.br",
        "dpo_contact": "privacidade@marealta.com.br",
        "purposes": [
            {"purpose": "Execução do contrato de serviço náutico", "legal_basis": "Art. 7º, V — LGPD"},
            {"purpose": "Cumprimento de obrigação legal / fiscal", "legal_basis": "Art. 7º, II — LGPD"},
            {"purpose": "Legítimo interesse (leads do site)", "legal_basis": "Art. 7º, IX — LGPD"},
        ],
        "third_parties": [
            {"name": "Mercury Marine (portal)", "purpose": "Consulta de preços / garantia de motores", "country": "Brasil"},
            {"name": "n8n (automação)", "purpose": "Notificações e automação de fluxo", "country": "Brasil"},
        ],
        "retention_policies": [
            {"data_type": "Dados de clientes ativos", "retention": "Duração do contrato + 5 anos (CTN Art. 195)"},
            {"data_type": "Leads do site (sem conversão)", "retention": "6 meses"},
            {"data_type": "Logs de autenticação", "retention": "90 dias"},
            {"data_type": "Registros fiscais / financeiros", "retention": "5 anos (obrigação legal)"},
            {"data_type": "Dados anonimizados", "retention": "Indefinido (não são dados pessoais)"},
        ],
        "data_subject_rights": [
            "I — Confirmação da existência de tratamento",
            "II — Acesso aos dados (GET /lgpd/data-export/{client_id})",
            "III — Correção (PUT /clients/{id})",
            "IV — Anonimização (POST /lgpd/erase/{client_id})",
            "V — Portabilidade (GET /lgpd/portability/{client_id})",
            "VIII — Informação sobre compartilhamento (GET /lgpd/data-processing-info)",
            "IX — Revogação de consentimento (POST /lgpd/consent/revoke/{client_id})",
        ],
    }


# ─── Audit Log (admin only) ─────────────────────────────────────────────────

@router.get("/audit-log", response_model=List[AuditLogRead])
def list_audit_log(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Returns LGPD audit trail (admin only). Art. 37, LGPD."""
    return get_audit_logs(db, tenant_id=current_user.tenant_id, limit=limit)

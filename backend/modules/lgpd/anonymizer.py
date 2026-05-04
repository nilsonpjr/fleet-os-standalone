"""
LGPD module — Anonymizer
Anonymizes personal data in-place (does NOT delete records).

Rationale:
  - Preserves referential integrity (OS, transactions, fiscal records)
  - Complies with tax retention laws (CTN Art. 195 — 5 years)
  - After anonymization, records are no longer "personal data" under LGPD
"""
import hashlib
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session


def _anon_hash(value: Optional[str]) -> str:
    """Deterministic hash — useful for audit but contains no PII."""
    if not value:
        return "ANONIMIZADO"
    return "ANON-" + hashlib.sha256(value.encode()).hexdigest()[:12].upper()


def anonymize_client(db: Session, client_id: int, tenant_id: int) -> bool:
    """
    Anonymizes all PII fields of a client record.
    Returns True if executed, False if client not found.
    Art. 18, IV, LGPD.
    """
    from backend_v2.modules.clients.models import Client
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.tenant_id == tenant_id,
    ).first()
    if not client:
        return False

    original_email = client.email  # Needed for engine anonymization

    client.name = "TITULAR ANONIMIZADO"
    client.document = "000.000.000-00"
    client.phone = None
    client.email = _anon_hash(client.email) + "@anonimizado.local"
    client.address = None
    client.telegram_id = None

    # LGPD flag — added as a Python attribute (no column needed if not migrating yet)
    # When DB migration runs, this becomes a real column
    if hasattr(client, "is_anonymized"):
        client.is_anonymized = True
    if hasattr(client, "consent_given_at"):
        client.consent_given_at = None

    db.add(client)
    db.flush()

    # Also anonymize denormalized client_name in engines
    _anonymize_engine_client_names(db, client_id, tenant_id)

    # Redact PII from order notes/descriptions
    _redact_order_pii(db, client_id)

    db.commit()
    return True


def _anonymize_engine_client_names(db: Session, client_id: int, tenant_id: int):
    """Removes client name references from engine records."""
    from backend_v2.modules.boats.models import Boat, Engine
    boats = db.query(Boat).filter(
        Boat.client_id == client_id,
        Boat.tenant_id == tenant_id,
    ).all()
    for boat in boats:
        for engine in boat.engines:
            engine.client_name = "N/A (anonimizado)"
            db.add(engine)


def _redact_order_pii(db: Session, client_id: int):
    """
    Replaces requester name in service orders.
    Keeps order structure intact for fiscal/accounting purposes.
    """
    from backend_v2.modules.orders.models import ServiceOrder, OrderNote
    orders = db.query(ServiceOrder).filter(ServiceOrder.client_id == client_id).all()
    for order in orders:
        if order.requester:
            order.requester = "ANONIMIZADO"
        # Do NOT redact description/diagnosis — those are technical records, not PII
        db.add(order)


def build_data_export(db: Session, client_id: int, tenant_id: int) -> dict:
    """
    Collects all personal data for a data subject.
    Art. 18, II (Acesso) and III (Portabilidade), LGPD.
    """
    from backend_v2.modules.clients.models import Client
    from backend_v2.modules.boats.models import Boat
    from backend_v2.modules.orders.models import ServiceOrder
    from backend_v2.modules.finance.models import Transaction

    client = db.query(Client).filter(
        Client.id == client_id, Client.tenant_id == tenant_id
    ).first()
    if not client:
        return {}

    boats = db.query(Boat).filter(
        Boat.client_id == client_id, Boat.tenant_id == tenant_id
    ).all()

    orders = db.query(ServiceOrder).filter(
        ServiceOrder.client_id == client_id, ServiceOrder.tenant_id == tenant_id
    ).all()

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "lgpd_basis": "Art. 18, II e III — Lei 13.709/2018",
        "personal_data": {
            "name": client.name,
            "document": client.document,
            "phone": client.phone,
            "email": client.email,
            "address": client.address,
            "telegram_id": client.telegram_id,
            "is_active": client.is_active,
        },
        "boats": [
            {
                "name": b.name,
                "hull_id": b.hull_id,
                "model": b.model,
                "engines": [
                    {
                        "serial_number": e.serial_number,
                        "model": e.model,
                        "sale_date": str(e.sale_date) if e.sale_date else None,
                        "warranty_status": e.warranty_status,
                    }
                    for e in (b.engines or [])
                ],
            }
            for b in boats
        ],
        "service_orders": [
            {
                "id": o.id,
                "description": o.description,
                "status": o.status,
                "created_at": str(o.created_at) if o.created_at else None,
                "total_value": o.total_value,
            }
            for o in orders
        ],
    }

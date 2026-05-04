"""Partners module CRUD."""
from typing import Optional
from sqlalchemy.orm import Session
from backend_v2.modules.partners.models import Partner, PartnerQuote
from backend_v2.modules.partners.schemas import PartnerCreate, PartnerUpdate, PartnerQuoteCreate


def get_partners(db: Session, tenant_id: int) -> list[Partner]:
    return db.query(Partner).filter(Partner.tenant_id == tenant_id).all()


def get_partner(db: Session, partner_id: int, tenant_id: int) -> Optional[Partner]:
    return db.query(Partner).filter(Partner.id == partner_id, Partner.tenant_id == tenant_id).first()


def create_partner(db: Session, partner: PartnerCreate, tenant_id: int) -> Partner:
    db_p = Partner(**partner.model_dump(), tenant_id=tenant_id)
    db.add(db_p)
    db.commit()
    db.refresh(db_p)
    return db_p


def update_partner(db: Session, partner_id: int, tenant_id: int, partner_update: PartnerUpdate) -> Optional[Partner]:
    db_p = get_partner(db, partner_id, tenant_id)
    if not db_p:
        return None
    for k, v in partner_update.model_dump(exclude_unset=True).items():
        setattr(db_p, k, v)
    db.commit()
    db.refresh(db_p)
    return db_p


def get_quotes(db: Session, tenant_id: int) -> list[PartnerQuote]:
    return db.query(PartnerQuote).filter(PartnerQuote.tenant_id == tenant_id).all()


def create_quote(db: Session, quote: PartnerQuoteCreate, tenant_id: int) -> PartnerQuote:
    db_q = PartnerQuote(**quote.model_dump(), tenant_id=tenant_id)
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q

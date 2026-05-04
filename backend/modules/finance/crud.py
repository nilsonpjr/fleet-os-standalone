"""Finance module CRUD."""
from sqlalchemy.orm import Session
from backend_v2.modules.finance.models import Transaction
from backend_v2.modules.finance.schemas import TransactionCreate


def get_transactions(db: Session, tenant_id: int) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.tenant_id == tenant_id)
        .order_by(Transaction.date.desc())
        .all()
    )


def create_transaction(db: Session, transaction: TransactionCreate, tenant_id: int) -> Transaction:
    db_txn = Transaction(**transaction.model_dump(), tenant_id=tenant_id)
    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)
    return db_txn

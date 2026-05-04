"""
Database configuration for 
Sets up SQLAlchemy engine, session factory, Base class and tenant-aware RLS middleware.
Same logic as backend/database.py — rewritten with updated imports.
"""
import os
import re
from typing import Optional, List, Tuple
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from core.logger import get_logger

logger = get_logger("database")

# Load .env — look in the current directory
_env_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    ".env",
)
load_dotenv(_env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

# Sanitize: Remove pgbouncer parameter which is incompatible with psycopg2/SQLAlchemy
if DATABASE_URL and "pgbouncer" in DATABASE_URL:
    # Remove pgbouncer=... regardless of where it is in the query string
    DATABASE_URL = re.sub(r'(\?|&)pgbouncer=[^&]*', '', DATABASE_URL)
    # Fix potential broken URL (e.g. ?& or trailing ?)
    DATABASE_URL = DATABASE_URL.replace("?&", "?").rstrip("?")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL não está definida. Configure a conexão com o banco de dados."
    )

if DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy requires postgresql:// instead of postgres://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- TENANT ROW-LEVEL SECURITY (Application Layer) ---

def _get_tenant_id() -> Optional[int]:
    """Retrieve current tenant_id from context (thread-local or ContextVar)."""
    try:
        from core.context import get_tenant_id
        return get_tenant_id()
    except ImportError:
        return None


@event.listens_for(SessionLocal, "do_orm_execute")
def _rls_tenant_filter(orm_execute_state):
    """Automatically adds WHERE tenant_id = X to every SELECT query."""
    tenant_id = _get_tenant_id()
    if (
        tenant_id is not None
        and orm_execute_state.is_select
        and not orm_execute_state.is_column_load
        and not orm_execute_state.is_relationship_load
    ):
        mapper = orm_execute_state.bind_mapper
        if mapper and hasattr(mapper.class_, "tenant_id"):
            orm_execute_state.statement = orm_execute_state.statement.filter(
                mapper.class_.tenant_id == tenant_id
            )


# --- AUTO MIGRATION HELPER ---

def ensure_columns(table_name: str, columns_to_add: List[Tuple[str, str]]) -> None:
    """
    Adds new columns to an existing table if they don't exist yet.
    Replaces Alembic for simple schema evolution without downtime risk.
    """
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        logger.error(f"AUTO-MIGRATION: Nome de tabela inválido: {table_name}")
        return

    inspector = inspect(engine)
    try:
        existing = [col["name"] for col in inspector.get_columns(table_name)]
        with engine.connect() as conn:
            modified = False
            for col_name, col_type in columns_to_add:
                if not re.match(r"^[a-zA-Z0-9_]+$", col_name):
                    logger.error(f"AUTO-MIGRATION: Nome de coluna inválido: {col_name}")
                    continue
                if col_name not in existing:
                    logger.info(f"AUTO-MIGRATION: Adding {col_name} to {table_name}")
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                    modified = True
            if modified:
                conn.commit()
    except Exception as exc:
        logger.error(f"AUTO-MIGRATION ERROR in {table_name}: {exc}", exc_info=True)

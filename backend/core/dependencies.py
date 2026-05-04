"""
FastAPI dependency providers for 
Provides: get_db, get_current_user, get_tenant_db, require_admin.
Same logic as backend/dependencies.py — updated imports only.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import verify_token
from modules.auth.models import User, UserRole


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency: validates Bearer JWT and returns the authenticated User.
    Raises 401 if token is missing, invalid, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization:
        raise credentials_exception

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    tenant_id: int = payload.get("tenant_id")

    if email is None or tenant_id is None:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.email == email, User.tenant_id == tenant_id)
        .first()
    )
    if user is None:
        raise credentials_exception

    # Attach tenant_id for easy downstream access
    user.current_tenant_id = tenant_id
    return user


async def get_tenant_db(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[Session, int, User]:
    """Returns (db, tenant_id, user) — convenience dependency for tenant-scoped operations."""
    return db, current_user.current_tenant_id, current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Raises 403 if the authenticated user is not an ADMIN."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user

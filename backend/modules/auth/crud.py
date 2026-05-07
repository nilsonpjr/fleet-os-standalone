"""
Auth module CRUD — database operations for users and tenants.
"""
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from modules.auth.models import User, Tenant, UserRole
from modules.auth.schemas import UserCreate, TenantSignup

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.strip().lower()).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(
    db: Session,
    user: UserCreate,
    tenant_id: int,
) -> User:
    db_user = User(
        tenant_id=tenant_id,
        name=user.name,
        email=user.email.strip().lower(),
        hashed_password=get_password_hash(user.password),
        role=UserRole(user.role),
        client_id=user.client_id,
        partner_id=user.partner_id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def register_tenant(db: Session, signup_data: TenantSignup) -> User:
    """Creates a new Tenant + Admin user in a single transaction."""
    tenant = Tenant(name=signup_data.company_name)
    db.add(tenant)
    db.flush()  # get tenant.id without committing

    admin = User(
        tenant_id=tenant.id,
        name=signup_data.admin_name,
        email=signup_data.admin_email.strip().lower(),
        hashed_password=get_password_hash(signup_data.admin_password),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

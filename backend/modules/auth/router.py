"""
Auth module router — /auth endpoints.
Handles login, signup, token refresh, user management.
"""
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend_v2.core.database import get_db
from backend_v2.core.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend_v2.modules.auth.models import User, UserRole
from backend_v2.modules.auth.schemas import (
    UserRead, UserCreate, UserUpdate, Token, TenantSignup,
)
from backend_v2.modules.auth.crud import (
    authenticate_user, get_user_by_email,
    create_user, register_tenant, get_password_hash,
)
from backend_v2.core.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _build_token(user: User) -> Token:
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email, "tenant_id": user.tenant_id, "role": user.role},
        expires_delta=expires,
    )
    return Token(access_token=token, token_type="bearer")


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    clean_email = form_data.username.strip().lower()
    user = authenticate_user(db, clean_email, form_data.password)
    if not user:
        debug_user = db.query(User).filter(User.email == clean_email).first()
        detail = (
            f"Senha incorreta para: '{clean_email}'"
            if debug_user
            else f"Usuário não encontrado: '{clean_email}'"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _build_token(user)


@router.post("/refresh-token", response_model=Token)
def refresh_token(current_user: User = Depends(get_current_user)):
    return _build_token(current_user)


@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/register", response_model=UserRead)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar usuários.")
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email já registrado.")
    return create_user(db, user, tenant_id=current_user.tenant_id)


@router.post("/signup", response_model=Token)
def signup(signup_data: TenantSignup, db: Session = Depends(get_db)):
    if get_user_by_email(db, signup_data.admin_email):
        raise HTTPException(status_code=400, detail="Este email já está cadastrado.")
    new_user = register_tenant(db, signup_data)
    return _build_token(new_user)


@router.get("/users", response_model=List[UserRead])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return db.query(User).filter(User.tenant_id == current_user.tenant_id).all()


@router.put("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    db_user = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == current_user.tenant_id)
        .first()
    )
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    db_user = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == current_user.tenant_id)
        .first()
    )
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível deletar seu próprio usuário.")
    db.delete(db_user)
    db.commit()
    return None

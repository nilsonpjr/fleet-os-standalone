from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from backend import models
from backend import schemas
from backend.database import get_db
from backend import context
from backend.logger import get_logger
from backend.security_config import get_secret_key

logger = get_logger("auth")

load_dotenv()

# Configuração
SECRET_KEY = get_secret_key()
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Gera novos hashes com bcrypt_sha256 para suportar senhas longas e
# mantém compatibilidade de verificação com hashes antigos em bcrypt.
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# --- PASSWORD HASHING ---

def _truncate_password_for_legacy_bcrypt(password: str) -> bytes:
    """Replica o limite histórico de 72 bytes do bcrypt legado."""
    return password.encode("utf-8")[:72]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError as exc:
        is_legacy_bcrypt_hash = hashed_password.startswith(("$2a$", "$2b$", "$2y$"))
        if is_legacy_bcrypt_hash and "longer than 72 bytes" in str(exc):
            return pwd_context.verify(_truncate_password_for_legacy_bcrypt(plain_password), hashed_password)
        raise

def get_password_hash(password: str) -> str:
    """Gera hash da senha."""
    return pwd_context.hash(password)

# --- TOKEN MANAGEMENT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria token JWT com tenant_id"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- REMOTE APPROVAL TOKENS ---

def create_remote_approval_token(order_id: int, tenant_id: int):
    """Gera um token assinado para aprovação remota válida por 48h"""
    expire = datetime.now(timezone.utc) + timedelta(hours=48)
    to_encode = {
        "order_id": order_id,
        "tenant_id": tenant_id,
        "exp": expire,
        "purpose": "remote_approval"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_remote_approval_token(token: str):
    """Valida o token de aprovação remota e retorna o payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "remote_approval":
            return None
        return payload
    except JWTError:
        return None

# --- AUTHENTICATION ---

def authenticate_user(db: Session, email: str, password: str):
    """Autentica usuário e retorna com tenant_id"""
    logger.debug(f"LOGIN ATTEMPT: {email}")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        logger.warning(f"LOGIN FAILED: User not found - {email}")
        return False
    
    if not verify_password(password, user.hashed_password):
        logger.warning(f"LOGIN FAILED: Incorrect password - {email}")
        return False
        
    logger.info(f"LOGIN SUCCESS: {email} (ID: {user.id})")
    return user

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Obtém usuário atual a partir do token (com validação de tenant)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        tenant_id: int = payload.get("tenant_id")
        if email is None or tenant_id is None:
            logger.error("AUTH FAILED: Missing sub or tenant_id in payload")
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError as e:
        logger.error(f"AUTH FAILED: JWTError - {str(e)}")
        raise credentials_exception
    
    user = db.query(models.User).filter(
        models.User.email == token_data.email,
        models.User.tenant_id == tenant_id
    ).first()
    
    if user is None:
        logger.error(f"AUTH FAILED: User not in DB - {token_data.email}")
        raise credentials_exception
    
    user.current_tenant_id = tenant_id
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    """Verifica se usuário está ativo e define contexto"""
    context.set_tenant_id(current_user.tenant_id)
    return current_user

# --- AUTHORIZATION ---

def require_role(allowed_roles: list):
    """Decorator para verificar permissões por role"""
    def role_checker(current_user: models.User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

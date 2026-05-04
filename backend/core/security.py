"""
Security configuration for backend_v2.
Handles encryption/decryption of sensitive data and JWT secret management.
Same logic as backend/security_config.py — rewritten with updated imports.
"""
import base64
import hashlib
import os

from backend_v2.core.logger import get_logger

logger = get_logger("security")

INSECURE_SECRET_SENTINELS = {
    "",
    "your-secret-key-change-this",
    "viverdi-nautica-secret-key-change-in-production",
}


def get_secret_key() -> str:
    secret_key = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or ""
    if secret_key in INSECURE_SECRET_SENTINELS:
        logger.warning(
            "Configuração de SECRET_KEY insegura! Defina a variável SECRET_KEY com um valor forte."
        )
        if not secret_key:
            return "your-secret-key-change-this"
    return secret_key


def is_secret_key_secure() -> bool:
    return get_secret_key() not in INSECURE_SECRET_SENTINELS


def get_encryption_key() -> str:
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if encryption_key:
        try:
            import base64 as _base64
            decoded = _base64.urlsafe_b64decode(encryption_key.encode("utf-8"))
            if len(decoded) == 32:
                return encryption_key
        except Exception:
            pass
        logger.warning("ENCRYPTION_KEY inválida. Derivando chave a partir do valor fornecido.")
        raw_key = hashlib.sha256(encryption_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(raw_key).decode("utf-8")

    logger.warning("ENCRYPTION_KEY não encontrada. Usando fallback derivado da SECRET_KEY.")
    raw_key = hashlib.sha256(get_secret_key().encode("utf-8")).digest()
    return base64.urlsafe_b64encode(raw_key).decode("utf-8")


def encrypt_data(plain_text: str) -> str:
    """Criptografa texto puro usando a ENCRYPTION_KEY configurada."""
    if not plain_text:
        return ""
    try:
        from cryptography.fernet import Fernet
        f = Fernet(get_encryption_key().encode("utf-8"))
        return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Erro na criptografia: {e}")
        return plain_text


def decrypt_data(cipher_text: str) -> str:
    """Descriptografa texto cifrado usando a ENCRYPTION_KEY configurada."""
    if not cipher_text:
        return ""
    if " " in cipher_text or len(cipher_text) < 32:
        return cipher_text
    try:
        from cryptography.fernet import Fernet
        f = Fernet(get_encryption_key().encode("utf-8"))
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return cipher_text

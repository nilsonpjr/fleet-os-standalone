"""
Auth module schemas — Pydantic models for auth/user endpoints.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class UserRead(BaseModel):
    id: int
    tenant_id: int
    name: str
    email: str
    role: str
    client_id: Optional[int] = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "TECHNICIAN"
    client_id: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None


class TenantSignup(BaseModel):
    company_name: str
    admin_name: str
    admin_email: EmailStr
    admin_password: str

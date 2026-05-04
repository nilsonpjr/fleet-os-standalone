"""Config module schemas."""
from typing import Optional, Any
from pydantic import BaseModel


class CompanyInfoUpdate(BaseModel):
    company_name: Optional[str] = None
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    ie: Optional[str] = None
    im: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    crt: Optional[str] = None
    environment: Optional[str] = None
    mercury_username: Optional[str] = None
    mercury_password: Optional[str] = None
    cert_file_path: Optional[str] = None
    cert_password: Optional[str] = None
    fiscal_environment: Optional[str] = None
    city_code: Optional[str] = None
    n8n_webhook_url: Optional[str] = None
    pix_enabled: Optional[bool] = None
    pix_key: Optional[str] = None
    pix_key_type: Optional[str] = None
    pix_bank_name: Optional[str] = None
    pix_merchant_name: Optional[str] = None
    pix_merchant_city: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_image_url: Optional[str] = None
    labor_rate_low: Optional[float] = None
    labor_rate_medium: Optional[float] = None
    labor_rate_high: Optional[float] = None
    home_content: Optional[Any] = None


class CompanyInfoRead(CompanyInfoUpdate):
    id: int
    tenant_id: int

    model_config = {"from_attributes": True}


class ServiceDefCreate(BaseModel):
    code: Optional[str] = None
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    default_price: Optional[float] = 0
    suggested_parts: Optional[Any] = None


class ServiceDefRead(ServiceDefCreate):
    id: int
    tenant_id: int

    model_config = {"from_attributes": True}

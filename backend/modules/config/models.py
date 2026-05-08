"""
Config module — CompanyInfo, ServiceDefinition, ServiceCategory, ServiceCatalog models.
Tables: company_info, service_definitions, service_categories, service_subcategories, service_catalog
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base
from core.security import encrypt_data, decrypt_data
from sqlalchemy import TypeDecorator


class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else encrypt_data(value)

    def process_result_value(self, value, dialect):
        return None if value is None else decrypt_data(value)


class EncryptedText(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else encrypt_data(value)

    def process_result_value(self, value, dialect):
        return None if value is None else decrypt_data(value)


class ComplexityType(str, enum.Enum):
    BAIXA = "Baixa"
    MEDIA = "Media"
    ALTA = "Alta"


class CompanyInfo(Base):
    __tablename__ = "company_info"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_name = Column(String(200))
    trade_name = Column(String(200))
    cnpj = Column(String(50))
    ie = Column(String(50))
    im = Column(String(50))
    phone = Column(String(50), nullable=True)
    whatsapp = Column(String(50), nullable=True)
    instagram = Column(String(200), nullable=True)
    street = Column(String(200))
    number = Column(String(50))
    neighborhood = Column(String(100))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    crt = Column(String(10))
    environment = Column(String(20))
    mercury_username = Column(EncryptedString(500))
    mercury_password = Column(EncryptedString(500))
    cert_file_path = Column(EncryptedText)
    cert_password = Column(EncryptedString(200))
    fiscal_environment = Column(String(20), default="homologation")
    sequence_nfe = Column(Integer, default=1)
    series_nfe = Column(Integer, default=1)
    city_code = Column(String(7), default="4118204")
    n8n_webhook_url = Column(String(500), nullable=True)
    pix_enabled = Column(Boolean, default=False)
    pix_key = Column(String(100))
    pix_key_type = Column(String(20))
    pix_bank_name = Column(String(100))
    pix_merchant_name = Column(String(200))
    pix_merchant_city = Column(String(100))
    hero_title = Column(String(300), nullable=True)
    hero_subtitle = Column(Text, nullable=True)
    hero_image_url = Column(String(500), nullable=True)
    labor_rate_low = Column(Float, default=0)
    labor_rate_medium = Column(Float, default=0)
    labor_rate_high = Column(Float, default=0)
    home_content = Column(JSON, nullable=True)


class ServiceDefinition(Base):
    __tablename__ = "service_definitions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String(50), nullable=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    default_price = Column(Float, default=0)
    suggested_parts = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)

    subcategories = relationship(
        "ServiceSubcategory", back_populates="category", cascade="all, delete-orphan"
    )


class ServiceSubcategory(Base):
    __tablename__ = "service_subcategories"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    name = Column(String(100), nullable=False)

    category = relationship("ServiceCategory", back_populates="subcategories")
    services = relationship(
        "ServiceCatalog", back_populates="subcategory", cascade="all, delete-orphan"
    )


class ServiceCatalog(Base):
    __tablename__ = "service_catalog"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    subcategory_id = Column(Integer, ForeignKey("service_subcategories.id"), nullable=False)
    reference_manufacturer = Column(String(100))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    standard_time_minutes = Column(Integer, default=0)
    complexity = Column(Enum(ComplexityType), default=ComplexityType.MEDIA)

    subcategory = relationship("ServiceSubcategory", back_populates="services")


class Manufacturer(Base):
    __tablename__ = "manufacturers"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False) # BOAT or ENGINE
    
    models = relationship("Model", back_populates="manufacturer", cascade="all, delete-orphan")


class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    
    manufacturer = relationship("Manufacturer", back_populates="models")

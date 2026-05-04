"""
Public module router — /public endpoints.

Public-facing endpoints (site catalog, leads, cart requests).
Relies on the original backend/crud.py for complex public query functions
(get_public_catalog, create_public_lead, etc.) via lazy import to avoid duplication.
"""
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend_v2.core.database import get_db
from backend_v2.core.logger import get_logger

logger = get_logger("public_router")
router = APIRouter(prefix="/public", tags=["Public"])


def _get_crud():
    """Lazy import of original backend CRUD to avoid circular deps."""
    try:
        from backend import crud  # type: ignore
        return crud
    except ImportError:
        return None


def _get_schemas():
    try:
        from backend import schemas  # type: ignore
        return schemas
    except ImportError:
        return None


@router.get("/site-config/{tenant_slug}")
def get_site_config(tenant_slug: str, db: Session = Depends(get_db)):
    crud = _get_crud()
    if not crud:
        raise HTTPException(status_code=503, detail="Public service unavailable.")
    config = crud.get_public_site_config(db, tenant_slug)
    if not config:
        raise HTTPException(status_code=404, detail="Tenant não encontrado.")
    return config


@router.get("/catalog/{tenant_slug}")
def get_catalog(
    tenant_slug: str,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 12,
    db: Session = Depends(get_db),
):
    crud = _get_crud()
    if not crud:
        raise HTTPException(status_code=503, detail="Public service unavailable.")
    config = crud.get_public_site_config(db, tenant_slug)
    if not config:
        raise HTTPException(status_code=404, detail="Tenant não encontrado.")
    return crud.get_public_catalog(db, tenant_slug, search=search, page=page, limit=limit)


@router.get("/catalog/{tenant_slug}/{slug}")
def get_catalog_item(tenant_slug: str, slug: str, db: Session = Depends(get_db)):
    crud = _get_crud()
    if not crud:
        raise HTTPException(status_code=503, detail="Public service unavailable.")
    item = crud.get_public_catalog_item(db, tenant_slug, slug)
    if not item:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return item


@router.post("/leads/{tenant_slug}", status_code=status.HTTP_201_CREATED)
def create_lead(
    tenant_slug: str,
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    crud = _get_crud()
    schemas = _get_schemas()
    if not crud or not schemas:
        raise HTTPException(status_code=503, detail="Public service unavailable.")
    lead_create = schemas.PublicLeadCreate(**payload)
    lead = crud.create_public_lead(db, tenant_slug, lead_create)
    if not lead:
        raise HTTPException(status_code=404, detail="Tenant não encontrado.")
    return {"status": "success", "id": lead.id}


@router.post("/cart-request/{tenant_slug}", status_code=status.HTTP_201_CREATED)
def create_cart_request(
    tenant_slug: str,
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    crud = _get_crud()
    schemas = _get_schemas()
    if not crud or not schemas:
        raise HTTPException(status_code=503, detail="Public service unavailable.")
    cart_create = schemas.PublicCartRequestCreate(**payload)
    request = crud.create_public_cart_request(db, tenant_slug, cart_create)
    if not request:
        raise HTTPException(status_code=404, detail="Tenant não encontrado.")
    return {"status": "success", "id": request.id}


@router.get("/options/manufacturers")
def get_manufacturers(
    tenant_slug: str,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    crud = _get_crud()
    if not crud:
        raise HTTPException(status_code=503, detail="Public service unavailable.")
    tenant = crud.resolve_tenant_by_slug(db, tenant_slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado.")
    return crud.get_manufacturers(db, tenant_id=tenant.id, type=type)

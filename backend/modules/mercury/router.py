"""
Mercury module router — /mercury endpoints.

This module is a thin wrapper. The actual heavy Playwright scraping logic is 
preserved as-is from backend/routers/mercury_router.py (it's complex, stateful 
and doesn't depend on SQLAlchemy models). Only the imports are updated to 
backend_v2.
"""
import threading
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from backend_v2.core.database import get_db
from backend_v2.core.dependencies import get_current_user
from backend_v2.core.logger import get_logger
from backend_v2.modules.auth.models import User
from backend_v2.modules.config.crud import get_company_info
from backend_v2.modules.inventory.crud import get_part, update_part
from backend_v2.modules.inventory.schemas import PartUpdate

logger = get_logger("mercury_router")
router = APIRouter(prefix="/api/mercury", tags=["Mercury"])

mercury_thread_semaphore = threading.Semaphore(2)


def _run_playwright_isolated(coro_func, *args):
    """Run async playwright function in an isolated thread (Windows-safe)."""
    import asyncio
    import sys
    if sys.platform == "win32":
        policy = asyncio.WindowsProactorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
        loop = policy.new_event_loop()
    else:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        with mercury_thread_semaphore:
            return loop.run_until_complete(coro_func(*args))
    finally:
        loop.close()


def _parse_brl(value_str: str) -> float:
    if not value_str:
        return 0.0
    try:
        clean = value_str.strip().replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(clean)
    except ValueError:
        return 0.0


class MercuryScraperError(Exception):
    pass


@router.get("/search/{item}")
async def search_mercury_product(
    item: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Searches for parts on the Mercury Marine portal via Playwright scraping."""
    try:
        # Import scraper from original backend (no duplication of 1000-line logic)
        from backend.routers.mercury_router import (  # type: ignore
            search_product_playwright, run_playwright_in_isolated_thread as _orig_runner
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="Mercury scraper not available.")

    company = get_company_info(db, tenant_id=current_user.tenant_id)
    if not company or not company.mercury_username or not company.mercury_password:
        raise HTTPException(status_code=400, detail="Credenciais Mercury não configuradas.")

    try:
        results = await run_in_threadpool(
            _orig_runner, search_product_playwright,
            item, company.mercury_username, company.mercury_password,
        )
        return {"status": "success", "results": results}
    except Exception as exc:
        logger.warning(f"Mercury search failed for '{item}': {exc}")
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/warranty/{serial}")
async def get_engine_warranty(
    serial: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetches warranty information for a motor serial from the Mercury portal."""
    try:
        from backend.routers.mercury_router import (  # type: ignore
            search_warranty_playwright, run_playwright_in_isolated_thread as _orig_runner
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="Mercury scraper not available.")

    company = get_company_info(db, tenant_id=current_user.tenant_id)
    if not company or not company.mercury_username or not company.mercury_password:
        raise HTTPException(status_code=400, detail="Credenciais Mercury não configuradas.")

    try:
        result = await run_in_threadpool(
            _orig_runner, search_warranty_playwright,
            serial, company.mercury_username, company.mercury_password,
        )
        if result:
            return {"status": "success", "data": result}
        raise HTTPException(status_code=404, detail=f"Motor '{serial}' não encontrado.")
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Mercury warranty failed for '{serial}': {exc}")
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/sync-price/{part_id}")
async def sync_part_price_mercury(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Syncs a part's cost/price from Mercury Marine portal prices."""
    try:
        from backend.routers.mercury_router import (  # type: ignore
            search_product_playwright, run_playwright_in_isolated_thread as _orig_runner
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="Mercury scraper not available.")

    company = get_company_info(db, tenant_id=current_user.tenant_id)
    if not company or not company.mercury_username or not company.mercury_password:
        raise HTTPException(status_code=400, detail="Credenciais Mercury não configuradas.")

    part = get_part(db, part_id, tenant_id=current_user.tenant_id)
    if not part:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")

    try:
        results = await run_in_threadpool(
            _orig_runner, search_product_playwright,
            part.sku, company.mercury_username, company.mercury_password,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro no scraper: {exc}")

    matched = next(
        (r for r in results if r["codigo"].strip() in (part.sku, f"{part.sku} ")),
        None,
    )
    if not matched:
        raise HTTPException(status_code=404, detail=f"SKU {part.sku} não encontrado na Mercury.")

    cost = _parse_brl(matched.get("valorCusto", "0"))
    price = _parse_brl(matched.get("valorVenda", "0"))
    if price == cost and cost > 0:
        price = round(cost * 1.60, 2)

    updated = update_part(db, part_id, current_user.tenant_id, PartUpdate(cost=cost, price=price))
    return {"status": "success", "part_id": part_id, "new_cost": cost, "new_price": price}

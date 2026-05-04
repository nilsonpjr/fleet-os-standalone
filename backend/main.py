"""
backend_v2/main.py — Modular FastAPI Application Entry Point

Strategy: This is a PARALLEL backend running alongside the original backend/.
          The original backend/ is NEVER modified.
          When backend_v2 is fully tested, switch the Dockerfile/render.yaml to
          point at this main.py instead of backend.main.

Module registration order follows the dependency graph:
  core → auth → clients → boats → inventory → orders → fiscal/finance → partners → config → mercury → public
"""
import sys
import asyncio
import os
from dotenv import load_dotenv

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load .env from the current directory
load_dotenv(
    os.path.join(os.path.dirname(__file__), ".env"),
    override=False,
)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.logger import get_logger
from core.security import is_secret_key_secure
from core.database import Base, engine, ensure_columns
from core.logger import get_logger

logger = get_logger("main")

# ------------------------------------------------------------------
# Import ALL module models so SQLAlchemy can build the full metadata
# graph correctly (relationships between modules need all tables known).
# ------------------------------------------------------------------
from modules.auth.models import User, Tenant            # noqa: F401
from modules.clients.models import Client, Marina       # noqa: F401
from modules.boats.models import Boat, Engine           # noqa: F401
from modules.inventory.models import (                  # noqa: F401
    Part, StockMovement, Invoice, MaintenanceKit, MaintenanceKitItem
)
from modules.orders.models import (                     # noqa: F401
    ServiceOrder, ServiceItem, OrderNote, TechnicalDelivery
)
from modules.fiscal.models import FiscalInvoice         # noqa: F401
from modules.finance.models import Transaction          # noqa: F401
from modules.partners.models import (                   # noqa: F401
    Partner, PartnerQuote, Inspection
)
from modules.config.models import (                     # noqa: F401
    CompanyInfo, ServiceDefinition, ServiceCategory,
    ServiceSubcategory, ServiceCatalog
)
from modules.lgpd.models import (                       # noqa: F401
    ConsentRecord, AuditLog, ErasureRequest
)
from modules.fleet.models import (                       # noqa: F401
    Vehicle, BoatRegulatory, Workshop as FleetWorkshop,
    FleetRequest, WorkshopQuote, WorkshopQuoteItem,
    WorkshopExecution, FleetClientDetail, MaintenanceSchedule,
)
from modules.notifications.models import Notification       # noqa: F401

# Create tables that don't exist yet (non-destructive)
Base.metadata.create_all(bind=engine)

# Schema Evolution: Add missing telemetry columns to existing tables
ensure_columns("vehicles", [
    ("last_lat", "FLOAT"),
    ("last_lng", "FLOAT"),
    ("last_sync_at", "TIMESTAMP")
])
ensure_columns("workshops", [
    ("last_lat", "FLOAT"),
    ("last_lng", "FLOAT"),
    ("last_sync_at", "TIMESTAMP")
])

# ------------------------------------------------------------------
# Import routers
# ------------------------------------------------------------------
from modules.auth.router import router as auth_router
from modules.clients.router import router as clients_router
from modules.boats.router import router as boats_router
from modules.inventory.router import router as inventory_router
from modules.orders.router import router as orders_router
from modules.fiscal.router import router as fiscal_router
from modules.finance.router import router as finance_router
from modules.partners.router import router as partners_router
from modules.config.router import router as config_router
from modules.mercury.router import router as mercury_router
from modules.public.router import router as public_router
from modules.lgpd.router import router as lgpd_router
from modules.fleet.router import router as fleet_router
from modules.notifications.router import router as notifications_router
from modules.fleet.telemetry_router import router as telemetry_router

# ------------------------------------------------------------------
# App Configuration
# ------------------------------------------------------------------
app = FastAPI(title="Viverdi Náutica API v2 (Modular)")


@app.head("/", include_in_schema=False)
def health_head():
    return JSONResponse(status_code=200, content={})


# CORS
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()]
if not origins:
    origins = [
        "https://www.marealtanautica.com.br",
        "https://marealtanautica.com.br",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "UNHANDLED EXCEPTION: method=%s path=%s type=%s",
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor."})


# Request logger middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"REQUEST: {request.method} {request.url.path}")
    response = await call_next(request)
    if response.status_code >= 400:
        logger.warning(f"RESPONSE ERROR: {request.url.path} -> {response.status_code}")
    return response


# Startup security checks
@app.on_event("startup")
async def startup_security_checks():
    db_url = os.getenv("DATABASE_URL", "")
    is_production = "postgresql" in db_url or "supabase" in db_url
    if not is_secret_key_secure():
        msg = "AMBIENTE INSEGURO: SECRET_KEY padrão detectada."
        if is_production:
            logger.error(f"FATAL: {msg}")
            sys.exit(1)
        else:
            logger.warning(msg)


# ------------------------------------------------------------------
# Register all routers (with /api prefix + bare prefix for Vercel compat)
# ------------------------------------------------------------------
_all_routers = [
    auth_router, clients_router, boats_router, inventory_router,
    orders_router, fiscal_router, finance_router, partners_router,
    config_router, mercury_router, public_router, lgpd_router,
    fleet_router, notifications_router, telemetry_router,
]

for router in _all_routers:
    if router.prefix.startswith("/api"):
        router.prefix = router.prefix.replace("/api", "", 1)
    app.include_router(router, prefix="/api")
    app.include_router(router)


# ------------------------------------------------------------------
# SPA Fallback (serves frontend/dist if present)
# ------------------------------------------------------------------
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Serve uploaded photos
_uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

_frontend_dist = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist"
)
if not os.path.exists(_frontend_dist) and os.path.exists("/frontend/dist"):
    _frontend_dist = "/frontend/dist"

if os.path.exists(_frontend_dist):
    @app.get("/assets/{filename}")
    async def serve_assets(filename: str):
        file_path = os.path.join(_frontend_dist, "assets", filename)
        if os.path.exists(file_path):
            return FileResponse(file_path)
        return JSONResponse(status_code=404, content={"message": "Arquivo não encontrado"})

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if any(full_path.startswith(p) for p in ("api", "docs", "openapi.json", "assets")):
            return JSONResponse(status_code=404, content={"message": "Endpoint não encontrado"})
        file_path = os.path.join(_frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(_frontend_dist, "index.html")
        if os.path.exists(index_path):
            response = FileResponse(index_path)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        return {"message": "Frontend não construído."}
else:
    @app.get("/")
    def read_root():
        return {"message": "backend_v2 running. Frontend dist not found."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))  # porta diferente para não colidir com backend/
    is_dev = os.environ.get("RENDER") is None
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=is_dev)

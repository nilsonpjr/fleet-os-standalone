"""Fleet module router — all fleet endpoints."""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
import shutil, os, uuid
from backend.services.storage_service import upload_file_to_storage

from backend_v2.core.database import get_db
from backend_v2.core.dependencies import get_current_user, require_admin
from backend_v2.modules.auth.models import User, UserRole
from backend_v2.modules.fleet import crud
from backend_v2.modules.fleet.schemas import (
    VehicleCreate, VehicleUpdate, VehicleRead,
    BoatRegulatoryCreate, BoatRegulatoryRead,
    WorkshopCreate, WorkshopUpdate, WorkshopRead,
    FleetRequestCreate, FleetRequestAssign, FleetRequestRead,
    WorkshopQuoteCreate, WorkshopQuoteRead,
    ExecutionUpdate, ExecutionRead,
    FleetClientDetailCreate, FleetClientDetailRead,
    MaintenanceScheduleCreate, MaintenanceScheduleRead,
    ExpiryAlert, RequestMessageCreate, RequestMessageRead,
)

router = APIRouter(prefix="/api/fleet", tags=["Fleet"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Photo Upload ───────────────────────────────────────────────────────────

@router.post("/upload/photo")
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a photo and return its public URL."""
    ext = os.path.splitext(file.filename or "image.jpg")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".heic"}:
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado.")
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOAD_DIR, filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"/uploads/{filename}"}


# ── Vehicles ───────────────────────────────────────────────────────────────

@router.get("/vehicles", response_model=List[VehicleRead])
def list_vehicles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    client_id = None
    if current_user.role == UserRole.CLIENT:
        client_id = current_user.client_id
    return crud.get_vehicles(db, tenant_id=current_user.tenant_id, client_id=client_id)


@router.post("/vehicles", response_model=VehicleRead)
def create_vehicle(
    data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return crud.create_vehicle(db, data, tenant_id=current_user.tenant_id)


@router.get("/vehicles/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    v = crud.get_vehicle(db, vehicle_id, current_user.tenant_id)
    if not v:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    return v


@router.put("/vehicles/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    v = crud.update_vehicle(db, vehicle_id, current_user.tenant_id, data)
    if not v:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    return v


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if not crud.delete_vehicle(db, vehicle_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")


# ── Boat Regulatory ────────────────────────────────────────────────────────

@router.get("/boats/{boat_id}/regulatory", response_model=BoatRegulatoryRead)
def get_boat_regulatory(boat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    br = crud.get_boat_regulatory(db, boat_id)
    if not br:
        raise HTTPException(status_code=404, detail="Dados regulatórios não encontrados.")
    return br


@router.put("/boats/{boat_id}/regulatory", response_model=BoatRegulatoryRead)
def upsert_boat_regulatory(
    boat_id: int,
    data: BoatRegulatoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    data.boat_id = boat_id
    return crud.get_or_create_boat_regulatory(db, data)


# ── Workshops ──────────────────────────────────────────────────────────────

@router.get("/workshops", response_model=List[WorkshopRead])
def list_workshops(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_workshops(db, tenant_id=current_user.tenant_id)


@router.post("/workshops", response_model=WorkshopRead)
def create_workshop(
    data: WorkshopCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return crud.create_workshop(db, data, tenant_id=current_user.tenant_id)


@router.get("/workshops/{workshop_id}", response_model=WorkshopRead)
def get_workshop(workshop_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    w = crud.get_workshop(db, workshop_id, current_user.tenant_id)
    if not w:
        raise HTTPException(status_code=404, detail="Oficina não encontrada.")
    return w


@router.put("/workshops/{workshop_id}", response_model=WorkshopRead)
def update_workshop(
    workshop_id: int,
    data: WorkshopUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    w = crud.update_workshop(db, workshop_id, current_user.tenant_id, data)
    if not w:
        raise HTTPException(status_code=404, detail="Oficina não encontrada.")
    return w


# ── Fleet Requests ─────────────────────────────────────────────────────────

@router.get("/requests", response_model=List[FleetRequestRead])
def list_requests(
    vehicle_id: Optional[int] = None,
    boat_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin/Manager: all requests. Client: only their own. Workshop: only assigned."""
    client_id = None
    if current_user.role == UserRole.CLIENT:
        client_id = current_user.client_id
    
    if current_user.role == UserRole.PARTNER:
        if not current_user.partner_id:
            return []
        return crud.get_requests_for_workshop(db, tenant_id=current_user.tenant_id, workshop_id=current_user.partner_id)
        
    return crud.get_requests(
        db, 
        tenant_id=current_user.tenant_id, 
        client_id=client_id,
        vehicle_id=vehicle_id,
        boat_id=boat_id,
        status=status
    )


@router.get("/requests/my", response_model=List[FleetRequestRead])
def list_my_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_requests(db, tenant_id=current_user.tenant_id, client_id=current_user.client_id)


@router.get("/requests/assigned", response_model=List[FleetRequestRead])
def list_assigned_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Workshop: requests assigned to this workshop (via partner_id → workshop)."""
    from backend_v2.modules.fleet.models import Workshop
    workshop = db.query(Workshop).filter(
        Workshop.tenant_id == current_user.tenant_id,
        Workshop.partner_id == getattr(current_user, "partner_id", None),
    ).first()
    if not workshop:
        return []
    return crud.get_requests_for_workshop(db, tenant_id=current_user.tenant_id, workshop_id=workshop.id)


@router.post("/requests", response_model=FleetRequestRead, status_code=status.HTTP_201_CREATED)
def create_request(
    data: FleetRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client_id = current_user.client_id or 0
    if current_user.role in (UserRole.ADMIN, UserRole.MANAGER):
        client_id = data.model_dump().get("client_id") or 0
    return crud.create_request(db, data, client_id=client_id, tenant_id=current_user.tenant_id)


@router.get("/requests/{request_id}", response_model=FleetRequestRead)
def get_request(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req = crud.get_request(db, request_id, current_user.tenant_id)
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    return req


@router.post("/requests/{request_id}/photos")
async def upload_request_photo(
    request_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = crud.get_request(db, request_id, current_user.tenant_id)
    if not req:
        raise HTTPException(status_code=404)
    
    file_ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
    filename = f"fleet/requests/{request_id}/{uuid.uuid4().hex}{file_ext}"
    url = upload_file_to_storage(file.file, filename, file.content_type)
    
    photos = list(req.photos or [])
    photos.append(url)
    req.photos = photos
    db.commit()
    return {"url": url}


@router.get("/requests/{request_id}/quotes", response_model=List[WorkshopQuoteRead])
def get_request_quotes(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req = crud.get_request(db, request_id, current_user.tenant_id)
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    if current_user.role == UserRole.CLIENT and req.client_id != (current_user.client_id or 0):
        raise HTTPException(status_code=403, detail="Acesso negado.")
    return crud.get_request_quotes(db, request_id, current_user.tenant_id)


@router.post("/requests/{request_id}/assign", response_model=FleetRequestRead)
def assign_request(
    request_id: int,
    data: FleetRequestAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    req = crud.assign_request(db, request_id, current_user.tenant_id, data.workshop_ids)
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    return req


@router.post("/requests/{request_id}/approve/admin")
def approve_admin(
    request_id: int, quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    req = crud.approve_request_admin(db, request_id, current_user.tenant_id, quote_id)
    if not req:
        raise HTTPException(status_code=404)
    return req


@router.post("/requests/{request_id}/approve/client")
def approve_client(
    request_id: int, quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = crud.approve_request_client(db, request_id, current_user.tenant_id, quote_id)
    if not req:
        raise HTTPException(status_code=404)
    return req


@router.post("/requests/{request_id}/revision")
def request_revision(
    request_id: int, quote_id: int, notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = crud.request_revision(db, request_id, current_user.tenant_id, quote_id, notes)
    if not req:
        raise HTTPException(status_code=404)
    return req


# ── Quotes ─────────────────────────────────────────────────────────────────

@router.post("/requests/{request_id}/quotes", response_model=WorkshopQuoteRead)
def create_quote(
    request_id: int,
    data: WorkshopQuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Workshop creates/updates quote for a request."""
    from backend_v2.modules.fleet.models import Workshop
    workshop = db.query(Workshop).filter(
        Workshop.tenant_id == current_user.tenant_id,
        Workshop.partner_id == getattr(current_user, "partner_id", None),
    ).first()
    if not workshop:
        raise HTTPException(status_code=403, detail="Nenhuma oficina vinculada ao usuário.")
    return crud.create_quote(db, request_id, workshop.id, data)


@router.post("/quotes/{quote_id}/photos-before")
async def upload_quote_photo_before(
    quote_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from backend_v2.modules.fleet.models import WorkshopQuote
    quote = db.query(WorkshopQuote).filter(WorkshopQuote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404)
    
    file_ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
    filename = f"fleet/quotes/{quote_id}/before_{uuid.uuid4().hex}{file_ext}"
    url = upload_file_to_storage(file.file, filename, file.content_type)
    
    photos = list(quote.photos_before or [])
    photos.append(url)
    quote.photos_before = photos
    db.commit()
    return {"url": url}


@router.post("/quotes/{quote_id}/submit", response_model=WorkshopQuoteRead)
def submit_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend_v2.modules.fleet.models import Workshop
    workshop = db.query(Workshop).filter(
        Workshop.tenant_id == current_user.tenant_id,
        Workshop.partner_id == getattr(current_user, "partner_id", None),
    ).first()
    if not workshop:
        raise HTTPException(status_code=403)
    q = crud.submit_quote(db, quote_id, workshop.id)
    if not q:
        raise HTTPException(status_code=404)
    return q


# ── Execution ──────────────────────────────────────────────────────────────

@router.put("/executions/{execution_id}", response_model=ExecutionRead)
def update_execution(
    execution_id: int,
    data: ExecutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend_v2.modules.fleet.models import Workshop
    workshop = db.query(Workshop).filter(
        Workshop.tenant_id == current_user.tenant_id,
        Workshop.partner_id == getattr(current_user, "partner_id", None),
    ).first()
    if not workshop:
        raise HTTPException(status_code=403)
    exec_ = crud.update_execution(db, execution_id, workshop.id, data)
    if not exec_:
        raise HTTPException(status_code=404)
    return exec_


@router.post("/executions/{execution_id}/close-request")
def request_closure(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend_v2.modules.fleet.models import Workshop
    workshop = db.query(Workshop).filter(
        Workshop.tenant_id == current_user.tenant_id,
        Workshop.partner_id == getattr(current_user, "partner_id", None),
    ).first()
    if not workshop:
        raise HTTPException(status_code=403)
    exec_ = crud.request_closure(db, execution_id, workshop.id)
    if not exec_:
        raise HTTPException(status_code=404)
    return exec_


@router.post("/executions/{execution_id}/approve/admin")
def approve_closure_admin(execution_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    exec_ = crud.approve_closure_admin(db, execution_id, current_user.tenant_id)
    if not exec_:
        raise HTTPException(status_code=404)
    return exec_


@router.post("/executions/{execution_id}/approve/client")
def approve_closure_client(execution_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exec_ = crud.approve_closure_client(db, execution_id, current_user.tenant_id)
    if not exec_:
        raise HTTPException(status_code=404)
    return exec_


# ── Expiry Alerts ──────────────────────────────────────────────────────────

@router.get("/alerts", response_model=List[ExpiryAlert])
def get_alerts(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_expiry_alerts(db, tenant_id=current_user.tenant_id, days_ahead=days_ahead)


# ── Fleet Client Details ───────────────────────────────────────────────────

@router.get("/clients/{client_id}/detail", response_model=FleetClientDetailRead)
def get_client_detail(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    detail = crud.get_client_detail(db, client_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Detalhes do cliente não encontrados.")
    return detail


@router.put("/clients/{client_id}/detail", response_model=FleetClientDetailRead)
def upsert_client_detail(
    client_id: int,
    data: FleetClientDetailCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return crud.upsert_client_detail(db, client_id, data)


# ── Reports ───────────────────────────────────────────────────────────────

@router.get("/reports/costs")
def get_cost_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin/Manager: aggregated costs by asset."""
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Acesso restrito.")
        
    return crud.get_cost_stats(db, tenant_id=current_user.tenant_id)


@router.get("/reports/stats")
def get_fleet_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin summary: costs, health, CO2."""
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=403)
    return crud.get_cost_stats(db, tenant_id=current_user.tenant_id)


@router.get("/reports/export/csv")
def export_costs_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exports cost report as CSV."""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=403)
        
    stats = crud.get_cost_stats(db, tenant_id=current_user.tenant_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ativo", "Tipo", "ID", "Gasto Total (BRL)"])
    
    for key, val in stats["by_asset"].items():
        type_prefix, asset_id = key.split(':')
        writer.writerow([key, type_prefix, asset_id, val])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_custos_fleet.csv"}
    )


# ── Maintenance Schedules (Preventiva) ────────────────────────────────────

@router.get("/maintenance", response_model=List[MaintenanceScheduleRead])
def list_maintenance_schedules(
    vehicle_id: Optional[int] = None,
    boat_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedules = crud.get_maintenance_schedules(db, tenant_id=current_user.tenant_id)
    if vehicle_id:
        schedules = [s for s in schedules if s.vehicle_id == vehicle_id]
    if boat_id:
        schedules = [s for s in schedules if s.boat_id == boat_id]
    return schedules


@router.post("/maintenance", response_model=MaintenanceScheduleRead)
def create_maintenance_schedule(
    data: MaintenanceScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.create_maintenance_schedule(db, data, tenant_id=current_user.tenant_id)


@router.get("/maintenance/alerts")
def get_preventive_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.get_preventive_alerts(db, tenant_id=current_user.tenant_id)


# ── Chat (Messages) ───────────────────────────────────────────────────────

@router.get("/requests/{request_id}/messages", response_model=List[RequestMessageRead])
def list_messages(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify access
    req = crud.get_request(db, request_id, current_user.tenant_id)
    if not req:
        raise HTTPException(status_code=404)
    
    msgs = crud.get_messages(db, request_id)
    # Inject user name for UI
    result = []
    for m in msgs:
        result.append({
            "id": m.id,
            "fleet_request_id": m.fleet_request_id,
            "user_id": m.user_id,
            "user_name": m.user.name,
            "message": m.message,
            "created_at": m.created_at
        })
    return result


@router.post("/requests/{request_id}/messages", response_model=RequestMessageRead)
def send_message(
    request_id: int,
    data: RequestMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = crud.get_request(db, request_id, current_user.tenant_id)
    if not req:
        raise HTTPException(status_code=404)
        
    msg = crud.create_message(db, request_id, current_user.id, data.message)
    return {
        "id": msg.id,
        "fleet_request_id": msg.fleet_request_id,
        "user_id": msg.user_id,
        "user_name": current_user.name,
        "message": msg.message,
        "created_at": msg.created_at
    }



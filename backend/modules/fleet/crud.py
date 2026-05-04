"""Fleet module — CRUD operations."""
from __future__ import annotations
from datetime import datetime, timezone, date, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from modules.fleet.models import (
    Vehicle, BoatRegulatory, Workshop, FleetRequest, WorkshopQuote,
    WorkshopQuoteItem, WorkshopExecution, FleetClientDetail,
    MaintenanceSchedule, RequestStatus, QuoteStatus, ExecutionApprovalStatus,
    RequestMessage,
)
from modules.auth.models import User
from modules.notifications.crud import notify_user
from modules.fleet.schemas import (
    VehicleCreate, VehicleUpdate,
    BoatRegulatoryCreate,
    WorkshopCreate, WorkshopUpdate,
    FleetRequestCreate, FleetRequestUpdate,
    WorkshopQuoteCreate, WorkshopQuoteUpdate,
    ExecutionUpdate,
    FleetClientDetailCreate,
    MaintenanceScheduleCreate,
    ExpiryAlert,
)


# ── Vehicles ──────────────────────────────────────────────────────────────

def get_vehicles(db: Session, tenant_id: int, active_only: bool = True, client_id: Optional[int] = None) -> List[Vehicle]:
    q = db.query(Vehicle).filter(Vehicle.tenant_id == tenant_id)
    if active_only:
        q = q.filter(Vehicle.is_active == True)  # noqa: E712
    if client_id:
        q = q.filter(Vehicle.client_id == client_id)
    return q.order_by(Vehicle.brand, Vehicle.model).all()


def get_vehicle(db: Session, vehicle_id: int, tenant_id: int) -> Optional[Vehicle]:
    return db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.tenant_id == tenant_id,
    ).first()


def create_vehicle(db: Session, data: VehicleCreate, tenant_id: int) -> Vehicle:
    v = Vehicle(**data.model_dump(), tenant_id=tenant_id)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def update_vehicle(db: Session, vehicle_id: int, tenant_id: int, data: VehicleUpdate) -> Optional[Vehicle]:
    v = get_vehicle(db, vehicle_id, tenant_id)
    if not v:
        return None
    for k, val in data.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    v.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(v)
    return v


def delete_vehicle(db: Session, vehicle_id: int, tenant_id: int) -> bool:
    v = get_vehicle(db, vehicle_id, tenant_id)
    if not v:
        return False
    v.is_active = False
    db.commit()
    return True


# ── BoatRegulatory ────────────────────────────────────────────────────────

def get_or_create_boat_regulatory(db: Session, data: BoatRegulatoryCreate) -> BoatRegulatory:
    existing = db.query(BoatRegulatory).filter(BoatRegulatory.boat_id == data.boat_id).first()
    if existing:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(existing, k, v)
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing
    br = BoatRegulatory(**data.model_dump())
    db.add(br)
    db.commit()
    db.refresh(br)
    return br


def get_boat_regulatory(db: Session, boat_id: int) -> Optional[BoatRegulatory]:
    return db.query(BoatRegulatory).filter(BoatRegulatory.boat_id == boat_id).first()


# ── Workshops ─────────────────────────────────────────────────────────────

def get_workshops(db: Session, tenant_id: int) -> List[Workshop]:
    return db.query(Workshop).filter(
        Workshop.tenant_id == tenant_id,
        Workshop.is_active == True,  # noqa: E712
    ).order_by(Workshop.name).all()


def get_workshop(db: Session, workshop_id: int, tenant_id: int) -> Optional[Workshop]:
    return db.query(Workshop).filter(
        Workshop.id == workshop_id,
        Workshop.tenant_id == tenant_id,
    ).first()


def create_workshop(db: Session, data: WorkshopCreate, tenant_id: int) -> Workshop:
    w = Workshop(**data.model_dump(), tenant_id=tenant_id)
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def update_workshop(db: Session, workshop_id: int, tenant_id: int, data: WorkshopUpdate) -> Optional[Workshop]:
    w = get_workshop(db, workshop_id, tenant_id)
    if not w:
        return None
    for k, val in data.model_dump(exclude_unset=True).items():
        setattr(w, k, val)
    db.commit()
    db.refresh(w)
    return w


# ── FleetRequests ─────────────────────────────────────────────────────────

def get_requests(
    db: Session, 
    tenant_id: int, 
    client_id: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    boat_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[FleetRequest]:
    q = db.query(FleetRequest).filter(FleetRequest.tenant_id == tenant_id)
    if client_id:
        q = q.filter(FleetRequest.client_id == client_id)
    if vehicle_id:
        q = q.filter(FleetRequest.vehicle_id == vehicle_id)
    if boat_id:
        q = q.filter(FleetRequest.boat_id == boat_id)
    if status:
        q = q.filter(FleetRequest.status == status)
    return q.order_by(FleetRequest.created_at.desc()).all()


def get_requests_for_workshop(db: Session, tenant_id: int, workshop_id: int) -> List[FleetRequest]:
    """Returns requests assigned to this workshop."""
    all_reqs = db.query(FleetRequest).filter(FleetRequest.tenant_id == tenant_id).all()
    return [r for r in all_reqs if workshop_id in (r.assigned_workshop_ids or [])]


def get_request(db: Session, request_id: int, tenant_id: int) -> Optional[FleetRequest]:
    return db.query(FleetRequest).filter(
        FleetRequest.id == request_id,
        FleetRequest.tenant_id == tenant_id,
    ).first()


def get_request_quotes(db: Session, request_id: int, tenant_id: int) -> List[WorkshopQuote]:
    req = get_request(db, request_id, tenant_id)
    if not req:
        return []
    return db.query(WorkshopQuote).filter(
        WorkshopQuote.fleet_request_id == request_id
    ).order_by(WorkshopQuote.created_at.desc()).all()


def create_request(db: Session, data: FleetRequestCreate, client_id: int, tenant_id: int) -> FleetRequest:
    req = FleetRequest(**data.model_dump(), client_id=client_id, tenant_id=tenant_id)
    db.add(req)
    db.commit()
    db.refresh(req)
    # notify_user(db, 1, tenant_id, "Nova Solicitação", f"Cliente abriu chamado #{req.id}", "info")
    return req


def assign_request(db: Session, request_id: int, tenant_id: int, workshop_ids: List[int]) -> Optional[FleetRequest]:
    req = get_request(db, request_id, tenant_id)
    if not req:
        return None
    req.assigned_workshop_ids = workshop_ids
    req.status = RequestStatus.ASSIGNED
    req.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)
    # Notify Workshops
    for ws_id in (workshop_ids or []):
        ws = get_workshop(db, ws_id, tenant_id)
        if ws and ws.partner_id:
            user = db.query(User).filter(User.partner_id == ws.partner_id).first()
            if user:
                notify_user(db, user.id, tenant_id, "Novo Chamado Atribuído", f"Chamado #{req.id} foi atribuído à sua oficina.", "info", f"/workshop/requests/{req.id}")
    return req


def approve_request_admin(db: Session, request_id: int, tenant_id: int, quote_id: int) -> Optional[FleetRequest]:
    req = get_request(db, request_id, tenant_id)
    if not req:
        return None
    req.admin_approved_at = datetime.now(timezone.utc)
    # Both approved → move to IN_PROGRESS
    if req.client_approved_at:
        req.status = RequestStatus.IN_PROGRESS
        _approve_winning_quote(db, quote_id)
    else:
        req.status = RequestStatus.ADMIN_APPROVED
    req.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)
    # Notify Client
    if req.client_id:
        user = db.query(User).filter(User.client_id == req.client_id).first()
        if user:
            notify_user(db, user.id, tenant_id, "Orçamento Aprovado (Admin)", f"O administrador aprovou o orçamento do chamado #{req.id}.", "success", f"/client/requests/{req.id}")
    return req


def approve_request_client(db: Session, request_id: int, tenant_id: int, quote_id: int) -> Optional[FleetRequest]:
    req = get_request(db, request_id, tenant_id)
    if not req:
        return None
    req.client_approved_at = datetime.now(timezone.utc)
    if req.admin_approved_at:
        req.status = RequestStatus.IN_PROGRESS
        _approve_winning_quote(db, quote_id)
    else:
        req.status = RequestStatus.CLIENT_APPROVED
    req.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)
    # notify_user(db, 1, tenant_id, "Cliente Aprovou Orçamento", f"Chamado #{req.id} aprovado pelo cliente.", "success")
    return req


def _approve_winning_quote(db: Session, quote_id: int) -> None:
    """Mark the winning quote as APPROVED; reject all others for same request."""
    quote = db.query(WorkshopQuote).filter(WorkshopQuote.id == quote_id).first()
    if not quote:
        return
    others = db.query(WorkshopQuote).filter(
        WorkshopQuote.fleet_request_id == quote.fleet_request_id,
        WorkshopQuote.id != quote_id,
    ).all()
    for o in others:
        o.status = QuoteStatus.REJECTED
    quote.status = QuoteStatus.APPROVED
    # Create execution record
    if not quote.execution:
        exec_ = WorkshopExecution(
            quote_id=quote.id,
            fleet_request_id=quote.fleet_request_id,
            workshop_id=quote.workshop_id,
            started_at=datetime.now(timezone.utc),
        )
        db.add(exec_)
    db.commit()


def request_revision(db: Session, request_id: int, tenant_id: int, quote_id: int, notes: str) -> Optional[FleetRequest]:
    req = get_request(db, request_id, tenant_id)
    quote = db.query(WorkshopQuote).filter(WorkshopQuote.id == quote_id).first()
    if not req or not quote:
        return None
    req.status = RequestStatus.REVISION_REQUESTED
    req.admin_approved_at = None
    req.client_approved_at = None
    quote.status = QuoteStatus.REVISION_REQUESTED
    quote.revision_notes = notes
    db.commit()
    db.refresh(req)
    return req


# ── WorkshopQuotes ────────────────────────────────────────────────────────

def create_quote(db: Session, request_id: int, workshop_id: int, data: WorkshopQuoteCreate) -> WorkshopQuote:
    items_data = data.items or []
    quote_data = data.model_dump(exclude={"items"})

    # Compute totals
    subtotal_parts = sum(
        i.total for i in items_data if i.type.value == "PART"
    )
    subtotal_labor = sum(
        i.total for i in items_data if i.type.value == "LABOR"
    )
    total = sum(i.total for i in items_data)

    quote = WorkshopQuote(
        **quote_data,
        fleet_request_id=request_id,
        workshop_id=workshop_id,
        subtotal_parts=subtotal_parts,
        subtotal_labor=subtotal_labor,
        total_value=total,
    )
    db.add(quote)
    db.flush()

    for item in items_data:
        db.add(WorkshopQuoteItem(**item.model_dump(), quote_id=quote.id))

    db.commit()
    db.refresh(quote)
    return quote


def submit_quote(db: Session, quote_id: int, workshop_id: int) -> Optional[WorkshopQuote]:
    quote = db.query(WorkshopQuote).filter(
        WorkshopQuote.id == quote_id,
        WorkshopQuote.workshop_id == workshop_id,
    ).first()
    if not quote:
        return None
    quote.status = QuoteStatus.SUBMITTED
    quote.submitted_at = datetime.now(timezone.utc)
    # Update request status to QUOTED if not already
    req = db.query(FleetRequest).filter(FleetRequest.id == quote.fleet_request_id).first()
    if req and req.status == RequestStatus.ASSIGNED:
        req.status = RequestStatus.QUOTED
    db.commit()
    db.refresh(quote)
    # notify_user(db, 1, req.tenant_id, "Novo Orçamento Recebido", f"Oficina {workshop_id} enviou orçamento para o chamado #{req.id}", "info")
    return quote


# ── WorkshopExecution ─────────────────────────────────────────────────────

def update_execution(db: Session, execution_id: int, workshop_id: int, data: ExecutionUpdate) -> Optional[WorkshopExecution]:
    exec_ = db.query(WorkshopExecution).filter(
        WorkshopExecution.id == execution_id,
        WorkshopExecution.workshop_id == workshop_id,
    ).first()
    if not exec_:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(exec_, k, v)
    db.commit()
    db.refresh(exec_)
    return exec_


def request_closure(db: Session, execution_id: int, workshop_id: int) -> Optional[WorkshopExecution]:
    exec_ = db.query(WorkshopExecution).filter(
        WorkshopExecution.id == execution_id,
        WorkshopExecution.workshop_id == workshop_id,
    ).first()
    if not exec_:
        return None
    exec_.completed_at = datetime.now(timezone.utc)
    req = db.query(FleetRequest).filter(FleetRequest.id == exec_.fleet_request_id).first()
    if req:
        req.status = RequestStatus.AWAITING_CLOSURE
    db.commit()
    db.refresh(exec_)
    # Notify Client
    if req and req.client_id:
        user = db.query(User).filter(User.client_id == req.client_id).first()
        if user:
            notify_user(db, user.id, req.tenant_id, "Serviço Concluído", f"O serviço do chamado #{req.id} foi concluído.", "success", f"/client/requests/{req.id}")
    return exec_


def approve_closure_admin(db: Session, execution_id: int, tenant_id: int) -> Optional[WorkshopExecution]:
    exec_ = db.query(WorkshopExecution).filter(WorkshopExecution.id == execution_id).first()
    if not exec_:
        return None
    exec_.admin_approved_at = datetime.now(timezone.utc)
    if exec_.approval_status == ExecutionApprovalStatus.CLIENT_APPROVED:
        _finalize_execution(db, exec_)
    else:
        exec_.approval_status = ExecutionApprovalStatus.ADMIN_APPROVED
    db.commit()
    db.refresh(exec_)
    return exec_


def approve_closure_client(db: Session, execution_id: int, tenant_id: int) -> Optional[WorkshopExecution]:
    exec_ = db.query(WorkshopExecution).filter(WorkshopExecution.id == execution_id).first()
    if not exec_:
        return None
    exec_.client_approved_at = datetime.now(timezone.utc)
    if exec_.approval_status == ExecutionApprovalStatus.ADMIN_APPROVED:
        _finalize_execution(db, exec_)
    else:
        exec_.approval_status = ExecutionApprovalStatus.CLIENT_APPROVED
    db.commit()
    db.refresh(exec_)
    return exec_


def _finalize_execution(db: Session, exec_: WorkshopExecution) -> None:
    exec_.approval_status = ExecutionApprovalStatus.APPROVED
    exec_.closed_at = datetime.now(timezone.utc)
    req = db.query(FleetRequest).filter(FleetRequest.id == exec_.fleet_request_id).first()
    if req:
        req.status = RequestStatus.DONE


# ── FleetClientDetail ─────────────────────────────────────────────────────

def upsert_client_detail(db: Session, client_id: int, data: FleetClientDetailCreate) -> FleetClientDetail:
    existing = db.query(FleetClientDetail).filter(FleetClientDetail.client_id == client_id).first()
    if existing:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing
    detail = FleetClientDetail(**data.model_dump(), client_id=client_id)
    db.add(detail)
    db.commit()
    db.refresh(detail)
    return detail


# ── Maintenance Schedules ──────────────────────────────────────────────────

def get_maintenance_schedules(db: Session, tenant_id: int):
    return db.query(MaintenanceSchedule).filter(MaintenanceSchedule.tenant_id == tenant_id).all()


def create_maintenance_schedule(db: Session, data: MaintenanceScheduleCreate, tenant_id: int):
    db_obj = MaintenanceSchedule(**data.model_dump(), tenant_id=tenant_id)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_client_detail(db: Session, client_id: int) -> Optional[FleetClientDetail]:
    return db.query(FleetClientDetail).filter(FleetClientDetail.client_id == client_id).first()


# ── MaintenanceSchedule ───────────────────────────────────────────────────

def get_maintenance_schedules(db: Session, tenant_id: int) -> List[MaintenanceSchedule]:
    return db.query(MaintenanceSchedule).filter(
        MaintenanceSchedule.tenant_id == tenant_id
    ).all()


def create_maintenance_schedule(db: Session, data: MaintenanceScheduleCreate, tenant_id: int) -> MaintenanceSchedule:
    s = MaintenanceSchedule(**data.model_dump(), tenant_id=tenant_id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ── Expiry Alerts ─────────────────────────────────────────────────────────

def get_expiry_alerts(db: Session, tenant_id: int, days_ahead: int = 30) -> List[ExpiryAlert]:
    alerts: List[ExpiryAlert] = []
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    vehicles = get_vehicles(db, tenant_id)
    for v in vehicles:
        checks = [
            ("IPVA",          v.ipva_due_date,        f"{v.brand} {v.model} ({v.plate})"),
            ("LICENCIAMENTO", v.licensing_due_date,   f"{v.brand} {v.model} ({v.plate})"),
            ("SEGURO",        v.insurance_expiry,     f"{v.brand} {v.model} ({v.plate})"),
        ]
        for alert_type, due_str, name in checks:
            if not due_str:
                continue
            try:
                due = date.fromisoformat(due_str[:10])
                days_left = (due - today).days
                if days_left <= days_ahead:
                    alerts.append(ExpiryAlert(
                        type=alert_type,
                        asset_id=v.id,
                        asset_name=name,
                        asset_type="vehicle",
                        due_date=due_str[:10],
                        days_left=days_left,
                        plate=v.plate,
                    ))
            except ValueError:
                continue

    # Boat regulatory alerts
    from modules.boats.models import Boat
    boats_with_reg = db.query(Boat, BoatRegulatory).join(
        BoatRegulatory, Boat.id == BoatRegulatory.boat_id
    ).filter(Boat.tenant_id == tenant_id).all()

    for boat, br in boats_with_reg:
        checks = [
            ("DOCUMENTACAO", br.registration_expiry, boat.name),
            ("SEGURO",       br.insurance_expiry,    boat.name),
        ]
        for alert_type, due_str, name in checks:
            if not due_str:
                continue
            try:
                due = date.fromisoformat(due_str[:10])
                days_left = (due - today).days
                if days_left <= days_ahead:
                    alerts.append(ExpiryAlert(
                        type=alert_type,
                        asset_id=boat.id,
                        asset_name=name,
                        asset_type="boat",
                        due_date=due_str[:10],
                        days_left=days_left
                    ))
            except ValueError:
                continue

    return sorted(alerts, key=lambda a: a.days_left)


# ── Cost Reports ──────────────────────────────────────────────────────────

def get_cost_stats(db: Session, tenant_id: int):
    # Total by asset
    requests = db.query(FleetRequest).filter(
        FleetRequest.tenant_id == tenant_id,
        FleetRequest.status == "DONE"
    ).all()

    by_asset: Dict[str, float] = {}
    total_parts = 0.0
    total_labor = 0.0
    total_co2 = 0.0 # kg of CO2

    # CO2 Emission Factors (kg/km)
    # Gasolina: ~0.12 kg/km
    # Diesel: ~0.15 kg/km
    # Flex: ~0.08 kg/km (weighted)
    EMISSION_FACTORS = {
        "GASOLINE": 0.12,
        "DIESEL": 0.15,
        "FLEX": 0.08,
        "ETHANOL": 0.04
    }

    for r in requests:
        if not r.quotes:
            continue
        approved = next((q for q in r.quotes if q.status in ("APPROVED", "DONE")), None)
        if not approved:
            continue

        asset_key = f"V:{r.vehicle_id}" if r.vehicle_id else f"B:{r.boat_id}"
        by_asset[asset_key] = by_asset.get(asset_key, 0.0) + (approved.total_value or 0.0)

        # Estimate mileage impact if vehicle
        if r.vehicle:
            factor = EMISSION_FACTORS.get(str(r.vehicle.fuel_type or "GASOLINE"), 0.12)
            # Assume each service covers a lifecycle of ~5000km for calculation purposes
            total_co2 += 5000 * factor

        for item in (approved.items or []):
            if item.type == "PART":
                total_parts += (item.total or 0.0)
            else:
                total_labor += (item.total or 0.0)

    return {
        "by_asset": by_asset,
        "parts_total": total_parts,
        "labor_total": total_labor,
        "grand_total": total_parts + total_labor,
        "total_co2": total_co2
    }


def get_asset_health_score(db: Session, asset_id: int, is_vehicle: bool = True) -> int:
    """Calculates a health score from 0-100 for an asset."""
    filter_args = {"vehicle_id": asset_id} if is_vehicle else {"boat_id": asset_id}
    requests = db.query(FleetRequest).filter_by(**filter_args).all()
    
    if not requests:
        return 100 # New asset, perfect health
    
    # Penalize for frequency of corrective maintenance
    # Base score 100
    score = 100
    
    # 1. Frequency Penalty
    # More than 3 requests in last 6 months -> penalty
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    recent_requests = [r for r in requests if r.created_at >= six_months_ago]
    if len(recent_requests) > 3:
        score -= (len(recent_requests) - 3) * 10
    
    # 2. Status Penalty
    # If currently in repair -> slight penalty to "current" health
    if any(r.status not in ("DONE", "CANCELLED") for r in requests):
        score -= 5
        
    # 3. Cost Ratio (Placeholder)
    # If total cost > 30% of asset value (simulated) -> penalty
    # (Since we don't have asset value, we use a fixed high threshold)
    total_cost = sum(
        next((q.total_value or 0 for q in r.quotes if q.status in ("APPROVED", "DONE")), 0)
        for r in requests
    )
    if total_cost > 50000: # Arbitrary high cost threshold
        score -= 15

    return max(0, min(100, score))


# ── Preventive Alerts ─────────────────────────────────────────────────────

def get_preventive_alerts(db: Session, tenant_id: int):
    """
    Returns alerts for maintenance schedules that are close to being due.
    Threshold: 90% of interval or within 15 days.
    """
    schedules = db.query(MaintenanceSchedule).filter(
        MaintenanceSchedule.tenant_id == tenant_id
    ).all()

    alerts = []
    today = date.today()

    for s in schedules:
        is_due = False
        reason = ""
        
        # Check by KM (Vehicles)
        if s.interval_km and s.last_done_km:
            # We need the current mileage of the vehicle
            if s.vehicle_id:
                vehicle = db.query(Vehicle).filter(Vehicle.id == s.vehicle_id).first()
                if vehicle:
                    current_km = vehicle.mileage_current
                    next_km = s.last_done_km + s.interval_km
                    # Threshold: 90% of interval reached
                    if current_km >= (s.last_done_km + (s.interval_km * 0.9)):
                        is_due = True
                        reason = f"KM ({current_km} / {next_km})"

        # Check by Days
        if s.interval_days and s.last_done_at:
            try:
                last_date = date.fromisoformat(s.last_done_at[:10])
                next_date = last_date + timedelta(days=s.interval_days)
                days_left = (next_date - today).days
                if days_left <= 15:
                    is_due = True
                    reason = f"Prazo ({days_left} dias restantes)" if not reason else f"{reason} + {days_left}d"
            except ValueError:
                continue

        if is_due:
            asset_name = ""
            if s.vehicle_id:
                asset_name = f"{s.vehicle.brand} {s.vehicle.model} ({s.vehicle.plate})"
            elif s.boat_id:
                asset_name = s.boat.name

            alerts.append({
                "id": s.id,
                "service_type": s.service_type,
                "asset_name": asset_name,
                "reason": reason,
                "status": "DUE_SOON" if "Prazo" in reason or "KM" in reason else "OVERDUE"
            })

    return alerts


# ── Request Messages (Chat) ──────────────────────────────────────────────

def get_messages(db: Session, request_id: int) -> List[RequestMessage]:
    return db.query(RequestMessage).filter(
        RequestMessage.fleet_request_id == request_id
    ).order_by(RequestMessage.created_at.asc()).all()


def create_message(db: Session, request_id: int, user_id: int, message: str) -> RequestMessage:
    msg = RequestMessage(
        fleet_request_id=request_id,
        user_id=user_id,
        message=message
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

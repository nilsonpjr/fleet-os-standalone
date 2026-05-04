"""
Full workflow integration test:
Client creates request → Admin assigns to workshop → Workshop submits quote
→ Admin approves → Client approves → Execution → Workshop requests closure
→ Admin approves closure → Client approves closure → Status DONE
"""
import pytest
from sqlalchemy.orm import Session
from backend_v2.modules.fleet import crud
from backend_v2.modules.fleet.schemas import (
    FleetRequestCreate, WorkshopCreate, VehicleCreate,
    WorkshopQuoteCreate, QuoteItemCreate, ExecutionUpdate,
)
from backend_v2.modules.fleet.models import RequestStatus, QuoteStatus, ExecutionApprovalStatus
from .conftest import _create_tenant, _create_user, _create_client
from backend_v2.modules.auth.models import UserRole


WORKSHOP_PAYLOAD = {
    "name": "Oficina Teste",
    "specialties": ["Motor"],
    "vehicle_types": ["CAR"],
}

VEHICLE_PAYLOAD = {
    "plate": "TST-0001",
    "brand": "Honda",
    "model": "Civic",
}

REQUEST_PAYLOAD = {
    "problem_description": "Motor fazendo barulho estranho ao acelerar",
    "urgency": "HIGH",
}

QUOTE_PAYLOAD = {
    "technician_name": "Carlos Mecânico",
    "diagnosis": "Desgaste na correia do motor",
    "estimated_days": 3,
    "validity_days": 7,
    "items": [
        {
            "type": "PART",
            "description": "Correia do motor",
            "part_sku": "CORR-001",
            "quantity": 1,
            "unit_price": 250.00,
            "total": 250.00,
        },
        {
            "type": "LABOR",
            "description": "Mão de obra - troca de correia",
            "quantity": 2,
            "unit_price": 150.00,
            "total": 300.00,
        },
    ],
}


class TestFullWorkflow:
    """Tests the complete request-to-done lifecycle."""

    def _setup_all(self, db: Session):
        """Create tenant, admin, client user, client record, vehicle, workshop."""
        tenant = _create_tenant(db)
        admin = _create_user(db, tenant.id, UserRole.ADMIN, "admin@wf.test")
        client_user = _create_user(db, tenant.id, UserRole.CLIENT, "client@wf.test")
        client_rec = _create_client(db, tenant.id)
        client_user.client_id = client_rec.id
        db.commit()

        vehicle = crud.create_vehicle(
            db, VehicleCreate(**VEHICLE_PAYLOAD), tenant_id=tenant.id
        )
        workshop = crud.create_workshop(
            db, WorkshopCreate(**WORKSHOP_PAYLOAD), tenant_id=tenant.id
        )
        return {
            "tenant": tenant,
            "admin": admin,
            "client_user": client_user,
            "client": client_rec,
            "vehicle": vehicle,
            "workshop": workshop,
        }

    def test_step1_client_creates_request(self, db):
        ctx = self._setup_all(db)
        req = crud.create_request(
            db,
            FleetRequestCreate(
                vehicle_id=ctx["vehicle"].id,
                **REQUEST_PAYLOAD,
            ),
            client_id=ctx["client"].id,
            tenant_id=ctx["tenant"].id,
        )
        assert req.status == RequestStatus.OPEN
        assert req.client_id == ctx["client"].id
        assert req.vehicle_id == ctx["vehicle"].id

    def test_step2_admin_assigns_to_workshop(self, db):
        ctx = self._setup_all(db)
        req = crud.create_request(
            db,
            FleetRequestCreate(vehicle_id=ctx["vehicle"].id, **REQUEST_PAYLOAD),
            client_id=ctx["client"].id,
            tenant_id=ctx["tenant"].id,
        )
        assigned = crud.assign_request(
            db, req.id, ctx["tenant"].id, [ctx["workshop"].id]
        )
        assert assigned.status == RequestStatus.ASSIGNED
        assert ctx["workshop"].id in assigned.assigned_workshop_ids

    def test_step3_workshop_submits_quote(self, db):
        ctx = self._setup_all(db)
        req = crud.create_request(
            db,
            FleetRequestCreate(vehicle_id=ctx["vehicle"].id, **REQUEST_PAYLOAD),
            client_id=ctx["client"].id,
            tenant_id=ctx["tenant"].id,
        )
        crud.assign_request(db, req.id, ctx["tenant"].id, [ctx["workshop"].id])

        quote = crud.create_quote(
            db,
            request_id=req.id,
            workshop_id=ctx["workshop"].id,
            data=WorkshopQuoteCreate(**QUOTE_PAYLOAD),
        )
        assert quote.total_value == 550.00
        assert quote.subtotal_parts == 250.00
        assert quote.subtotal_labor == 300.00
        assert len(quote.items) == 2

        submitted = crud.submit_quote(db, quote.id, ctx["workshop"].id)
        assert submitted.status == QuoteStatus.SUBMITTED

        db.refresh(req)
        assert req.status == RequestStatus.QUOTED

    def test_step4_double_approval_admin_first(self, db):
        ctx = self._setup_all(db)
        req = crud.create_request(
            db,
            FleetRequestCreate(vehicle_id=ctx["vehicle"].id, **REQUEST_PAYLOAD),
            client_id=ctx["client"].id,
            tenant_id=ctx["tenant"].id,
        )
        crud.assign_request(db, req.id, ctx["tenant"].id, [ctx["workshop"].id])
        quote = crud.create_quote(
            db, req.id, ctx["workshop"].id, WorkshopQuoteCreate(**QUOTE_PAYLOAD)
        )
        crud.submit_quote(db, quote.id, ctx["workshop"].id)

        # Admin approves first → status stays ADMIN_APPROVED
        req_after_admin = crud.approve_request_admin(
            db, req.id, ctx["tenant"].id, quote.id
        )
        assert req_after_admin.status == RequestStatus.ADMIN_APPROVED
        assert req_after_admin.admin_approved_at is not None

        # Client approves → BOTH approved → IN_PROGRESS
        req_done = crud.approve_request_client(
            db, req.id, ctx["tenant"].id, quote.id
        )
        assert req_done.status == RequestStatus.IN_PROGRESS

        db.refresh(quote)
        assert quote.status == QuoteStatus.APPROVED

    def test_step4b_double_approval_client_first(self, db):
        ctx = self._setup_all(db)
        req = crud.create_request(
            db,
            FleetRequestCreate(vehicle_id=ctx["vehicle"].id, **REQUEST_PAYLOAD),
            client_id=ctx["client"].id,
            tenant_id=ctx["tenant"].id,
        )
        crud.assign_request(db, req.id, ctx["tenant"].id, [ctx["workshop"].id])
        quote = crud.create_quote(
            db, req.id, ctx["workshop"].id, WorkshopQuoteCreate(**QUOTE_PAYLOAD)
        )
        crud.submit_quote(db, quote.id, ctx["workshop"].id)

        # Client first → CLIENT_APPROVED
        req_after_client = crud.approve_request_client(
            db, req.id, ctx["tenant"].id, quote.id
        )
        assert req_after_client.status == RequestStatus.CLIENT_APPROVED
        assert req_after_client.admin_approved_at is None

        # Admin second → IN_PROGRESS
        req_in_progress = crud.approve_request_admin(
            db, req.id, ctx["tenant"].id, quote.id
        )
        assert req_in_progress.status == RequestStatus.IN_PROGRESS

    def test_step5_revision_request(self, db):
        ctx = self._setup_all(db)
        req = crud.create_request(
            db,
            FleetRequestCreate(vehicle_id=ctx["vehicle"].id, **REQUEST_PAYLOAD),
            client_id=ctx["client"].id,
            tenant_id=ctx["tenant"].id,
        )
        crud.assign_request(db, req.id, ctx["tenant"].id, [ctx["workshop"].id])
        quote = crud.create_quote(
            db, req.id, ctx["workshop"].id, WorkshopQuoteCreate(**QUOTE_PAYLOAD)
        )
        crud.submit_quote(db, quote.id, ctx["workshop"].id)

        # Admin requests revision
        revised = crud.request_revision(
            db, req.id, ctx["tenant"].id, quote.id, "Peça muito cara, reveja o preço"
        )
        assert revised.status == RequestStatus.REVISION_REQUESTED
        db.refresh(quote)
        assert quote.status == QuoteStatus.REVISION_REQUESTED
        assert "Peça muito cara" in quote.revision_notes

    def test_step6_execution_and_closure(self, db):
        ctx = self._setup_all(db)
        req = crud.create_request(
            db,
            FleetRequestCreate(vehicle_id=ctx["vehicle"].id, **REQUEST_PAYLOAD),
            client_id=ctx["client"].id,
            tenant_id=ctx["tenant"].id,
        )
        crud.assign_request(db, req.id, ctx["tenant"].id, [ctx["workshop"].id])
        quote = crud.create_quote(
            db, req.id, ctx["workshop"].id, WorkshopQuoteCreate(**QUOTE_PAYLOAD)
        )
        crud.submit_quote(db, quote.id, ctx["workshop"].id)

        # Both approve → creates execution
        crud.approve_request_admin(db, req.id, ctx["tenant"].id, quote.id)
        crud.approve_request_client(db, req.id, ctx["tenant"].id, quote.id)

        db.refresh(quote)
        assert quote.execution is not None
        exec_id = quote.execution.id

        # Workshop updates progress (photos, notes)
        updated = crud.update_execution(
            db,
            exec_id,
            ctx["workshop"].id,
            ExecutionUpdate(
                technician_notes="Correia trocada com sucesso",
                labor_hours=2.5,
                total_executed=550.00,
                photos_after=["url/after1.jpg"],
            ),
        )
        assert updated.technician_notes == "Correia trocada com sucesso"
        assert updated.labor_hours == 2.5

        # Workshop requests closure
        closed = crud.request_closure(db, exec_id, ctx["workshop"].id)
        assert closed.completed_at is not None
        db.refresh(req)
        assert req.status == RequestStatus.AWAITING_CLOSURE

        # Admin approves closure
        after_admin = crud.approve_closure_admin(db, exec_id, ctx["tenant"].id)
        assert after_admin.approval_status == ExecutionApprovalStatus.ADMIN_APPROVED

        # Client approves closure → DONE
        final = crud.approve_closure_client(db, exec_id, ctx["tenant"].id)
        assert final.approval_status == ExecutionApprovalStatus.APPROVED
        assert final.closed_at is not None
        db.refresh(req)
        assert req.status == RequestStatus.DONE

    def test_multi_workshop_quotes_rejected_on_approval(self, db):
        """When quote A is approved, other quotes from same request are rejected."""
        ctx = self._setup_all(db)
        workshop2 = crud.create_workshop(
            db,
            WorkshopCreate(name="Oficina 2", specialties=[], vehicle_types=[]),
            tenant_id=ctx["tenant"].id,
        )
        req = crud.create_request(
            db,
            FleetRequestCreate(vehicle_id=ctx["vehicle"].id, **REQUEST_PAYLOAD),
            client_id=ctx["client"].id,
            tenant_id=ctx["tenant"].id,
        )
        crud.assign_request(db, req.id, ctx["tenant"].id,
                            [ctx["workshop"].id, workshop2.id])

        quote1 = crud.create_quote(
            db, req.id, ctx["workshop"].id, WorkshopQuoteCreate(**QUOTE_PAYLOAD)
        )
        quote2 = crud.create_quote(
            db, req.id, workshop2.id,
            WorkshopQuoteCreate(
                technician_name="Outro técnico",
                items=[QuoteItemCreate(
                    type="PART", description="Correia genérica",
                    quantity=1, unit_price=180.00, total=180.00,
                )],
            ),
        )
        crud.submit_quote(db, quote1.id, ctx["workshop"].id)
        crud.submit_quote(db, quote2.id, workshop2.id)

        # Approve quote1 → quote2 should be rejected
        crud.approve_request_admin(db, req.id, ctx["tenant"].id, quote1.id)
        crud.approve_request_client(db, req.id, ctx["tenant"].id, quote1.id)

        db.refresh(quote1)
        db.refresh(quote2)
        assert quote1.status == QuoteStatus.APPROVED
        assert quote2.status == QuoteStatus.REJECTED

    def test_list_request_quotes(self, db):
        """Admin-facing helper should list all quotes for the request."""
        ctx = self._setup_all(db)
        workshop2 = crud.create_workshop(
            db,
            WorkshopCreate(name="Oficina 2", specialties=[], vehicle_types=[]),
            tenant_id=ctx["tenant"].id,
        )
        req = crud.create_request(
            db,
            FleetRequestCreate(vehicle_id=ctx["vehicle"].id, **REQUEST_PAYLOAD),
            client_id=ctx["client"].id,
            tenant_id=ctx["tenant"].id,
        )
        crud.assign_request(db, req.id, ctx["tenant"].id, [ctx["workshop"].id, workshop2.id])
        q1 = crud.create_quote(db, req.id, ctx["workshop"].id, WorkshopQuoteCreate(**QUOTE_PAYLOAD))
        q2 = crud.create_quote(
            db,
            req.id,
            workshop2.id,
            WorkshopQuoteCreate(
                technician_name="Outro técnico",
                items=[QuoteItemCreate(
                    type="PART",
                    description="Componente",
                    quantity=1,
                    unit_price=100.0,
                    total=100.0,
                )],
            ),
        )
        quotes = crud.get_request_quotes(db, req.id, ctx["tenant"].id)
        assert len(quotes) == 2
        assert {q.id for q in quotes} == {q1.id, q2.id}


class TestFleetRequestPermissions:
    """Test role-based access to fleet request endpoints."""

    def test_client_can_create_request(self, http, db, client_setup):
        token, _, _, _ = client_setup
        resp = http.post(
            "/api/fleet/requests",
            json=REQUEST_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "OPEN"

    def test_unauthenticated_cannot_access(self, http, db):
        resp = http.get("/api/fleet/requests")
        assert resp.status_code == 401

    def test_admin_sees_all_requests(self, http, db, admin_token):
        token, _, _ = admin_token
        resp = http.get("/api/fleet/requests",
                        headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

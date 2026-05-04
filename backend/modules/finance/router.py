"""Finance module router — /transactions and /finance endpoints."""
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from modules.auth.models import User
from modules.finance.schemas import TransactionRead, TransactionCreate
from modules.finance.crud import get_transactions, create_transaction
from modules.fleet.models import FleetRequest
from backend.services.payment_service import payment_service

router = APIRouter(prefix="/api/transactions", tags=["Transações Financeiras"])


@router.get("", response_model=List[TransactionRead])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_transactions(db, tenant_id=current_user.tenant_id)


@router.post("", response_model=TransactionRead)
def create_new_transaction(
    transaction: TransactionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_transaction(db, transaction, tenant_id=current_user.tenant_id)


@router.post("/import", response_model=List[TransactionRead])
async def import_financial_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Imports transactions from CSV, OFX or PDF bank statements."""
    content = await file.read()
    filename = (file.filename or "").lower()

    try:
        # Import the same service used in the original backend
        from backend.services.finance_import_service import FinanceImportService  # type: ignore

        if filename.endswith(".csv"):
            rows = FinanceImportService.parse_csv(content)
        elif filename.endswith(".pdf"):
            rows = FinanceImportService.parse_pdf(content)
        elif filename.endswith(".ofx"):
            rows = FinanceImportService.parse_ofx(content)
        else:
            raise HTTPException(status_code=400, detail="Formato não suportado. Use CSV, PDF ou OFX.")

        result = []
        for row in rows:
            txn = TransactionCreate(
                type=row.get("type", "EXPENSE"),
                category=row.get("category", "Importado"),
                description=row.get("description", "Sem descrição"),
                amount=row.get("amount", 0.0),
                date=row.get("date"),
                status=row.get("status", "PAID"),
                document_number=row.get("document_number"),
            )
            result.append(create_transaction(db, txn, tenant_id=current_user.tenant_id))
        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao processar importação: {exc}")


@router.get("/pix/{request_id}")
def get_pix_payment(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates PIX data for a specific fleet request."""
    req = db.query(FleetRequest).filter(
        FleetRequest.id == request_id,
        FleetRequest.tenant_id == current_user.tenant_id
    ).first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    
    # Get approved quote
    quote = next((q for q in req.quotes if q.status in ("APPROVED", "DONE")), None)
    if not quote:
        raise HTTPException(status_code=400, detail="Não há orçamento aprovado para esta solicitação.")
    
    # Use fallback data if tenant config is missing
    pix_key = "00000000000" # TODO: Fetch from Tenant config
    merchant_name = "FleetOS Solutions"
    merchant_city = "Florianopolis"
    
    pix_string = payment_service.generate_static_pix(
        pix_key=pix_key,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
        amount=float(quote.total_value or 0.0),
        description=f"Servico #{req.id}"
    )
    
    qr_code = payment_service.generate_qr_code_base64(pix_string)
    
    return {
        "pix_string": pix_string,
        "qr_code": qr_code,
        "amount": quote.total_value,
        "recipient": merchant_name
    }

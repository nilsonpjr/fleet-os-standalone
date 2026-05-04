from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend_v2.core.database import get_db
from backend_v2.core.dependencies import get_current_user
from backend_v2.modules.auth.models import User
from backend_v2.modules.notifications.schemas import NotificationRead
from backend_v2.modules.notifications import crud

router = APIRouter(prefix="/api/notifications", tags=["Notificações"])

@router.get("", response_model=List[NotificationRead])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.get_notifications(db, user_id=current_user.id, tenant_id=current_user.tenant_id)

@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = crud.mark_as_read(db, notification_id, current_user.id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notificação não encontrada.")
    return notif

@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crud.mark_all_as_read(db, current_user.id)
    return {"status": "success"}

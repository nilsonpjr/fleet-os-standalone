from sqlalchemy.orm import Session
from modules.notifications.models import Notification
from modules.notifications.schemas import NotificationCreate

def get_notifications(db: Session, user_id: int, tenant_id: int, limit: int = 20):
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.tenant_id == tenant_id
    ).order_by(Notification.created_at.desc()).limit(limit).all()

def create_notification(db: Session, data: NotificationCreate, tenant_id: int):
    db_obj = Notification(
        **data.model_dump(),
        tenant_id=tenant_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def mark_as_read(db: Session, notification_id: int, user_id: int):
    db_obj = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    if db_obj:
        db_obj.is_read = True
        db.commit()
        db.refresh(db_obj)
    return db_obj

def mark_all_as_read(db: Session, user_id: int):
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()

def notify_user(db: Session, user_id: int, tenant_id: int, title: str, message: str, type: str = "info", link: str = None):
    return create_notification(db, NotificationCreate(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        link=link
    ), tenant_id=tenant_id)

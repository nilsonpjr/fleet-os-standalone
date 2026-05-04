from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # info, success, warning, error
    
    is_read = Column(Boolean, default=False)
    link = Column(String(500), nullable=True)  # URL to redirect when clicked
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel
from core.database import get_db
from modules.fleet.models import Vehicle

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

class TelemetryData(BaseModel):
    device_id: str  # Map this to vehicle plate or custom ID
    lat: float
    lng: float
    mileage: float

@router.post("/hook")
def receive_telemetry(data: TelemetryData, db: Session = Depends(get_db)):
    """Webhook for IoT devices to send status updates."""
    # Find vehicle by plate (simplified mapping)
    vehicle = db.query(Vehicle).filter(Vehicle.plate == data.device_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    vehicle.last_lat = data.lat
    vehicle.last_lng = data.lng
    vehicle.last_sync_at = datetime.now(timezone.utc)
    vehicle.mileage_current = data.mileage
    
    db.commit()
    return {"status": "success", "synced_at": vehicle.last_sync_at}

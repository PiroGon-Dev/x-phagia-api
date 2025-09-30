# ============================================================================
# routes/devices.py - Device Management Routes
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Device, User
from ..schemas import DeviceResponse
from ..auth import get_current_user
from ..config import settings

router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("/", response_model=List[DeviceResponse])
async def get_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all registered devices"""
    devices = db.query(Device).all()
    return devices

@router.get("/current", response_model=DeviceResponse)
async def get_current_device(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current device information"""
    device = db.query(Device).filter(
        Device.serial_number == settings.device_serial_number
    ).first()
    
    if not device:
        # Auto-register device if not found
        device = Device(
            serial_number=settings.device_serial_number,
            name=settings.device_name,
            firmware_version=settings.firmware_version
        )
        db.add(device)
        db.commit()
        db.refresh(device)
    
    return device

@router.put("/current/status")
async def update_device_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current device status"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    device = db.query(Device).filter(
        Device.serial_number == settings.device_serial_number
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    from ..models import DeviceStatus
    try:
        device.status = DeviceStatus(status)
        from datetime import datetime
        device.last_online = datetime.utcnow()
        db.commit()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device status"
        )
    
    return {"message": "Device status updated successfully"}
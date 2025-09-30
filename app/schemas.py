# ============================================================================
# schemas.py - Pydantic Models (Pydantic v2 compliant)
# ============================================================================

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime
from .models import PatientSex, SessionStatus, OperatorType, DeviceStatus, UserRole
from uuid import UUID
patient_id: UUID
device_id: UUID


# Patient Schemas
class PatientBase(BaseModel):
    patient_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: Optional[datetime]
    sex: Optional[PatientSex]
    medical_record_number: Optional[str] = Field(None, max_length=50)

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True   # ✅ updated for Pydantic v2

# Session Schemas
class SessionBase(BaseModel):
    session_number: int = Field(..., ge=1, le=9999)
    threshold_level: float = Field(..., ge=0.0, le=50.0)
    tolerance_level: float = Field(..., ge=0.0, le=50.0)
    stimulation_level: float = Field(..., ge=0.0, le=50.0)
    frequency_level: float = Field(..., ge=1.0, le=1000.0)
    pulse_width_level: float = Field(..., ge=1.0, le=1000.0)
    operator_name: str = Field(..., min_length=2, max_length=100)
    notes: Optional[str] = None

class SessionCreate(SessionBase):
    patient_id: str = Field(..., pattern=r'^[a-f0-9\-]{36}$')
    device_id: str = Field(..., pattern=r'^[a-f0-9\-]{36}$')   # ✅ regex → pattern
    operator_type: OperatorType = OperatorType.LOGIN

class SessionResponse(SessionBase):
    id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: SessionStatus
    patient_id: str
    device_id: str
    operator_type: OperatorType
    test_passed: Optional[bool]
    stimulation_status: Optional[str]
    
    class Config:
        from_attributes = True   # ✅ updated

# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class KioskPinRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=6)

# Device Schemas
class DeviceResponse(BaseModel):
    id: str
    serial_number: str
    name: str
    model: Optional[str]
    firmware_version: Optional[str]
    software_version: Optional[str]
    status: DeviceStatus
    last_calibration: Optional[datetime]
    next_maintenance: Optional[datetime]
    registered_at: datetime
    
    class Config:
        from_attributes = True   # ✅ updated

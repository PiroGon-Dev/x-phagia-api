# ============================================================================
# routes/patients.py - Patient Management Routes
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from typing import List, Optional
from ..database import get_db
from ..models import Patient, User
from ..schemas import PatientCreate, PatientResponse
from ..auth import get_current_user
from ..services import AuditLogger

router = APIRouter(prefix="/patients", tags=["patients"])



def serialize_for_json(data: dict):
    """Convert datetime objects to ISO strings for JSON serialization."""
    def _serialize(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value
    
    return {k: _serialize(v) for k, v in data.items()}


@router.get("/", response_model=List[PatientResponse])
async def get_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, min_length=2),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all patients with optional search and pagination"""
    query = db.query(Patient)
    
    if search:
        query = query.filter(
            or_(
                Patient.name.ilike(f"%{search}%"),
                Patient.patient_number.ilike(f"%{search}%"),
                Patient.medical_record_number.ilike(f"%{search}%")
            )
        )
    
    patients = query.offset(skip).limit(limit).all()
    return patients

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new patient"""
    # Check if patient number already exists
    existing = db.query(Patient).filter(Patient.patient_number == patient.patient_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient number already exists"
        )
    
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    # Audit log
    audit_logger = AuditLogger(db)
    await audit_logger.log_action(
        user_id=current_user.id,
        action="CREATE",
        resource_type="patient",
        resource_id=db_patient.id,
        new_values=serialize_for_json(patient.dict())
    )
    
    return db_patient

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific patient by ID"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return patient

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_update: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a patient"""
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Store old values for audit
    old_values = {
        "name": db_patient.name,
        "patient_number": db_patient.patient_number,
        "date_of_birth": db_patient.date_of_birth,
        "sex": db_patient.sex,
        "medical_record_number": db_patient.medical_record_number
    }
    
    # Update fields
    for field, value in patient_update.dict().items():
        setattr(db_patient, field, value)
    
    from datetime import datetime
    db_patient.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_patient)
    
    # Audit log
    audit_logger = AuditLogger(db)
    await audit_logger.log_action(
        user_id=current_user.id,
        action="UPDATE",
        resource_type="patient",
        resource_id=patient_id,
        old_values=old_values,
        new_values=serialize_for_json(patient_update.dict())
    )
    
    return db_patient

@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a patient and all associated sessions"""
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Store for audit
    old_values = {
        "name": db_patient.name,
        "patient_number": db_patient.patient_number
    }
    
    db.delete(db_patient)
    db.commit()
    
    # Audit log
    audit_logger = AuditLogger(db)
    await audit_logger.log_action(
        user_id=current_user.id,
        action="DELETE",
        resource_type="patient",
        resource_id=patient_id,
        old_values=old_values
    )
    
    return {"message": "Patient deleted successfully"}
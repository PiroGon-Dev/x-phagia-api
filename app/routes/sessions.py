# ============================================================================
# routes/sessions.py - Session Management Routes
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from typing import List, Optional
from ..database import get_db
from ..models import Session, Patient, Device, User
from ..schemas import SessionCreate, SessionResponse
from ..auth import get_current_user
from ..services import FileManager, AuditLogger
from ..config import settings

router = APIRouter(prefix="/sessions", tags=["sessions"])
file_manager = FileManager(settings.data_path)

@router.get("/", response_model=List[SessionResponse])
async def get_sessions(
    patient_id: Optional[str] = None,
    device_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sessions with optional filtering"""
    query = db.query(Session).order_by(desc(Session.start_time))
    
    if patient_id:
        query = query.filter(Session.patient_id == patient_id)
    if device_id:
        query = query.filter(Session.device_id == device_id)
    
    sessions = query.offset(skip).limit(limit).all()
    return sessions

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session: SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new therapy session"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == session.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Verify device exists
    device = db.query(Device).filter(Device.id == session.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Create session
    db_session = Session(
        **session.dict(),
        operator_id=current_user.id if hasattr(current_user, 'id') else "kiosk"
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Create file directory
    file_manager.create_session_directory(db_session.id)
    
    # Audit log
    audit_logger = AuditLogger(db)
    await audit_logger.log_action(
        user_id=getattr(current_user, 'id', 'kiosk'),
        action="CREATE",
        resource_type="session",
        resource_id=db_session.id,
        new_values=session.dict()
    )
    
    return db_session

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific session"""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session

@router.put("/{session_id}/complete")
async def complete_session(
    session_id: str,
    test_passed: bool = Form(...),
    stimulation_status: str = Form(...),
    notes: Optional[str] = Form(None),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete a therapy session"""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    from datetime import datetime
    from ..models import SessionStatus
    
    session.end_time = datetime.utcnow()
    session.status = SessionStatus.COMPLETED
    session.test_passed = test_passed
    session.stimulation_status = stimulation_status
    if notes:
        session.notes = notes
    
    db.commit()
    
    return {"message": "Session completed successfully"}

@router.post("/{session_id}/upload/{signal_type}")
async def upload_signal_data(
    session_id: str,
    signal_type: str,
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload signal data for a session"""
    # Validate signal type
    valid_signals = ["impedance", "ecg", "emg", "pressure", "temperature"]
    if signal_type not in valid_signals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid signal type. Must be one of: {valid_signals}"
        )
    
    # Verify session exists
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check file size
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large"
        )
    
    # Save file
    content = await file.read()
    file_path = await file_manager.save_signal_data(session_id, signal_type, content)
    
    # Update session with file path
    setattr(session, f"{signal_type}_path", file_path)
    db.commit()
    
    return {"message": f"{signal_type} data uploaded successfully", "file_path": file_path}

@router.get("/{session_id}/export")
async def export_session(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export session data as ZIP file"""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    export_path = file_manager.export_session(session_id)
    
    return FileResponse(
        path=export_path,
        filename=f"session_{session_id}.zip",
        media_type="application/zip"
    )
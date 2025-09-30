# ============================================================================
# routes/system.py - System Management Routes
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from ..database import get_db
from ..models import User, Patient, Session as DBSession, AuditLog
from ..auth import get_current_user
from ..services import BackupService
from ..config import settings

router = APIRouter(prefix="/system", tags=["system"])
backup_service = BackupService()

@router.get("/health")
async def health_check():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/stats")
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system statistics"""
    stats = {
        "patients": db.query(func.count(Patient.id)).scalar(),
        "sessions": db.query(func.count(DBSession.id)).scalar(),
        "active_sessions": db.query(func.count(DBSession.id)).filter(
            DBSession.status == "active"
        ).scalar(),
        "completed_sessions": db.query(func.count(DBSession.id)).filter(
            DBSession.status == "completed"
        ).scalar()
    }
    
    return stats

@router.post("/backup")
async def create_backup(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create system backup"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    background_tasks.add_task(backup_service.create_full_backup)
    
    return {"message": "Backup initiated"}

@router.get("/audit")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "success": log.success,
            "ip_address": log.ip_address
        }
        for log in logs
    ]
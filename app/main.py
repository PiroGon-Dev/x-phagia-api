from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
import uvicorn
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import shutil

# Import modules (these would be separate files in actual implementation)
from .config import settings
from .database import engine, get_db, Base
from .models import *
from .schemas import *
from .auth import get_current_user, create_access_token, verify_password, verify_kiosk_pin
from .services import FileManager, BackupService, AuditLogger

# Import routes - Fixed import
from .routes import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    Base.metadata.create_all(bind=engine)
    
    # Initialize default admin user if none exists
    db = next(get_db())
    try:
        from .models import User, UserRole
        from .auth import hash_password
        
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin_user:
            default_admin = User(
                email="superadmin@pirogon.com",
                username="superadmin",
                full_name="System Administrator",
                password_hash=hash_password("SuperSecret123!"),  # Change in production!
                role=UserRole.ADMIN
            )
            db.add(default_admin)
            db.commit()
            logging.info("Default admin user created: superadmin@localhost / SuperSecret123!")
        
        # Initialize current device if not exists
        from .models import Device, DeviceStatus
        device = db.query(Device).filter(Device.serial_number == settings.device_serial_number).first()
        if not device:
            device = Device(
                serial_number=settings.device_serial_number,
                name=settings.device_name,
                firmware_version=settings.firmware_version,
                software_version="1.0.0",
                status=DeviceStatus.ACTIVE,
                kiosk_pin_hash=hash_password("1234") if settings.kiosk_enabled else None
            )
            db.add(device)
            db.commit()
            logging.info(f"Device registered: {settings.device_serial_number}")
            
    except Exception as e:
        logging.error(f"Error during startup initialization: {e}")
        db.rollback()
    finally:
        db.close()
    
    logging.info("PiroGon Device API started successfully")
    yield
    # Shutdown
    logging.info("Medical Device API shutting down")

app = FastAPI(
    title="PiroGon Device API",
    description="Local-based PiroGon device data management system",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        settings.device_ip  # e.g., "192.168.1.100"
    ]
)




# Security
security = HTTPBearer()

# Services
file_manager = FileManager(settings.data_path)
backup_service = BackupService(f"{settings.data_path}/backups")
audit_logger = AuditLogger()

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "PiroGon Device API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/api/v1/system/health",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# Additional health check at root level
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Disable in production
        log_level="info"
    )
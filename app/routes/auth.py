# ============================================================================  
# routes/auth.py - Authentication Routes  
# ============================================================================  

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from ..auth import hash_password
from ..models import UserRole
from datetime import datetime
from ..database import get_db
from ..models import User, Device
from ..schemas import LoginRequest, TokenResponse, KioskPinRequest
from ..auth import verify_password, create_access_token, verify_kiosk_pin
from ..config import settings
from ..auth import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

# ----------------------------
# User login
# ----------------------------
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """User login with email and password"""
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
    )

# ----------------------------
# Kiosk login
# ----------------------------
@router.post("/kiosk", response_model=TokenResponse)
async def kiosk_login(request: KioskPinRequest, db: Session = Depends(get_db)):
    """Kiosk login with PIN"""
    if not settings.kiosk_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kiosk mode is disabled"
        )

    device = db.query(Device).filter(Device.serial_number == settings.device_serial_number).first()
    if not device or not verify_kiosk_pin(request.pin, device):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN"
        )

    access_token = create_access_token(
        data={"sub": "kiosk", "device_id": device.id, "role": "kiosk"}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user={
            "id": "kiosk",
            "device_id": device.id,
            "role": "kiosk"
        }
    )

# ----------------------------
# Current user info
# ----------------------------
@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login
    }




# ----------------------------
# Create new user (admin only)
# ----------------------------
@router.post("/create-user", response_model=dict)
async def create_user(
    email: str = Body(...),
    username: str = Body(...),
    full_name: str = Body(...),
    password: str = Body(...),
    role: UserRole = Body(UserRole.OPERATOR),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user - Admin only"""
    
    # Only admins can create users
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )
    
    # Check if email or username already exists
    if db.query(User).filter((User.email == email) | (User.username == username)).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already exists"
        )
    
    new_user = User(
        email=email,
        username=username,
        full_name=full_name,
        password_hash=hash_password(password),
        role=role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "full_name": new_user.full_name,
        "role": new_user.role.value,
        "is_active": new_user.is_active
    }

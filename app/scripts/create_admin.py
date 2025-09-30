# scripts/create_admin.py - Create initial admin user
import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import User, Device, Base
from app.auth import hash_password
from app.config import settings

async def create_admin_user():
    """Create initial admin user and device"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@meddevice.local").first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            email="admin@meddevice.local",
            username="admin",
            full_name="System Administrator",
            password_hash=hash_password("admin123"),
            role="admin"
        )
        db.add(admin)
        
        # Create device record
        device = db.query(Device).filter(Device.serial_number == settings.device_serial_number).first()
        if not device:
            device = Device(
                serial_number=settings.device_serial_number,
                name=settings.device_name,
                model="Compute Module 5",
                firmware_version=settings.firmware_version,
                software_version="1.0.0",
                status="active",
                kiosk_pin_hash=hash_password("1234")  # Default PIN
            )
            db.add(device)
        
        db.commit()
        print("Admin user and device created successfully")
        print("Email: admin@meddevice.local")
        print("Password: admin123")
        print("Default Kiosk PIN: 1234")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}")
    finally:
        db.close()
# ============================================================================
# models.py - SQLAlchemy Database Models
# ============================================================================

from sqlalchemy import Column, String, Integer, DateTime, Float, Boolean, ForeignKey, Enum, Text, JSON, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import datetime
import uuid
from enum import Enum as PyEnum

# ✅ Import the shared Base
from .database import Base

# Enums
class PatientSex(str, PyEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class SessionStatus(str, PyEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABORTED = "aborted"
    ERROR = "error"

class OperatorType(str, PyEnum):
    LOGIN = "login"
    KIOSK = "kiosk"

class DeviceStatus(str, PyEnum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"
    OFFLINE = "offline"

class UserRole(str, PyEnum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

# Models
class Device(Base):
    __tablename__ = "devices"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    serial_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    model = Column(String)
    firmware_version = Column(String)
    software_version = Column(String)
    
    # Status & Maintenance
    status = Column(Enum(DeviceStatus), default=DeviceStatus.ACTIVE)
    last_calibration = Column(DateTime)
    next_maintenance = Column(DateTime)
    
    # Security
    encryption_key_fingerprint = Column(String)
    kiosk_pin_hash = Column(String)
    
    # Timestamps
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_online = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="device")

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    date_of_birth = Column(DateTime)
    sex = Column(Enum(PatientSex))
    medical_record_number = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="patient", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_number = Column(Integer, nullable=False)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    
    # Therapy Parameters
    threshold_level = Column(Float)
    tolerance_level = Column(Float)
    stimulation_level = Column(Float)
    frequency_level = Column(Float)  # Hz
    pulse_width_level = Column(Float)  # μs
    
    # File Paths (relative to session directory)
    impedance_path = Column(String)
    ecg_path = Column(String)
    emg_path = Column(String)
    pressure_path = Column(String)
    temperature_path = Column(String)
    
    # Operator Information
    operator_id = Column(String)
    operator_name = Column(String)
    operator_type = Column(Enum(OperatorType))
    
    # Session Results
    test_passed = Column(Boolean)
    stimulation_status = Column(String)
    notes = Column(Text)
    
    # Foreign Keys
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="sessions")
    device = relationship("Device", back_populates="sessions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_session_patient_id', 'patient_id'),
        Index('idx_session_start_time', 'start_time'),
        Index('idx_session_device_id', 'device_id'),
    )

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    password_hash = Column(String, nullable=False)
    
    # Role & Status
    role = Column(Enum(UserRole), default=UserRole.OPERATOR)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String, nullable=False)  # CREATE, READ, UPDATE, DELETE
    resource_type = Column(String, nullable=False)  # session, patient, device
    resource_id = Column(String, nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    success = Column(Boolean, default=True)
    error_message = Column(String)


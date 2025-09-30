# ============================================================================
# config.py - Configuration Settings
# ============================================================================

from pydantic_settings import BaseSettings
from pydantic import Extra

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///../database/pgdevice.db" 
    
    # Security
    secret_key: str = "PGDEVICESECRETKEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File Storage
    data_path: str = "/data"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Device Configuration
    device_serial_number: str = "CM5-001"
    device_name: str = "Medical Device CM5"
    firmware_version: str = "1.0.0"
    device_ip: str = "192.168.1.100"
    
    # Kiosk Mode
    kiosk_enabled: bool = True
    kiosk_pin_hash: str = "$2b$12$"  # Set bcrypt hash of PIN
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
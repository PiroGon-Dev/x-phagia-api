# ============================================================================
# services.py - Business Logic Services
# ============================================================================

import shutil
import zipfile
import aiofiles
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Request
from .models import AuditLog

class FileManager:
    def __init__(self, base_path: str = "/data"):
        self.base_path = Path(base_path)
        self.sessions_path = self.base_path / "sessions"
        self.exports_path = self.base_path / "exports"
        
        # Ensure directories exist
        self.sessions_path.mkdir(parents=True, exist_ok=True)
        self.exports_path.mkdir(parents=True, exist_ok=True)
    
    def create_session_directory(self, session_id: str) -> Path:
        session_dir = self.sessions_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "signals").mkdir(exist_ok=True)
        return session_dir
    
    async def save_signal_data(self, session_id: str, signal_type: str, data: bytes) -> str:
        session_dir = self.sessions_path / session_id / "signals"
        file_path = session_dir / f"{signal_type}.csv"
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(data)
        
        return str(file_path.relative_to(self.base_path))
    
    async def save_session_metadata(self, session_id: str, metadata: Dict[str, Any]):
        session_dir = self.sessions_path / session_id
        metadata_path = session_dir / "metadata.json"
        
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata, indent=2, default=str))
    
    def export_session(self, session_id: str) -> Path:
        session_dir = self.sessions_path / session_id
        export_path = self.exports_path / f"session_{session_id}.zip"
        
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in session_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(session_dir)
                    zipf.write(file_path, arcname)
        
        return export_path

class AuditLogger:
    def __init__(self, db_session: Session = None):
        self.db = db_session

    def _serialize(self, data: dict):
        if not data:
            return None
        def convert(value):
            if isinstance(value, datetime):
                return value.isoformat()
            return value
        return {k: convert(v) for k, v in data.items()}

    async def log_action(self, user_id: str, action: str, resource_type: str, 
                         resource_id: str, old_values: dict = None, 
                         new_values: dict = None, success: bool = True, 
                         error_message: str = None, request: Request = None):

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=self._serialize(old_values),
            new_values=self._serialize(new_values),
            success=success,
            error_message=error_message,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )

        if self.db:
            self.db.add(audit_log)
            self.db.commit()

    def __init__(self, db_session: Session = None):
        self.db = db_session
    
    async def log_action(self, user_id: str, action: str, resource_type: str, 
                        resource_id: str, old_values: dict = None, 
                        new_values: dict = None, success: bool = True, 
                        error_message: str = None, request: Request = None):
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            success=success,
            error_message=error_message,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )
        
        if self.db:
            self.db.add(audit_log)
            self.db.commit()

class BackupService:
    def __init__(self, backup_path: str = "/data/backups"):
        self.backup_path = Path(backup_path)
        self.backup_path.mkdir(parents=True, exist_ok=True)
    
    async def create_full_backup(self) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"full_backup_{timestamp}"
        backup_dir = self.backup_path / backup_name
        backup_dir.mkdir(exist_ok=True)
        
        # Create backup (implementation would depend on database type)
        # This is a simplified example
        archive_path = backup_dir.with_suffix('.tar.gz')
        shutil.make_archive(str(backup_dir), 'gztar', str(backup_dir))
        
        return str(archive_path)
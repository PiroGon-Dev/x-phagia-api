# ============================================================================
# routes/__init__.py - Routes Module Initialization
# ============================================================================

from fastapi import APIRouter

# Import individual route modules
try:
    from . import auth, patients, sessions, devices, system
    
    # Create main API router
    api_router = APIRouter()
    
    # Include all route modules
    api_router.include_router(auth.router)
    api_router.include_router(patients.router)
    api_router.include_router(sessions.router)
    api_router.include_router(devices.router)
    api_router.include_router(system.router)
    
except ImportError as e:
    print(f"Warning: Could not import route module: {e}")
    # Create empty router as fallback
    api_router = APIRouter()

# Export the main router
__all__ = ["api_router"]
"""
V2 Settings Routes - System settings with proper layering
Uses: SettingsService -> SettingsRepository
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_postgres_session
from app.repositories.settings_repository import SettingsRepository
from app.services.settings_service import SettingsService
from routes.v2_auth_routes import get_current_user, UserRole


router = APIRouter(
    prefix="/api/v2/settings",
    tags=["V2 Settings"]
)


# ==================== Dependencies ====================

def get_settings_service(session: AsyncSession = Depends(get_postgres_session)) -> SettingsService:
    """Get settings service with repository"""
    repository = SettingsRepository(session)
    return SettingsService(repository)


def require_admin_or_gm(user):
    """Check if user is admin or general manager"""
    if user.role not in [UserRole.SYSTEM_ADMIN, UserRole.GENERAL_MANAGER, UserRole.PROCUREMENT_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="صلاحيات غير كافية"
        )


# ==================== Pydantic Models ====================

class SettingUpdate(BaseModel):
    value: str


class SettingResponse(BaseModel):
    key: str
    value: str
    description: str = None
    updated_by_name: str = None
    updated_at: str = None


# ==================== Endpoints ====================

@router.get("")
async def get_all_settings(
    current_user = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Get all system settings
    Uses: SettingsService -> SettingsRepository
    """
    require_admin_or_gm(current_user)
    return await service.get_all_settings()


@router.get("/{key}")
async def get_setting(
    key: str,
    current_user = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Get a specific setting by key
    Uses: SettingsService -> SettingsRepository
    """
    require_admin_or_gm(current_user)
    value = await service.get_setting(key)
    
    if value is None:
        raise HTTPException(status_code=404, detail="الإعداد غير موجود")
    
    return {"key": key, "value": value}


@router.put("/{key}")
async def update_setting(
    key: str,
    data: SettingUpdate,
    current_user = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Update a specific setting
    Uses: SettingsService -> SettingsRepository
    """
    require_admin_or_gm(current_user)
    
    await service.set_setting(
        key=key,
        value=data.value,
        user_id=current_user.id,
        user_name=current_user.name
    )
    
    return {"message": f"تم تحديث الإعداد {key} بنجاح"}


@router.get("/system/approval-limit")
async def get_approval_limit(
    current_user = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Get the GM approval limit
    Uses: SettingsService -> SettingsRepository
    """
    limit = await service.get_approval_limit()
    return {"approval_limit": limit}

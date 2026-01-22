"""
V2 Sysadmin Routes - System administration with proper layering
Uses: SettingsService -> SettingsRepository
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Dict, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid
from pathlib import Path

from database import get_postgres_session
from app.repositories.settings_repository import SettingsRepository
from app.services.settings_service import SettingsService
from routes.v2_auth_routes import get_current_user, UserRole

# مجلد رفع الملفات
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


router = APIRouter(
    prefix="/api/v2/sysadmin",
    tags=["V2 System Admin"]
)


# ==================== Dependencies ====================

def get_settings_service(session: AsyncSession = Depends(get_postgres_session)) -> SettingsService:
    """Get settings service with repository"""
    repository = SettingsRepository(session)
    return SettingsService(repository)


def require_system_admin(user):
    """Check if user is system admin"""
    if user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="صلاحيات مدير النظام مطلوبة"
        )


# ==================== Pydantic Models ====================

class CompanySettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    report_header: Optional[str] = None
    report_footer: Optional[str] = None
    pdf_primary_color: Optional[str] = None
    pdf_show_logo: Optional[str] = None


# ==================== Endpoints ====================

@router.get("/company-settings")
async def get_company_settings(
    current_user = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Get company settings for PDF customization - System Admin only
    Uses: SettingsService -> SettingsRepository
    """
    require_system_admin(current_user)
    return await service.get_company_settings()


@router.get("/company-settings/public")
async def get_company_settings_public(
    current_user = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Get company settings for PDF customization - Available for all authenticated users
    Uses: SettingsService -> SettingsRepository
    """
    return await service.get_company_settings()


@router.put("/company-settings")
async def update_company_settings(
    settings_data: CompanySettingsUpdate,
    current_user = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Update company settings - System Admin only
    Uses: SettingsService -> SettingsRepository
    """
    require_system_admin(current_user)
    
    updates = settings_data.dict(exclude_none=True)
    await service.update_company_settings(
        settings=updates,
        user_id=current_user.id,
        user_name=current_user.name
    )
    
    return {"message": "تم تحديث إعدادات الشركة بنجاح"}


@router.get("/settings")
async def get_all_settings(
    current_user = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Get all system settings - System Admin only
    Uses: SettingsService -> SettingsRepository
    """
    require_system_admin(current_user)
    return await service.get_all_settings()


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    value: Dict,
    current_user = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Update a single system setting - System Admin only
    Uses: SettingsService -> SettingsRepository
    """
    require_system_admin(current_user)
    
    await service.set_setting(
        key=key,
        value=str(value.get("value", "")),
        user_id=current_user.id,
        user_name=current_user.name
    )
    
    return {"message": f"تم تحديث الإعداد {key} بنجاح"}

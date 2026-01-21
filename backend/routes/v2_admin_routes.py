"""
V2 Admin Routes - System administration with proper layering
Uses: AdminService -> AdminRepository
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_postgres_session
from app.repositories.admin_repository import AdminRepository
from app.services.admin_service import AdminService
from routes.v2_auth_routes import get_current_user, UserRole


router = APIRouter(
    prefix="/api/v2/admin",
    tags=["V2 Admin"]
)


# ==================== Dependencies ====================

def get_admin_service(session: AsyncSession = Depends(get_postgres_session)) -> AdminService:
    """Get admin service with repository"""
    repository = AdminRepository(session)
    return AdminService(repository)


def require_system_admin(user):
    """Check if user is system admin"""
    if user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط مدير النظام يمكنه الوصول لهذه الصفحة"
        )


# ==================== Pydantic Models ====================

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    supervisor_prefix: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    supervisor_prefix: Optional[str] = None


class PasswordReset(BaseModel):
    new_password: str


# ==================== Users Endpoints ====================

@router.get("/users")
async def get_users(
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Get all users - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    return await service.get_all_users()


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Get user by ID - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return user


@router.post("/users")
async def create_user(
    data: UserCreate,
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Create a new user - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    
    try:
        return await service.create_user(
            name=data.name,
            email=data.email,
            password=data.password,
            role=data.role
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Update a user - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    
    updates = data.dict(exclude_none=True)
    user = await service.update_user(user_id, updates)
    
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
    return user


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Toggle user active status - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    
    user = await service.toggle_user_active(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
    return user


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    data: PasswordReset,
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Reset user password - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    
    success = await service.reset_user_password(user_id, data.new_password)
    if not success:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
    return {"message": "تم إعادة تعيين كلمة المرور بنجاح"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Delete a user - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="لا يمكنك حذف حسابك الخاص")
    
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
    return {"message": "تم حذف المستخدم بنجاح"}


# ==================== System Endpoints ====================

@router.get("/stats")
async def get_system_stats(
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Get system statistics - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    return await service.get_system_stats()


@router.get("/system/info")
async def get_system_info(
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Get system information - System Admin only
    Uses: AdminService
    """
    require_system_admin(current_user)
    return await service.get_system_info()


@router.get("/system/database-stats")
async def get_database_stats(
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Get database statistics - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    return await service.get_database_stats()


# ==================== Audit Logs ====================

@router.get("/audit-logs")
async def get_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Get audit logs with filters - System Admin only
    Uses: AdminService -> AdminRepository
    """
    require_system_admin(current_user)
    return await service.get_audit_logs(
        entity_type=entity_type,
        action=action,
        user_id=user_id,
        days=days,
        page=page,
        page_size=page_size
    )

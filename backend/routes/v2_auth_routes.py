"""
Auth API v2 - Using Service Layer
V2 مصادقة API - باستخدام طبقة الخدمات

Architecture: Route -> Service -> Repository
All database logic is delegated to AuthService/UserRepository
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID

from app.services import AuthService
from app.dependencies import get_auth_service
from app.config import PaginationConfig

# Security
security = HTTPBearer()

# Pagination constants
DEFAULT_LIMIT = PaginationConfig.DEFAULT_PAGE_SIZE
MAX_LIMIT = PaginationConfig.MAX_PAGE_SIZE

# Create router
router = APIRouter(prefix="/api/v2/auth", tags=["V2 Auth"])


# ==================== PYDANTIC MODELS ====================

class UserRole:
    """User roles enum"""
    SYSTEM_ADMIN = "system_admin"
    SUPERVISOR = "supervisor"
    ENGINEER = "engineer"
    PROCUREMENT_MANAGER = "procurement_manager"
    PRINTER = "printer"
    DELIVERY_TRACKER = "delivery_tracker"
    GENERAL_MANAGER = "general_manager"
    QUANTITY_ENGINEER = "quantity_engineer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    assigned_projects: Optional[List[str]] = []
    assigned_engineers: Optional[List[str]] = []


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    assigned_projects: Optional[List[str]] = None
    assigned_engineers: Optional[List[str]] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class AdminResetPasswordRequest(BaseModel):
    new_password: str


class SetupAdminRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool = True
    supervisor_prefix: Optional[str] = None
    assigned_projects: Optional[List[str]] = []
    assigned_engineers: Optional[List[str]] = []
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UsersListResponse(BaseModel):
    """Paginated users response"""
    items: List[UserResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


# ==================== HELPER ====================

def user_to_response(user) -> UserResponse:
    """Convert User model to UserResponse"""
    # Handle JSON string fields
    import json
    
    assigned_projects = user.assigned_projects or []
    if isinstance(assigned_projects, str):
        try:
            assigned_projects = json.loads(assigned_projects)
        except:
            assigned_projects = []
    
    assigned_engineers = user.assigned_engineers or []
    if isinstance(assigned_engineers, str):
        try:
            assigned_engineers = json.loads(assigned_engineers)
        except:
            assigned_engineers = []
    
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        supervisor_prefix=getattr(user, 'supervisor_prefix', None),
        assigned_projects=assigned_projects,
        assigned_engineers=assigned_engineers
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user from token - Dependency"""
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز الدخول غير صالح أو منتهي"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="الحساب معطل"
        )
    
    return user


async def require_admin(current_user = Depends(get_current_user)):
    """Require admin role"""
    if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.PROCUREMENT_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك بهذه العملية"
        )
    return current_user


# ==================== PUBLIC ROUTES ====================

@router.get("/health")
async def health_check(auth_service: AuthService = Depends(get_auth_service)):
    """
    Health check for auth service
    Uses: AuthService -> UserRepository
    """
    count = await auth_service.count_users()
    return {
        "status": "healthy",
        "service": "auth_v2",
        "users_count": count
    }


@router.get("/setup/check")
async def check_setup_required(auth_service: AuthService = Depends(get_auth_service)):
    """
    Check if system needs initial admin setup
    Uses: AuthService -> UserRepository
    """
    admin_count = await auth_service.count_users_by_role(UserRole.SYSTEM_ADMIN)
    return {
        "setup_required": admin_count == 0
    }


@router.post("/setup/admin", response_model=TokenResponse)
async def setup_first_admin(
    data: SetupAdminRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Create first system admin (only works if no admin exists)
    Uses: AuthService -> UserRepository
    """
    # Check if admin already exists
    admin_count = await auth_service.count_users_by_role(UserRole.SYSTEM_ADMIN)
    if admin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="تم إعداد النظام مسبقاً"
        )
    
    # Create admin
    user = await auth_service.create_user(
        email=data.email,
        password=data.password,
        name=data.name,
        role=UserRole.SYSTEM_ADMIN
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="البريد الإلكتروني مستخدم"
        )
    
    # Generate token
    result = await auth_service.authenticate(data.email, data.password)
    if not result:
        raise HTTPException(status_code=500, detail="خطأ في إنشاء الجلسة")
    
    user, token = result
    return TokenResponse(
        access_token=token,
        user=user_to_response(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    User login
    Uses: AuthService -> UserRepository
    """
    result = await auth_service.authenticate(data.email, data.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة"
        )
    
    user, token = result
    return TokenResponse(
        access_token=token,
        user=user_to_response(user)
    )


# ==================== AUTHENTICATED ROUTES ====================

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """
    Get current user profile
    Uses: get_current_user dependency
    """
    return user_to_response(current_user)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change current user password
    Uses: AuthService -> UserRepository
    """
    success = await auth_service.change_password(
        UUID(str(current_user.id)),
        data.current_password,
        data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الحالية غير صحيحة"
        )
    
    return {"message": "تم تغيير كلمة المرور بنجاح"}


# ==================== ADMIN ROUTES ====================

@router.get("/users", response_model=UsersListResponse)
async def get_all_users(
    skip: int = 0,
    limit: int = DEFAULT_LIMIT,
    admin_user = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get all users (admin only)
    Uses: AuthService -> UserRepository
    """
    limit = min(limit, MAX_LIMIT)
    total = await auth_service.count_users()
    users = await auth_service.get_all_users(skip, limit)
    items = [user_to_response(u) for u in users]
    
    return UsersListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(items)) < total
    )


@router.get("/users/role/{role}", response_model=List[UserResponse])
async def get_users_by_role(
    role: str,
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get users by role
    Uses: AuthService -> UserRepository
    """
    users = await auth_service.get_users_by_role(role)
    return [user_to_response(u) for u in users]


@router.get("/users/engineers", response_model=List[UserResponse])
async def get_engineers(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get all engineers (convenience endpoint)
    Uses: AuthService -> UserRepository
    """
    users = await auth_service.get_users_by_role(UserRole.ENGINEER)
    return [user_to_response(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin_user = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get user by ID (admin only)
    Uses: AuthService -> UserRepository
    """
    user = await auth_service.get_user_by_id(UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    return user_to_response(user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    admin_user = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Create new user (admin only)
    Uses: AuthService -> UserRepository
    """
    user = await auth_service.create_user(
        email=data.email,
        password=data.password,
        name=data.name,
        role=data.role,
        assigned_projects=data.assigned_projects,
        assigned_engineers=data.assigned_engineers
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="البريد الإلكتروني مستخدم مسبقاً"
        )
    
    return user_to_response(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserUpdate,
    admin_user = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update user (admin only)
    Uses: AuthService -> UserRepository
    """
    update_data = data.model_dump(exclude_unset=True)
    user = await auth_service.update_user(UUID(user_id), update_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    return user_to_response(user)


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    data: AdminResetPasswordRequest,
    admin_user = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Reset user password (admin only)
    Uses: AuthService -> UserRepository
    """
    success = await auth_service.admin_reset_password(UUID(user_id), data.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    return {"message": "تم إعادة تعيين كلمة المرور بنجاح"}


@router.post("/users/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: str,
    admin_user = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Toggle user active status (admin only)
    Uses: AuthService -> UserRepository
    """
    # Prevent self-deactivation
    if str(admin_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يمكنك تعطيل حسابك"
        )
    
    user = await auth_service.toggle_user_active(UUID(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    return user_to_response(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_user = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Delete user (admin only, soft delete)
    Uses: AuthService -> UserRepository
    """
    # Prevent self-deletion
    if str(admin_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يمكنك حذف حسابك"
        )
    
    success = await auth_service.delete_user(UUID(user_id))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    return {"message": "تم حذف المستخدم بنجاح"}


# ==================== UTILITY ROUTES ====================

@router.get("/users/filters/list", response_model=List[UserResponse])
async def get_users_for_filters(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get users list for filter dropdowns
    Uses: AuthService -> UserRepository
    """
    users = await auth_service.get_all_users(0, 1000)
    return [
        UserResponse(
            id=str(u.id),
            name=u.name,
            email=u.email,
            role=u.role,
            is_active=u.is_active
        )
        for u in users if u.is_active
    ]

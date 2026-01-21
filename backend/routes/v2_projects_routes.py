"""
Projects API v2 - Clean Architecture + N+1 Fix + Real Pagination
API المشاريع V2 - معمارية نظيفة + حل N+1 + Pagination حقيقي

Architecture: Route -> Service -> Repository
- NO direct SQL in routes
- Batch queries to solve N+1
- Real pagination with total count
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from database import Project

# Import Services via DI
from app.services import ProjectService
from app.dependencies import get_project_service
from app.config import PaginationConfig, PaginatedResponse, to_iso_string
from routes.v2_auth_routes import get_current_user


router = APIRouter(prefix="/api/v2/projects", tags=["Projects V2"])

# Pagination
MAX_LIMIT = PaginationConfig.MAX_PAGE_SIZE
DEFAULT_LIMIT = PaginationConfig.DEFAULT_PAGE_SIZE


# ==================== Schemas ====================

class ProjectCreate(BaseModel):
    name: str
    code: str  # كود المشروع إلزامي وفريد
    owner_name: Optional[str] = None
    description: Optional[str] = ""
    location: Optional[str] = None
    total_area: float = 0
    floors_count: int = 0
    supervisor_id: Optional[str] = None  # المشرف المعين للمشروع
    engineer_id: Optional[str] = None  # المهندس المعين للمشروع


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    owner_name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    total_area: Optional[float] = None
    floors_count: Optional[int] = None
    supervisor_id: Optional[str] = None
    engineer_id: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    code: Optional[str]
    owner_name: Optional[str]
    description: Optional[str]
    location: Optional[str]
    total_area: float
    floors_count: int
    status: str
    supervisor_id: Optional[str] = None
    supervisor_name: Optional[str] = None
    engineer_id: Optional[str] = None
    engineer_name: Optional[str] = None
    created_by: Optional[str]
    created_by_name: Optional[str]
    created_at: Optional[str]
    total_requests: int = 0
    total_orders: int = 0
    total_budget: float = 0
    total_spent: float = 0

    class Config:
        from_attributes = True


class ProjectsListResponse(BaseModel):
    """Paginated projects response"""
    items: List[ProjectResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


# ==================== Helper ====================

def project_to_response(p: Project, stats: dict) -> dict:
    """Convert Project model to response dict"""
    return {
        "id": str(p.id),
        "name": p.name,
        "code": p.code,
        "owner_name": getattr(p, 'owner_name', None),
        "description": p.description,
        "location": getattr(p, 'location', None),
        "total_area": p.total_area or 0,
        "floors_count": p.floors_count or 0,
        "status": p.status or "active",
        "supervisor_id": getattr(p, 'supervisor_id', None),
        "supervisor_name": getattr(p, 'supervisor_name', None),
        "engineer_id": getattr(p, 'engineer_id', None),
        "engineer_name": getattr(p, 'engineer_name', None),
        "created_by": str(p.created_by) if hasattr(p, 'created_by') and p.created_by else None,
        "created_by_name": getattr(p, 'created_by_name', None),
        "created_at": to_iso_string(p.created_at),
        **stats
    }


# ==================== Routes ====================

@router.get("/", response_model=ProjectsListResponse)
async def get_all_projects(
    skip: int = Query(0, ge=0, description="عدد العناصر للتخطي"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="عدد العناصر"),
    status_filter: Optional[str] = Query(None, description="تصفية حسب الحالة"),
    project_service: ProjectService = Depends(get_project_service),
    current_user = Depends(get_current_user)
):
    """
    الحصول على جميع المشاريع مع الإحصائيات
    
    Features:
    - Real pagination with total count
    - N+1 fix: batch stats query
    - Filterable by status
    """
    limit = min(limit, MAX_LIMIT)
    
    # Get total count for pagination
    total = await project_service.count_projects(status_filter)
    
    # Get projects
    all_projects = await project_service.get_all_projects()
    
    # Filter by status if provided
    if status_filter:
        all_projects = [p for p in all_projects if p.status == status_filter]
    
    # Apply pagination
    paginated_projects = all_projects[skip:skip + limit]
    
    # Get stats in BATCH (solves N+1)
    project_ids = [str(p.id) for p in paginated_projects]
    stats_map = await project_service.get_projects_with_stats_batch(project_ids)
    
    # Build response
    items = [
        project_to_response(p, stats_map.get(str(p.id), {}))
        for p in paginated_projects
    ]
    
    return ProjectsListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(items)) < total
    )


@router.get("/active", response_model=List[ProjectResponse])
async def get_active_projects(
    project_service: ProjectService = Depends(get_project_service),
    current_user = Depends(get_current_user)
):
    """الحصول على المشاريع النشطة فقط"""
    projects = await project_service.get_active_projects()
    
    # Batch stats (N+1 fix)
    project_ids = [str(p.id) for p in projects]
    stats_map = await project_service.get_projects_with_stats_batch(project_ids)
    
    return [
        project_to_response(p, stats_map.get(str(p.id), {}))
        for p in projects
    ]


@router.get("/summary")
async def get_projects_summary(
    project_service: ProjectService = Depends(get_project_service),
    current_user = Depends(get_current_user)
):
    """الحصول على ملخص المشاريع"""
    return await project_service.get_projects_summary()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    current_user = Depends(get_current_user)
):
    """الحصول على مشروع محدد مع الإحصائيات"""
    project = await project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المشروع غير موجود"
        )
    
    stats = await project_service.get_project_full_stats(str(project.id))
    return project_to_response(project, stats)


@router.get("/{project_id}/dashboard")
async def get_project_dashboard(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    current_user = Depends(get_current_user)
):
    """الحصول على لوحة تحكم المشروع"""
    dashboard = await project_service.get_project_dashboard(project_id)
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المشروع غير موجود"
        )
    
    return dashboard


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    project_service: ProjectService = Depends(get_project_service),
    current_user = Depends(get_current_user)
):
    """إنشاء مشروع جديد"""
    user_id = current_user.get("id") if isinstance(current_user, dict) else str(current_user.id)
    user_name = current_user.get("name") if isinstance(current_user, dict) else current_user.name
    
    project = await project_service.create_project(
        name=project_data.name,
        code=project_data.code,
        owner_name=project_data.owner_name,
        description=project_data.description or "",
        location=project_data.location,
        total_area=project_data.total_area,
        floors_count=project_data.floors_count,
        created_by=user_id or "system",
        created_by_name=user_name or "النظام"
    )
    
    stats = await project_service.get_project_full_stats(str(project.id))
    return project_to_response(project, stats)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    project_service: ProjectService = Depends(get_project_service),
    current_user = Depends(get_current_user)
):
    """تحديث مشروع"""
    update_data = {k: v for k, v in project_data.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا توجد بيانات للتحديث"
        )
    
    project = await project_service.update_project(project_id, update_data)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المشروع غير موجود"
        )
    
    stats = await project_service.get_project_full_stats(str(project.id))
    return project_to_response(project, stats)


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    current_user = Depends(get_current_user)
):
    """حذف مشروع"""
    success = await project_service.delete_project(project_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المشروع غير موجود"
        )
    
    return {"message": "تم حذف المشروع بنجاح"}

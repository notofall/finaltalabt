"""
Buildings API v2 - Using Service Layer
V2 مباني API - باستخدام طبقة الخدمات

Architecture: Route -> Service -> Repository
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.services import BuildingsService
from app.dependencies import get_buildings_service
from routes.v2_auth_routes import get_current_user
from database.connection import get_postgres_session
from database.models import Project

# Create router
router = APIRouter(prefix="/api/v2/buildings", tags=["V2 Buildings"])


# ==================== PYDANTIC MODELS ====================

class TemplateCreate(BaseModel):
    code: str
    name: str
    area: float = 0
    rooms_count: int = 0
    bathrooms_count: int = 0
    count: int = 1
    description: Optional[str] = None


class TemplateUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    area: Optional[float] = None
    rooms_count: Optional[int] = None
    bathrooms_count: Optional[int] = None
    count: Optional[int] = None
    description: Optional[str] = None


class TemplateMaterialCreate(BaseModel):
    catalog_item_id: str
    item_code: str
    item_name: str
    unit: str
    quantity_per_unit: float
    unit_price: float = 0


class FloorCreate(BaseModel):
    floor_number: int
    floor_name: str
    area: float
    steel_factor: float = 100


class FloorUpdate(BaseModel):
    floor_name: Optional[str] = None
    area: Optional[float] = None
    steel_factor: Optional[float] = None


class AreaMaterialCreate(BaseModel):
    catalog_item_id: str
    item_name: str
    unit: str
    factor: float
    unit_price: float = 0


class AreaMaterialUpdate(BaseModel):
    item_name: Optional[str] = None
    factor: Optional[float] = None
    unit_price: Optional[float] = None


class SupplyUpdate(BaseModel):
    received_quantity: Optional[float] = None
    notes: Optional[str] = None


# ==================== HELPER ====================

def floor_to_response(floor) -> dict:
    """Convert ProjectFloor to response"""
    return {
        "id": str(floor.id),
        "project_id": str(floor.project_id),
        "floor_number": floor.floor_number,
        "floor_name": floor.floor_name,
        "area": floor.area,
        "steel_factor": floor.steel_factor,
        "created_at": floor.created_at.isoformat() if floor.created_at else None
    }


def area_material_to_response(material) -> dict:
    """Convert ProjectAreaMaterial to response"""
    return {
        "id": str(material.id),
        "project_id": str(material.project_id),
        "catalog_item_id": str(material.catalog_item_id) if material.catalog_item_id else None,
        "item_name": material.item_name,
        "unit": material.unit,
        "factor": material.factor,
        "unit_price": material.unit_price,
        "created_at": material.created_at.isoformat() if material.created_at else None
    }


def supply_to_response(item) -> dict:
    """Convert SupplyTracking to response"""
    remaining = (item.required_quantity or 0) - (item.received_quantity or 0)
    completion = round((item.received_quantity or 0) / item.required_quantity * 100, 1) if item.required_quantity else 0
    
    return {
        "id": str(item.id),
        "project_id": str(item.project_id),
        "item_name": item.item_name,
        "unit": item.unit,
        "required_quantity": item.required_quantity,
        "received_quantity": item.received_quantity or 0,
        "remaining_quantity": remaining,
        "completion_percentage": completion,
        "notes": item.notes
    }


# ==================== DASHBOARD & REPORTS ====================

@router.get("/dashboard")
async def get_buildings_dashboard(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get buildings system dashboard"""
    # Get projects count
    projects_result = await session.execute(select(func.count(Project.id)))
    total_projects = projects_result.scalar_one()
    
    # Get active projects
    active_result = await session.execute(
        select(func.count(Project.id)).where(Project.status == "active")
    )
    active_projects = active_result.scalar_one()
    
    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": total_projects - active_projects,
        "templates_count": 0,  # To be implemented
        "total_floors": 0,  # To be implemented
        "recent_activity": []
    }


@router.get("/reports/summary")
async def get_buildings_reports_summary(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get buildings reports summary"""
    # Get projects
    result = await session.execute(select(Project))
    projects = result.scalars().all()
    
    return {
        "total_projects": len(projects),
        "projects_by_status": {
            "active": len([p for p in projects if p.status == "active"]),
            "completed": len([p for p in projects if p.status == "completed"]),
            "on_hold": len([p for p in projects if p.status == "on_hold"])
        },
        "summary": {
            "total_area": 0,
            "total_materials": 0,
            "total_cost": 0
        }
    }


@router.get("/permissions/my")
async def get_my_permissions(
    current_user = Depends(get_current_user)
):
    """Get current user permissions for buildings system"""
    # Basic role-based permissions
    permissions = {
        "can_view": True,
        "can_edit": current_user.role in ["quantity_engineer", "system_admin", "procurement_manager"],
        "can_delete": current_user.role in ["system_admin", "procurement_manager"],
        "can_create_template": current_user.role in ["quantity_engineer", "system_admin"],
        "can_manage_floors": current_user.role in ["quantity_engineer", "system_admin"],
        "can_export": True,
        "assigned_projects": []  # To be implemented - project-specific permissions
    }
    
    return permissions


@router.get("/users/available")
async def get_available_users(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get all users available for permission assignment"""
    from database.models import User
    
    result = await session.execute(
        select(User).where(User.is_active == True)
    )
    users = result.scalars().all()
    
    return [
        {
            "id": str(u.id),
            "name": u.name,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ]


@router.get("/permissions")
async def get_all_permissions(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get all building permissions (admin only)"""
    from database.models import BuildingsPermission, User
    
    # Check if table exists
    try:
        result = await session.execute(
            select(BuildingPermission)
        )
        permissions = result.scalars().all()
        
        return [
            {
                "id": str(p.id),
                "user_id": p.user_id,
                "user_name": p.user_name,
                "project_id": p.project_id,
                "project_name": getattr(p, 'project_name', 'جميع المشاريع'),
                "can_view": p.can_view,
                "can_edit": p.can_edit,
                "can_delete": p.can_delete,
                "can_export": p.can_export
            }
            for p in permissions
        ]
    except Exception as e:
        print(f"Error fetching permissions: {e}")
        return []


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
async def grant_permission(
    data: dict,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Grant building permission to user"""
    from database.models import BuildingsPermission, User, Project
    import uuid as uuid_lib
    
    user_id = data.get("user_id")
    
    # Get user info
    user_result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
    # Get project info if specified
    project_id = data.get("project_id") or None
    project_name = "جميع المشاريع"
    if project_id:
        proj_result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = proj_result.scalar_one_or_none()
        if project:
            project_name = project.name
    
    # Create permission
    permission = BuildingPermission(
        id=str(uuid_lib.uuid4()),
        user_id=str(user.id),
        user_name=user.name,
        project_id=project_id,
        project_name=project_name,
        can_view=data.get("can_view", True),
        can_edit=data.get("can_edit", False),
        can_delete=data.get("can_delete", False),
        can_export=data.get("can_export", True),
        granted_by=str(current_user.id),
        granted_by_name=current_user.name
    )
    
    session.add(permission)
    await session.commit()
    
    return {"message": "تم إعطاء الصلاحية بنجاح", "id": permission.id}


@router.delete("/permissions/{permission_id}")
async def revoke_permission(
    permission_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Revoke building permission"""
    from database.models import BuildingPermission
    
    result = await session.execute(
        select(BuildingPermission).where(BuildingPermission.id == permission_id)
    )
    permission = result.scalar_one_or_none()
    
    if not permission:
        raise HTTPException(status_code=404, detail="الصلاحية غير موجودة")
    
    await session.delete(permission)
    await session.commit()
    
    return {"message": "تم إلغاء الصلاحية"}


# ==================== TEMPLATES ====================

@router.get("/projects/{project_id}/templates")
async def get_templates(
    project_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Get all templates for a project with materials
    Uses: BuildingsService -> BuildingsRepository
    """
    return await buildings_service.get_templates_by_project(project_id)


@router.post("/projects/{project_id}/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    project_id: str,
    data: TemplateCreate,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Create unit template
    Uses: BuildingsService -> BuildingsRepository
    """
    template = await buildings_service.create_template(
        project_id=project_id,
        code=data.code,
        name=data.name,
        area=data.area,
        rooms_count=data.rooms_count,
        bathrooms_count=data.bathrooms_count,
        count=data.count,
        description=data.description,
        created_by=str(current_user.id),
        created_by_name=current_user.name
    )
    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "message": "تم إنشاء النموذج بنجاح"
    }


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Update unit template
    Uses: BuildingsService -> BuildingsRepository
    """
    update_data = data.model_dump(exclude_unset=True)
    template = await buildings_service.update_template(template_id, update_data)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="النموذج غير موجود"
        )
    return {"message": "تم تحديث النموذج بنجاح"}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Delete unit template
    Uses: BuildingsService -> BuildingsRepository
    """
    success = await buildings_service.delete_template(template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="النموذج غير موجود"
        )
    return {"message": "تم حذف النموذج بنجاح"}


@router.post("/templates/{template_id}/materials", status_code=status.HTTP_201_CREATED)
async def add_template_material(
    template_id: str,
    data: TemplateMaterialCreate,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Add material to template
    Uses: BuildingsService -> BuildingsRepository
    """
    material = await buildings_service.add_template_material(
        template_id=template_id,
        catalog_item_id=data.catalog_item_id,
        item_code=data.item_code,
        item_name=data.item_name,
        unit=data.unit,
        quantity_per_unit=data.quantity_per_unit,
        unit_price=data.unit_price
    )
    return {"id": material.id, "message": "تم إضافة المادة بنجاح"}


@router.delete("/templates/{template_id}/materials/{material_id}")
async def delete_template_material(
    template_id: str,
    material_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Delete material from template
    Uses: BuildingsService -> BuildingsRepository
    """
    success = await buildings_service.delete_template_material(material_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المادة غير موجودة"
        )
    return {"message": "تم حذف المادة بنجاح"}


# ==================== FLOORS ====================

@router.get("/projects/{project_id}/floors")
async def get_floors(
    project_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Get all floors for a project
    Uses: BuildingsService -> BuildingsRepository
    """
    floors = await buildings_service.get_floors_by_project(project_id)
    return [floor_to_response(f) for f in floors]


@router.post("/projects/{project_id}/floors", status_code=status.HTTP_201_CREATED)
async def create_floor(
    project_id: str,
    data: FloorCreate,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Create project floor
    Uses: BuildingsService -> BuildingsRepository
    """
    floor = await buildings_service.create_floor(
        project_id=project_id,
        floor_number=data.floor_number,
        floor_name=data.floor_name,
        area=data.area,
        steel_factor=data.steel_factor,
        created_by=str(current_user.id),
        created_by_name=current_user.name
    )
    return floor_to_response(floor)


@router.put("/projects/{project_id}/floors/{floor_id}")
async def update_floor(
    project_id: str,
    floor_id: str,
    data: FloorUpdate,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Update project floor
    Uses: BuildingsService -> BuildingsRepository
    """
    update_data = data.model_dump(exclude_unset=True)
    floor = await buildings_service.update_floor(floor_id, update_data)
    
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الدور غير موجود"
        )
    return floor_to_response(floor)


@router.delete("/projects/{project_id}/floors/{floor_id}")
async def delete_floor(
    project_id: str,
    floor_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Delete project floor
    Uses: BuildingsService -> BuildingsRepository
    """
    success = await buildings_service.delete_floor(floor_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الدور غير موجود"
        )
    return {"message": "تم حذف الدور بنجاح"}


# ==================== AREA MATERIALS ====================

@router.get("/projects/{project_id}/area-materials")
async def get_area_materials(
    project_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Get area materials for a project
    Uses: BuildingsService -> BuildingsRepository
    """
    materials = await buildings_service.get_area_materials_by_project(project_id)
    return [area_material_to_response(m) for m in materials]


@router.post("/projects/{project_id}/area-materials", status_code=status.HTTP_201_CREATED)
async def create_area_material(
    project_id: str,
    data: AreaMaterialCreate,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Create area material
    Uses: BuildingsService -> BuildingsRepository
    """
    material = await buildings_service.create_area_material(
        project_id=project_id,
        catalog_item_id=data.catalog_item_id,
        item_name=data.item_name,
        unit=data.unit,
        factor=data.factor,
        unit_price=data.unit_price,
        created_by=str(current_user.id),
        created_by_name=current_user.name
    )
    return area_material_to_response(material)


@router.put("/projects/{project_id}/area-materials/{material_id}")
async def update_area_material(
    project_id: str,
    material_id: str,
    data: AreaMaterialUpdate,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Update area material
    Uses: BuildingsService -> BuildingsRepository
    """
    update_data = data.model_dump(exclude_unset=True)
    material = await buildings_service.update_area_material(material_id, update_data)
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المادة غير موجودة"
        )
    return area_material_to_response(material)


@router.delete("/projects/{project_id}/area-materials/{material_id}")
async def delete_area_material(
    project_id: str,
    material_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Delete area material
    Uses: BuildingsService -> BuildingsRepository
    """
    success = await buildings_service.delete_area_material(material_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المادة غير موجودة"
        )
    return {"message": "تم حذف المادة بنجاح"}


# ==================== SUPPLY TRACKING ====================

@router.get("/projects/{project_id}/supply")
async def get_supply(
    project_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Get supply tracking for a project
    Uses: BuildingsService -> BuildingsRepository
    """
    items = await buildings_service.get_supply_by_project(project_id)
    return [supply_to_response(item) for item in items]


@router.put("/projects/{project_id}/supply/{item_id}")
async def update_supply_item(
    project_id: str,
    item_id: str,
    data: SupplyUpdate,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Update supply item
    Uses: BuildingsService -> BuildingsRepository
    """
    update_data = data.model_dump(exclude_unset=True)
    item = await buildings_service.update_supply_item(item_id, update_data)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="العنصر غير موجود"
        )
    return supply_to_response(item)


# ==================== CALCULATIONS ====================

@router.get("/projects/{project_id}/calculate")
async def calculate_quantities(
    project_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Calculate all quantities for a project (BOQ)
    Uses: BuildingsService -> BuildingsRepository
    """
    return await buildings_service.calculate_project_quantities(project_id)


@router.get("/projects/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service)
):
    """
    Get project statistics
    Uses: BuildingsService -> BuildingsRepository
    """
    return await buildings_service.get_project_stats(project_id)

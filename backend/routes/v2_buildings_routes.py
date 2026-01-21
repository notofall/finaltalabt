"""
Buildings API v2 - Using Service Layer
V2 مباني API - باستخدام طبقة الخدمات

Architecture: Route -> Service -> Repository
"""
from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from uuid import uuid4

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
    # طريقة الحساب: factor (بالمعامل) أو direct (كمية مباشرة)
    calculation_method: str = "factor"
    factor: float = 0  # المعامل (للطريقة factor)
    direct_quantity: float = 0  # الكمية المباشرة (للطريقة direct)
    unit_price: float = 0
    # نوع الحساب: all_floors أو selected_floor
    calculation_type: str = "all_floors"
    selected_floor_id: Optional[str] = None  # ID الدور المحدد
    # للبلاط
    tile_width: float = 0  # عرض البلاطة بالسم
    tile_height: float = 0  # طول البلاطة بالسم
    waste_percentage: float = 0  # نسبة الهالك %
    notes: Optional[str] = None


class AreaMaterialUpdate(BaseModel):
    item_name: Optional[str] = None
    calculation_method: Optional[str] = None
    factor: Optional[float] = None
    direct_quantity: Optional[float] = None
    unit_price: Optional[float] = None
    calculation_type: Optional[str] = None
    selected_floor_id: Optional[str] = None
    tile_width: Optional[float] = None
    tile_height: Optional[float] = None
    waste_percentage: Optional[float] = None
    notes: Optional[str] = None


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
        "steel_factor": floor.steel_factor
    }


def area_material_to_response(material) -> dict:
    """Convert ProjectAreaMaterial to response"""
    return {
        "id": str(material.id),
        "project_id": str(material.project_id),
        "catalog_item_id": str(material.catalog_item_id) if material.catalog_item_id else None,
        "item_code": getattr(material, 'item_code', None),
        "item_name": material.item_name,
        "unit": material.unit,
        "calculation_method": getattr(material, 'calculation_method', 'factor') or 'factor',
        "factor": material.factor,
        "direct_quantity": getattr(material, 'direct_quantity', 0) or 0,
        "unit_price": material.unit_price,
        "calculation_type": getattr(material, 'calculation_type', 'all_floors') or 'all_floors',
        "selected_floor_id": getattr(material, 'selected_floor_id', None),
        "tile_width": getattr(material, 'tile_width', 0) or 0,
        "tile_height": getattr(material, 'tile_height', 0) or 0,
        "waste_percentage": getattr(material, 'waste_percentage', 0) or 0,
        "notes": getattr(material, 'notes', None),
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

@router.get("/projects")
async def get_buildings_projects(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get projects enabled for buildings system"""
    # Get only projects with is_building_project = True
    result = await session.execute(
        select(Project).where(
            Project.status == "active"
        ).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    
    # Filter projects that have is_building_project = True (default is True for new ones)
    building_projects = []
    for p in projects:
        # Check if is_building_project exists and is True (or default to True if field is new)
        is_building = getattr(p, 'is_building_project', True)
        if is_building is None or is_building:
            building_projects.append({
                "id": str(p.id),
                "name": p.name,
                "code": p.code,
                "owner_name": p.owner_name,
                "status": p.status,
                "total_area": p.total_area or 0,
                "floors_count": p.floors_count or 0
            })
    
    return building_projects


@router.delete("/projects/{project_id}")
async def delete_project_quantities(
    project_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Delete all quantities data for a project (BOQ, templates, floors, supply tracking)"""
    from database.models import UnitTemplate, UnitTemplateMaterial, ProjectFloor, ProjectAreaMaterial, SupplyTracking
    
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    # Get template IDs for this project to delete their materials
    templates_result = await session.execute(
        select(UnitTemplate.id).where(UnitTemplate.project_id == project_id)
    )
    template_ids = [t[0] for t in templates_result.fetchall()]
    
    deleted_counts = {
        "template_materials": 0,
        "templates": 0,
        "floors": 0,
        "area_materials": 0,
        "supply_tracking": 0
    }
    
    # Delete template materials first (foreign key constraint)
    if template_ids:
        del_materials = await session.execute(
            delete(UnitTemplateMaterial).where(UnitTemplateMaterial.template_id.in_(template_ids))
        )
        deleted_counts["template_materials"] = del_materials.rowcount
    
    # Delete unit templates
    del_templates = await session.execute(
        delete(UnitTemplate).where(UnitTemplate.project_id == project_id)
    )
    deleted_counts["templates"] = del_templates.rowcount
    
    # Delete project floors
    del_floors = await session.execute(
        delete(ProjectFloor).where(ProjectFloor.project_id == project_id)
    )
    deleted_counts["floors"] = del_floors.rowcount
    
    # Delete area materials
    del_area = await session.execute(
        delete(ProjectAreaMaterial).where(ProjectAreaMaterial.project_id == project_id)
    )
    deleted_counts["area_materials"] = del_area.rowcount
    
    # Delete supply tracking
    del_supply = await session.execute(
        delete(SupplyTracking).where(SupplyTracking.project_id == project_id)
    )
    deleted_counts["supply_tracking"] = del_supply.rowcount
    
    await session.commit()
    
    total_deleted = sum(deleted_counts.values())
    
    return {
        "message": f"تم حذف كميات المشروع بنجاح ({total_deleted} سجل)",
        "details": deleted_counts
    }


@router.post("/projects/{project_id}/enable")
async def enable_project_for_buildings(
    project_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Enable project for buildings system"""
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    # Set is_building_project to True
    project.is_building_project = True
    await session.commit()
    
    return {"message": "تم تفعيل المشروع في نظام الكميات بنجاح"}


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


@router.get("/reports/supply-details/{project_id}")
async def get_supply_details_report(
    project_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get detailed supply report for a project"""
    from database.models import SupplyTracking
    
    # Get project
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    # Get supply tracking items for this project
    supply_result = await session.execute(
        select(SupplyTracking).where(SupplyTracking.project_id == project_id)
    )
    supply_items = supply_result.scalars().all()
    
    # Categorize items
    completed_items = []
    in_progress_items = []
    not_started_items = []
    
    total_required = 0
    total_received = 0
    total_required_value = 0
    total_received_value = 0
    
    for item in supply_items:
        required_qty = item.required_quantity or 0
        received_qty = item.received_quantity or 0
        unit_price = item.unit_price if hasattr(item, 'unit_price') else 0
        remaining = required_qty - received_qty
        completion = round((received_qty / required_qty * 100), 1) if required_qty > 0 else 0
        
        total_required += required_qty
        total_received += received_qty
        total_required_value += required_qty * unit_price
        total_received_value += received_qty * unit_price
        
        item_data = {
            "id": str(item.id),
            "item_code": getattr(item, 'item_code', None),
            "item_name": item.item_name,
            "unit": item.unit,
            "required_quantity": required_qty,
            "received_quantity": received_qty,
            "remaining_quantity": remaining,
            "completion_percentage": completion,
            "remaining_value": remaining * unit_price
        }
        
        if completion >= 100:
            completed_items.append(item_data)
        elif received_qty > 0:
            in_progress_items.append(item_data)
        else:
            not_started_items.append(item_data)
    
    total_items = len(supply_items)
    overall_completion = round((total_received / total_required * 100), 1) if total_required > 0 else 0
    
    # Return report data structure matching frontend expectations
    return {
        "project_id": project_id,
        "project_name": project.name,
        "summary": {
            "total_items": total_items,
            "completed_count": len(completed_items),
            "in_progress_count": len(in_progress_items),
            "not_started_count": len(not_started_items),
            "overall_completion": overall_completion,
            "total_required": total_required,
            "total_received": total_received,
            "total_remaining": total_required - total_received,
            "total_required_value": total_required_value,
            "total_received_value": total_received_value
        },
        "completed_items": completed_items,
        "in_progress_items": in_progress_items,
        "not_started_items": not_started_items,
        "materials": [],
        "delivery_timeline": [],
        "suppliers": []
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
            select(BuildingsPermission)
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
    permission = BuildingsPermission(
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
    from database.models import BuildingsPermission
    
    result = await session.execute(
        select(BuildingsPermission).where(BuildingsPermission.id == permission_id)
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
    buildings_service: BuildingsService = Depends(get_buildings_service),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Create unit template
    Uses: BuildingsService -> BuildingsRepository
    """
    # Get project name
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    template = await buildings_service.create_template(
        project_id=project_id,
        project_name=project.name,
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
    Create area material with advanced options
    Uses: BuildingsService -> BuildingsRepository
    """
    material = await buildings_service.create_area_material(
        project_id=project_id,
        catalog_item_id=data.catalog_item_id,
        item_name=data.item_name,
        unit=data.unit,
        calculation_method=data.calculation_method,
        factor=data.factor,
        direct_quantity=data.direct_quantity,
        unit_price=data.unit_price,
        calculation_type=data.calculation_type,
        selected_floor_id=data.selected_floor_id,
        tile_width=data.tile_width,
        tile_height=data.tile_height,
        waste_percentage=data.waste_percentage,
        notes=data.notes,
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


@router.post("/projects/{project_id}/sync-supply")
async def sync_supply_tracking(
    project_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Sync supply tracking with calculated quantities
    Creates supply items for all calculated materials
    """
    from database.models import SupplyTracking, UnitTemplate, UnitTemplateMaterial, ProjectFloor, ProjectAreaMaterial
    
    # Get project
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    # Delete existing supply items for this project
    await session.execute(
        delete(SupplyTracking).where(SupplyTracking.project_id == project_id)
    )
    
    # Get templates with materials
    templates_result = await session.execute(
        select(UnitTemplate).where(UnitTemplate.project_id == project_id)
    )
    templates = templates_result.scalars().all()
    
    # Get floors for total area
    floors_result = await session.execute(
        select(ProjectFloor).where(ProjectFloor.project_id == project_id)
    )
    floors = floors_result.scalars().all()
    total_area = sum(f.area for f in floors)
    
    # Get area materials
    area_materials_result = await session.execute(
        select(ProjectAreaMaterial).where(ProjectAreaMaterial.project_id == project_id)
    )
    area_materials = area_materials_result.scalars().all()
    
    created_items = []
    
    # Create supply items from template materials
    for template in templates:
        materials_result = await session.execute(
            select(UnitTemplateMaterial).where(UnitTemplateMaterial.template_id == template.id)
        )
        materials = materials_result.scalars().all()
        
        for m in materials:
            quantity = m.quantity_per_unit * template.count
            supply_item = SupplyTracking(
                id=str(uuid4()),
                project_id=project_id,
                catalog_item_id=m.catalog_item_id,
                item_code=m.item_code,
                item_name=f"{m.item_name} ({template.name})",
                unit=m.unit,
                required_quantity=quantity,
                received_quantity=0,
                unit_price=m.unit_price,
                source="quantity",
                notes=f"من نموذج: {template.name}"
            )
            session.add(supply_item)
            created_items.append(supply_item)
    
    # Create supply items from area materials
    for m in area_materials:
        calc_method = getattr(m, 'calculation_method', 'factor') or 'factor'
        
        if calc_method == 'direct':
            base_quantity = getattr(m, 'direct_quantity', 0) or 0
            floor_area = 0
        else:
            # Get floor area
            if getattr(m, 'calculation_type', 'all_floors') == 'selected_floor' and getattr(m, 'selected_floor_id', None):
                floor_area = next((f.area for f in floors if str(f.id) == m.selected_floor_id), 0)
            else:
                floor_area = total_area
            base_quantity = floor_area * m.factor
        
        # Handle tile calculation
        tile_width = getattr(m, 'tile_width', 0) or 0
        tile_height = getattr(m, 'tile_height', 0) or 0
        if tile_width > 0 and tile_height > 0 and floor_area > 0:
            tile_area_m2 = (tile_width / 100) * (tile_height / 100)
            if tile_area_m2 > 0:
                base_quantity = floor_area / tile_area_m2
        
        # Apply waste percentage
        waste_pct = getattr(m, 'waste_percentage', 0) or 0
        quantity = base_quantity * (1 + waste_pct / 100)
        
        supply_item = SupplyTracking(
            id=str(uuid4()),
            project_id=project_id,
            catalog_item_id=m.catalog_item_id,
            item_code=getattr(m, 'item_code', None),
            item_name=m.item_name,
            unit=m.unit,
            required_quantity=round(quantity, 2),
            received_quantity=0,
            unit_price=m.unit_price,
            source="area",
            notes="مواد المساحة"
        )
        session.add(supply_item)
        created_items.append(supply_item)
    
    await session.commit()
    
    return {
        "message": f"تم مزامنة التوريد بنجاح ({len(created_items)} عنصر)",
        "items_count": len(created_items)
    }


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


# ==================== EXPORT / IMPORT ====================

@router.get("/projects/{project_id}/export/boq-excel")
async def export_boq_excel(
    project_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Export BOQ to Excel file"""
    from fastapi.responses import StreamingResponse
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from io import BytesIO
    from database.models import UnitTemplate, UnitTemplateMaterial, ProjectFloor, ProjectAreaMaterial
    
    # Get project
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    # Calculate quantities
    calc_data = await buildings_service.calculate_project_quantities(project_id)
    
    # Create workbook
    wb = Workbook()
    
    # Styles
    header_font = Font(bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center')
    right_align = Alignment(horizontal='right', vertical='center')
    
    # === Sheet 1: Summary ===
    ws = wb.active
    ws.title = "ملخص"
    ws.sheet_view.rightToLeft = True
    
    ws['A1'] = f"جدول الكميات - {project.name}"
    ws['A1'].font = Font(bold=True, size=16)
    ws.merge_cells('A1:E1')
    
    ws['A3'] = "المشروع:"
    ws['B3'] = project.name
    ws['A4'] = "المالك:"
    ws['B4'] = project.owner_name or ""
    ws['A5'] = "إجمالي المساحة:"
    ws['B5'] = f"{calc_data['total_area']} م²"
    ws['A6'] = "إجمالي الوحدات:"
    ws['B6'] = calc_data['total_units']
    ws['A7'] = "إجمالي الحديد:"
    ws['B7'] = f"{calc_data['steel_calculation']['total_steel_tons']} طن"
    ws['A8'] = "إجمالي التكلفة:"
    ws['B8'] = f"{calc_data['total_materials_cost']:,.2f} ر.س"
    
    # === Sheet 2: Steel by Floor ===
    ws2 = wb.create_sheet("الحديد حسب الدور")
    ws2.sheet_view.rightToLeft = True
    
    headers = ["الدور", "المساحة (م²)", "المعامل (كجم/م²)", "الحديد (طن)"]
    for col, header in enumerate(headers, 1):
        cell = ws2.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = center_align
    
    for row, floor in enumerate(calc_data['steel_calculation']['floors'], 2):
        ws2.cell(row=row, column=1, value=floor['floor_name']).border = border
        ws2.cell(row=row, column=2, value=floor['area']).border = border
        ws2.cell(row=row, column=3, value=floor['steel_factor']).border = border
        ws2.cell(row=row, column=4, value=floor['steel_tons']).border = border
    
    # === Sheet 3: Unit Materials ===
    ws3 = wb.create_sheet("مواد الوحدات")
    ws3.sheet_view.rightToLeft = True
    
    headers = ["الكود", "المادة", "الوحدة", "الكمية", "السعر", "الإجمالي"]
    for col, header in enumerate(headers, 1):
        cell = ws3.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = center_align
    
    for row, mat in enumerate(calc_data['materials'], 2):
        ws3.cell(row=row, column=1, value=mat.get('item_code', '')).border = border
        ws3.cell(row=row, column=2, value=mat['item_name']).border = border
        ws3.cell(row=row, column=3, value=mat['unit']).border = border
        ws3.cell(row=row, column=4, value=mat['quantity']).border = border
        ws3.cell(row=row, column=5, value=mat['unit_price']).border = border
        ws3.cell(row=row, column=6, value=mat['total_price']).border = border
    
    # Total row
    total_row = len(calc_data['materials']) + 2
    ws3.cell(row=total_row, column=5, value="الإجمالي:").font = Font(bold=True)
    ws3.cell(row=total_row, column=6, value=calc_data['total_unit_materials_cost']).font = Font(bold=True)
    
    # === Sheet 4: Area Materials ===
    ws4 = wb.create_sheet("مواد المساحة")
    ws4.sheet_view.rightToLeft = True
    
    headers = ["المادة", "الوحدة", "المعامل", "الدور", "الهالك%", "الكمية", "السعر", "الإجمالي"]
    for col, header in enumerate(headers, 1):
        cell = ws4.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = center_align
    
    for row, mat in enumerate(calc_data['area_materials'], 2):
        ws4.cell(row=row, column=1, value=mat['item_name']).border = border
        ws4.cell(row=row, column=2, value=mat['unit']).border = border
        ws4.cell(row=row, column=3, value=mat.get('factor', 0)).border = border
        ws4.cell(row=row, column=4, value=mat.get('floor_name', 'جميع الأدوار')).border = border
        ws4.cell(row=row, column=5, value=mat.get('waste_percentage', 0)).border = border
        ws4.cell(row=row, column=6, value=mat['quantity']).border = border
        ws4.cell(row=row, column=7, value=mat['unit_price']).border = border
        ws4.cell(row=row, column=8, value=mat['total_price']).border = border
    
    # Total row
    total_row = len(calc_data['area_materials']) + 2
    ws4.cell(row=total_row, column=7, value="الإجمالي:").font = Font(bold=True)
    ws4.cell(row=total_row, column=8, value=calc_data['total_area_materials_cost']).font = Font(bold=True)
    
    # Adjust column widths
    for ws in [wb.active, ws2, ws3, ws4]:
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            ws.column_dimensions[column].width = max_length + 5
    
    # Save to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=BOQ_{project.name}.xlsx"}
    )


@router.get("/projects/{project_id}/export/boq-pdf")
async def export_boq_pdf(
    project_id: str,
    current_user = Depends(get_current_user),
    buildings_service: BuildingsService = Depends(get_buildings_service),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Export BOQ to PDF file"""
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from io import BytesIO
    import os
    
    # Get project
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    # Calculate quantities
    calc_data = await buildings_service.calculate_project_quantities(project_id)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('Title', fontSize=18, alignment=1, spaceAfter=20)
    elements.append(Paragraph(f"BOQ - {project.name}", title_style))
    elements.append(Spacer(1, 20))
    
    # Summary table
    summary_data = [
        ["Project", project.name],
        ["Owner", project.owner_name or ""],
        ["Total Area", f"{calc_data['total_area']} m²"],
        ["Total Units", str(calc_data['total_units'])],
        ["Total Steel", f"{calc_data['steel_calculation']['total_steel_tons']} ton"],
        ["Total Cost", f"{calc_data['total_materials_cost']:,.2f} SAR"],
    ]
    
    summary_table = Table(summary_data, colWidths=[150, 300])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.18, 0.49, 0.2)),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Steel table
    elements.append(Paragraph("Steel by Floor", styles['Heading2']))
    steel_data = [["Floor", "Area (m²)", "Factor (kg/m²)", "Steel (ton)"]]
    for floor in calc_data['steel_calculation']['floors']:
        steel_data.append([floor['floor_name'], floor['area'], floor['steel_factor'], floor['steel_tons']])
    steel_data.append(["Total", calc_data['total_area'], "", calc_data['steel_calculation']['total_steel_tons']])
    
    steel_table = Table(steel_data, colWidths=[150, 100, 100, 100])
    steel_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.18, 0.49, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(steel_table)
    elements.append(Spacer(1, 30))
    
    # Unit Materials table
    if calc_data['materials']:
        elements.append(Paragraph("Unit Materials", styles['Heading2']))
        mat_data = [["Code", "Material", "Unit", "Qty", "Price", "Total"]]
        for mat in calc_data['materials']:
            mat_data.append([
                mat.get('item_code', ''),
                mat['item_name'][:30],
                mat['unit'],
                mat['quantity'],
                mat['unit_price'],
                mat['total_price']
            ])
        mat_data.append(["", "", "", "", "Total:", f"{calc_data['total_unit_materials_cost']:,.2f}"])
        
        mat_table = Table(mat_data, colWidths=[60, 150, 50, 60, 60, 80])
        mat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.18, 0.49, 0.2)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
        elements.append(mat_table)
        elements.append(Spacer(1, 30))
    
    # Area Materials table
    if calc_data['area_materials']:
        elements.append(Paragraph("Area Materials", styles['Heading2']))
        area_data = [["Material", "Unit", "Factor", "Waste%", "Qty", "Price", "Total"]]
        for mat in calc_data['area_materials']:
            area_data.append([
                mat['item_name'][:25],
                mat['unit'],
                mat.get('factor', 0),
                mat.get('waste_percentage', 0),
                mat['quantity'],
                mat['unit_price'],
                mat['total_price']
            ])
        area_data.append(["", "", "", "", "", "Total:", f"{calc_data['total_area_materials_cost']:,.2f}"])
        
        area_table = Table(area_data, colWidths=[120, 40, 50, 50, 60, 60, 80])
        area_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.18, 0.49, 0.2)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
        elements.append(area_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=BOQ_{project.name}.pdf"}
    )


@router.get("/projects/{project_id}/export/floors-excel")
async def export_floors_excel(
    project_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Export floors to Excel file"""
    from fastapi.responses import StreamingResponse
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from io import BytesIO
    from database.models import ProjectFloor
    
    # Get project
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    # Get floors
    floors_result = await session.execute(
        select(ProjectFloor).where(ProjectFloor.project_id == project_id).order_by(ProjectFloor.floor_number)
    )
    floors = floors_result.scalars().all()
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "الأدوار"
    ws.sheet_view.rightToLeft = True
    
    # Styles
    header_font = Font(bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    
    # Headers
    headers = ["رقم الدور", "اسم الدور", "المساحة (م²)", "معامل التسليح (كجم/م²)"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
    
    # Data
    for row, floor in enumerate(floors, 2):
        ws.cell(row=row, column=1, value=floor.floor_number).border = border
        ws.cell(row=row, column=2, value=floor.floor_name).border = border
        ws.cell(row=row, column=3, value=floor.area).border = border
        ws.cell(row=row, column=4, value=floor.steel_factor).border = border
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 25
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Floors_{project.name}.xlsx"}
    )


@router.post("/projects/{project_id}/import/floors")
async def import_floors_excel(
    project_id: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Import floors from Excel file"""
    from openpyxl import load_workbook
    from io import BytesIO
    from database.models import ProjectFloor
    
    # Get project
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    # Read Excel file
    contents = await file.read()
    wb = load_workbook(BytesIO(contents))
    ws = wb.active
    
    imported_count = 0
    errors = []
    
    # Skip header row
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0] and not row[1]:
            continue
        
        try:
            floor_number = int(row[0]) if row[0] else 0
            floor_name = str(row[1]) if row[1] else f"الدور {floor_number}"
            area = float(row[2]) if row[2] else 0
            steel_factor = float(row[3]) if row[3] else 120
            
            floor = ProjectFloor(
                id=str(uuid4()),
                project_id=project_id,
                floor_number=floor_number,
                floor_name=floor_name,
                area=area,
                steel_factor=steel_factor
            )
            session.add(floor)
            imported_count += 1
        except Exception as e:
            errors.append(f"Row {row}: {str(e)}")
    
    await session.commit()
    
    return {
        "message": f"تم استيراد {imported_count} دور بنجاح",
        "imported_count": imported_count,
        "errors": errors if errors else None
    }


@router.get("/export/project-template")
async def download_project_template(current_user = Depends(get_current_user)):
    """Download project import template (Excel)"""
    from fastapi.responses import StreamingResponse
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side
    from io import BytesIO
    
    wb = Workbook()
    
    # Floors sheet
    ws1 = wb.active
    ws1.title = "الأدوار"
    ws1.sheet_view.rightToLeft = True
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    
    headers = ["رقم الدور", "اسم الدور", "المساحة (م²)", "معامل التسليح (كجم/م²)"]
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
    
    # Sample data
    sample_floors = [
        [0, "اللبشة", 430, 120],
        [1, "دور المواقف", 800, 120],
        [2, "الدور الأول", 300, 120],
    ]
    for row, data in enumerate(sample_floors, 2):
        for col, value in enumerate(data, 1):
            ws1.cell(row=row, column=col, value=value)
    
    ws1.column_dimensions['A'].width = 12
    ws1.column_dimensions['B'].width = 20
    ws1.column_dimensions['C'].width = 15
    ws1.column_dimensions['D'].width = 25
    
    # Templates sheet
    ws2 = wb.create_sheet("النماذج")
    ws2.sheet_view.rightToLeft = True
    
    headers = ["الكود", "الاسم", "عدد الوحدات", "المساحة (م²)", "الغرف", "الحمامات"]
    for col, header in enumerate(headers, 1):
        cell = ws2.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
    
    sample_templates = [
        ["A", "شقة أمامية", 4, 200, 4, 3],
        ["B", "شقة خلفية", 3, 150, 3, 2],
    ]
    for row, data in enumerate(sample_templates, 2):
        for col, value in enumerate(data, 1):
            ws2.cell(row=row, column=col, value=value)
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=project_template.xlsx"}
    )

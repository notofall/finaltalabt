"""
V2 Quantity Routes - Quantity Engineer dashboard with proper layering
Uses: QuantityService -> QuantityRepository
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import io
import csv

from database import get_postgres_session
from app.repositories.quantity_repository import QuantityRepository
from app.services.quantity_service import QuantityService
from routes.v2_auth_routes import get_current_user, UserRole


router = APIRouter(
    prefix="/api/v2/quantity",
    tags=["V2 Quantity Engineer"]
)


# ==================== Dependencies ====================

def get_quantity_service(session: AsyncSession = Depends(get_postgres_session)) -> QuantityService:
    """Get quantity service with repository"""
    repository = QuantityRepository(session)
    return QuantityService(repository)


def require_quantity_access(user):
    """Check if user has quantity engineer access"""
    allowed_roles = [
        UserRole.QUANTITY_ENGINEER,
        UserRole.PROCUREMENT_MANAGER,
        UserRole.SYSTEM_ADMIN
    ]
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك بهذا الإجراء"
        )


# ==================== Pydantic Models ====================

class PlannedQuantityCreate(BaseModel):
    catalog_item_id: str
    project_id: str
    planned_quantity: float
    expected_order_date: Optional[str] = None
    priority: int = 2
    notes: Optional[str] = None
    category_id: Optional[str] = None


class PlannedQuantityUpdate(BaseModel):
    planned_quantity: Optional[float] = None
    expected_order_date: Optional[str] = None
    priority: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[str] = None


# ==================== Dashboard Stats ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Get quantity engineer dashboard statistics
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    return await service.get_dashboard_stats()


# ==================== Catalog Items ====================

@router.get("/catalog-items")
async def get_catalog_items(
    search: Optional[str] = None,
    supplier_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Get catalog items for planning
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    return await service.get_catalog_items(
        search=search,
        supplier_id=supplier_id,
        page=page,
        page_size=page_size
    )


# ==================== Budget Categories ====================

@router.get("/budget-categories")
async def get_all_budget_categories(
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Get all budget categories
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    return await service.get_all_budget_categories()


@router.get("/budget-categories/{project_id}")
async def get_budget_categories_by_project(
    project_id: str,
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Get budget categories for a specific project
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    return await service.get_budget_categories_by_project(project_id)


# ==================== Planned Quantities CRUD ====================

@router.get("/planned")
async def get_planned_quantities(
    project_id: Optional[str] = None,
    catalog_item_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Get planned quantities with filters and pagination
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    return await service.get_planned_quantities(
        project_id=project_id,
        catalog_item_id=catalog_item_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size
    )


@router.post("/planned")
async def create_planned_quantity(
    data: PlannedQuantityCreate,
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Create a new planned quantity
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    
    try:
        result = await service.create_planned_quantity(
            catalog_item_id=data.catalog_item_id,
            project_id=data.project_id,
            planned_quantity=data.planned_quantity,
            user_id=current_user.id,
            user_name=current_user.name,
            expected_order_date=data.expected_order_date,
            priority=data.priority,
            notes=data.notes,
            category_id=data.category_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/planned/{quantity_id}")
async def update_planned_quantity(
    quantity_id: str,
    data: PlannedQuantityUpdate,
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Update a planned quantity
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    
    updates = data.dict(exclude_none=True)
    result = await service.update_planned_quantity(quantity_id, updates)
    
    if not result:
        raise HTTPException(status_code=404, detail="الكمية المخططة غير موجودة")
    
    return result


@router.delete("/planned/{quantity_id}")
async def delete_planned_quantity(
    quantity_id: str,
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Delete a planned quantity
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    
    deleted = await service.delete_planned_quantity(quantity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="الكمية المخططة غير موجودة")
    
    return {"message": "تم حذف الكمية المخططة بنجاح"}


# ==================== Reports ====================

@router.get("/reports/summary")
async def get_summary_report(
    project_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Get summary report for planned quantities
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    return await service.get_summary_report(project_id)


@router.get("/alerts")
async def get_alerts(
    days_threshold: int = Query(7, ge=1, le=90),
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Get alerts for items needing attention
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    return await service.get_alerts(days_threshold)


# ==================== Export/Import ====================

@router.get("/planned/export")
async def export_planned_quantities(
    project_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Export planned quantities to CSV
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    
    result = await service.get_planned_quantities(
        project_id=project_id,
        page=1,
        page_size=10000
    )
    
    items = result.get("items", [])
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "كود الصنف", "اسم الصنف", "الوحدة", "الكمية المخططة", 
        "الكمية المطلوبة", "الكمية المتبقية", "المشروع", 
        "تاريخ الطلب المتوقع", "الحالة", "الأولوية"
    ])
    
    # Data
    for item in items:
        writer.writerow([
            item.get("item_code", ""),
            item.get("item_name", ""),
            item.get("unit", ""),
            item.get("planned_quantity", 0),
            item.get("ordered_quantity", 0),
            item.get("remaining_quantity", 0),
            item.get("project_name", ""),
            item.get("expected_order_date", ""),
            item.get("status", ""),
            item.get("priority", "")
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=planned_quantities.csv"}
    )


@router.get("/planned/template")
async def get_import_template(
    current_user = Depends(get_current_user)
):
    """
    Get CSV template for importing planned quantities
    """
    require_quantity_access(current_user)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "catalog_item_id", "project_id", "planned_quantity", 
        "expected_order_date", "priority", "notes"
    ])
    
    # Example row
    writer.writerow([
        "item-uuid-here", "project-uuid-here", "100", 
        "2026-02-01", "2", "ملاحظات اختيارية"
    ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=import_template.csv"}
    )


@router.get("/reports/export")
async def export_reports(
    project_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: QuantityService = Depends(get_quantity_service)
):
    """
    Export reports to CSV
    Uses: QuantityService -> QuantityRepository
    """
    require_quantity_access(current_user)
    
    report = await service.get_summary_report(project_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["تقرير ملخص الكميات المخططة"])
    writer.writerow([])
    writer.writerow(["إجمالي الأصناف", report.get("total_items", 0)])
    writer.writerow(["إجمالي الكمية المخططة", report.get("total_planned_quantity", 0)])
    writer.writerow(["إجمالي الكمية المطلوبة", report.get("total_ordered_quantity", 0)])
    writer.writerow(["إجمالي الكمية المتبقية", report.get("total_remaining_quantity", 0)])
    writer.writerow([])
    writer.writerow(["توزيع الحالات:"])
    
    for status, count in report.get("status_breakdown", {}).items():
        writer.writerow([status, count])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=quantity_report.csv"}
    )

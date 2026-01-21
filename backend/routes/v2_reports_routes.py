"""
V2 Reports Routes - Dashboard and reports APIs with proper layering
Uses: ReportsService -> ReportsRepository

Architecture: Route -> Service -> Repository
- Routes: HTTP handling, auth, response formatting
- Services: Business logic
- Repositories: Data access
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import io
import csv

from database import get_postgres_session
from app.repositories.reports_repository import ReportsRepository
from app.services.reports_service import ReportsService
from routes.v2_auth_routes import get_current_user, UserRole


router = APIRouter(
    prefix="/api/v2/reports",
    tags=["V2 Reports"]
)


# ==================== Dependencies ====================

def get_reports_service(
    session: AsyncSession = Depends(get_postgres_session)
) -> ReportsService:
    """Get reports service with repository"""
    repository = ReportsRepository(session)
    return ReportsService(repository)


def require_manager_access(user):
    """Check if user has manager access"""
    allowed_roles = [
        UserRole.PROCUREMENT_MANAGER,
        UserRole.GENERAL_MANAGER,
        UserRole.SYSTEM_ADMIN
    ]
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="غير مصرح لك بهذا الإجراء"
        )


# ==================== Dashboard Stats ====================

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user = Depends(get_current_user),
    service: ReportsService = Depends(get_reports_service)
):
    """
    Get main dashboard statistics
    Uses: ReportsService -> ReportsRepository
    """
    require_manager_access(current_user)
    return await service.get_dashboard_stats()


# ==================== Budget Reports ====================

@router.get("/budget")
async def get_budget_report(
    project_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: ReportsService = Depends(get_reports_service)
):
    """
    Get budget report
    Uses: ReportsService -> ReportsRepository
    """
    require_manager_access(current_user)
    return await service.get_budget_report(project_id)


@router.get("/budget/export")
async def export_budget_report(
    project_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: ReportsService = Depends(get_reports_service)
):
    """
    Export budget report to CSV
    Uses: ReportsService -> ReportsRepository
    """
    require_manager_access(current_user)
    
    data = await service.get_budget_export_data(project_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "الكود", "الاسم", "الميزانية المقدرة", 
        "المصروف", "المتبقي", "النسبة المستخدمة %"
    ])
    
    for item in data:
        writer.writerow([
            item["code"], item["name"], item["estimated"],
            item["spent"], item["remaining"], item["percentage"]
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=budget_report.csv"}
    )


# ==================== Cost Savings Report ====================

@router.get("/cost-savings")
async def get_cost_savings_report(
    current_user = Depends(get_current_user),
    service: ReportsService = Depends(get_reports_service)
):
    """
    Get cost savings report comparing prices
    Uses: ReportsService -> ReportsRepository
    """
    require_manager_access(current_user)
    return await service.get_cost_savings_report()


# ==================== Project Report ====================

@router.get("/project/{project_id}")
async def get_project_report(
    project_id: str,
    current_user = Depends(get_current_user),
    service: ReportsService = Depends(get_reports_service)
):
    """
    Get detailed project report
    Uses: ReportsService -> ReportsRepository
    """
    require_manager_access(current_user)
    
    report = await service.get_project_report(project_id)
    if not report:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    return report


# ==================== Advanced Reports ====================

@router.get("/advanced/summary")
async def get_advanced_summary_report(
    project_id: Optional[str] = None,
    engineer_id: Optional[str] = None,
    supervisor_id: Optional[str] = None,
    supplier_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: ReportsService = Depends(get_reports_service)
):
    """
    Get advanced summary report with filters
    Uses: ReportsService -> ReportsRepository
    """
    require_manager_access(current_user)
    return await service.get_advanced_summary(
        project_id=project_id,
        supplier_id=supplier_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/advanced/approval-analytics")
async def get_approval_analytics(
    project_id: Optional[str] = None,
    engineer_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: ReportsService = Depends(get_reports_service)
):
    """
    Get approval analytics report
    Uses: ReportsService -> ReportsRepository
    """
    require_manager_access(current_user)
    return await service.get_approval_analytics(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/advanced/supplier-performance")
async def get_supplier_performance(
    supplier_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: ReportsService = Depends(get_reports_service)
):
    """
    Get supplier performance report
    Uses: ReportsService -> ReportsRepository
    """
    require_manager_access(current_user)
    return await service.get_supplier_performance(
        supplier_id=supplier_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/advanced/price-variance")
async def get_price_variance(
    item_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: ReportsService = Depends(get_reports_service)
):
    """
    Get price variance report
    Uses: ReportsService -> ReportsRepository
    """
    require_manager_access(current_user)
    return await service.get_price_variance(item_name=item_name)

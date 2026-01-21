"""
Delivery API v2 - Using Services Layer
API التسليم باستخدام طبقة الخدمات
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.services import DeliveryService
from app.dependencies import get_delivery_service
from routes.v2_auth_routes import get_current_user


router = APIRouter(prefix="/api/v2/delivery", tags=["Delivery V2"])


# ==================== Schemas ====================

class DeliveryItemConfirm(BaseModel):
    item_id: str
    quantity_delivered: float


class DeliveryConfirmRequest(BaseModel):
    items: List[DeliveryItemConfirm]


class DeliveryStatsResponse(BaseModel):
    total_pending: int
    shipped: int
    partially_delivered: int
    awaiting_shipment: int


class SupplyStatusResponse(BaseModel):
    total_items: int
    completed_count: int
    in_progress_count: int
    not_started_count: int
    total_required: float
    total_received: float
    completion_percentage: float


# ==================== Routes ====================

@router.get("/stats", response_model=DeliveryStatsResponse)
async def get_delivery_stats(
    delivery_service: DeliveryService = Depends(get_delivery_service),
    current_user: dict = Depends(get_current_user)
):
    """الحصول على إحصائيات التسليم"""
    stats = await delivery_service.get_delivery_stats()
    return DeliveryStatsResponse(**stats)


@router.get("/pending")
async def get_pending_deliveries(
    delivery_service: DeliveryService = Depends(get_delivery_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """الحصول على أوامر الشراء بانتظار التسليم"""
    from database import Project, Supplier, MaterialRequest
    from sqlalchemy import select
    
    orders = await delivery_service.get_pending_deliveries()
    result = []
    
    for o in orders:
        # Get project name
        project_name = None
        if o.project_id:
            project_result = await session.execute(
                select(Project.name).where(Project.id == o.project_id)
            )
            project_name = project_result.scalar_one_or_none()
        
        # Get supplier name
        supplier_name = None
        if o.supplier_id:
            supplier_result = await session.execute(
                select(Supplier.name).where(Supplier.id == o.supplier_id)
            )
            supplier_name = supplier_result.scalar_one_or_none()
        
        # Get request number
        request_number = None
        if o.request_id:
            request_result = await session.execute(
                select(MaterialRequest.request_number).where(MaterialRequest.id == o.request_id)
            )
            request_number = request_result.scalar_one_or_none()
        
        result.append({
            "id": str(o.id),
            "order_number": o.order_number,
            "request_number": request_number,
            "project_id": o.project_id,
            "project_name": project_name,
            "supplier_id": o.supplier_id,
            "supplier_name": supplier_name,
            "status": o.status,
            "total_amount": o.total_amount or 0,
            "items_count": len(o.items) if hasattr(o, 'items') and o.items else 0,
            "items": [
                {
                    "id": str(item.id) if hasattr(item, 'id') else None,
                    "name": item.name if hasattr(item, 'name') else item.get('name', ''),
                    "quantity": item.quantity if hasattr(item, 'quantity') else item.get('quantity', 0),
                    "unit": item.unit if hasattr(item, 'unit') else item.get('unit', 'قطعة'),
                    "unit_price": item.unit_price if hasattr(item, 'unit_price') else item.get('unit_price', 0),
                    "delivered_quantity": item.delivered_quantity if hasattr(item, 'delivered_quantity') else item.get('delivered_quantity', 0)
                }
                for item in (o.items if hasattr(o, 'items') and o.items else [])
            ],
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "supplier_receipt_number": o.supplier_receipt_number if hasattr(o, 'supplier_receipt_number') else None,
            "delivery_notes": o.delivery_notes if hasattr(o, 'delivery_notes') else None
        })
    
    return result


@router.post("/{order_id}/ship")
async def mark_as_shipped(
    order_id: UUID,
    tracking_number: str = "",
    delivery_service: DeliveryService = Depends(get_delivery_service),
    current_user: dict = Depends(get_current_user)
):
    """تحديث حالة الشحن"""
    # التحقق من الصلاحيات
    allowed_roles = ["system_admin", "procurement_manager", "delivery_tracker"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية تحديث حالة الشحن"
        )
    
    order = await delivery_service.mark_as_shipped(
        order_id,
        current_user.get("name", "Unknown"),
        tracking_number
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="أمر الشراء غير موجود"
        )
    return {"message": "تم تحديث حالة الشحن", "order_id": str(order_id)}


@router.post("/{order_id}/confirm-receipt")
async def confirm_receipt(
    order_id: UUID,
    request: DeliveryConfirmRequest,
    delivery_service: DeliveryService = Depends(get_delivery_service),
    current_user: dict = Depends(get_current_user)
):
    """
    تأكيد استلام العناصر
    يقوم تلقائياً بتحديث تتبع التوريد
    """
    # التحقق من الصلاحيات
    allowed_roles = ["system_admin", "procurement_manager", "delivery_tracker"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية تأكيد الاستلام"
        )
    
    # تحويل البيانات
    items = [
        {"item_id": item.item_id, "quantity_delivered": item.quantity_delivered}
        for item in request.items
    ]
    
    result = await delivery_service.confirm_receipt(
        order_id,
        items,
        current_user.get("name", "Unknown")
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "حدث خطأ")
        )
    
    return {
        "message": "تم تأكيد الاستلام بنجاح",
        "status": result.get("status"),
        "fully_delivered": result.get("fully_delivered"),
        "supply_items_updated": result.get("supply_items_updated", 0)
    }


@router.get("/project/{project_id}/supply-status", response_model=SupplyStatusResponse)
async def get_project_supply_status(
    project_id: UUID,
    delivery_service: DeliveryService = Depends(get_delivery_service),
    current_user: dict = Depends(get_current_user)
):
    """الحصول على حالة التوريد لمشروع محدد"""
    status = await delivery_service.get_project_supply_status(project_id)
    return SupplyStatusResponse(**status)

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
    current_user: dict = Depends(get_current_user)
):
    """الحصول على أوامر الشراء بانتظار التسليم"""
    orders = await delivery_service.get_pending_deliveries()
    return [
        {
            "id": str(o.id),
            "order_number": o.order_number,
            "status": o.status,
            "total_amount": o.total_amount or 0,
            "items_count": len(o.items) if hasattr(o, 'items') and o.items else 0
        }
        for o in orders
    ]


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

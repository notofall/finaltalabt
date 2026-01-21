"""
Delivery API v2 - Using Services Layer
API التسليم باستخدام طبقة الخدمات
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.services import DeliveryService
from app.dependencies import get_delivery_service
from routes.v2_auth_routes import get_current_user
from database.connection import get_postgres_session as get_session


router = APIRouter(prefix="/api/v2/delivery", tags=["Delivery V2"])


# ==================== Schemas ====================

class DeliveryItemConfirm(BaseModel):
    item_id: Optional[str] = None
    name: Optional[str] = None
    quantity_delivered: float


class DeliveryConfirmRequest(BaseModel):
    items: List[DeliveryItemConfirm]
    supplier_receipt_number: Optional[str] = None
    delivery_notes: Optional[str] = None


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
    from database import Project, Supplier, MaterialRequest, PurchaseOrderItem
    from sqlalchemy import select
    
    orders = await delivery_service.get_pending_deliveries()
    result = []
    
    for o in orders:
        # Get project name
        project_name = o.project_name
        if not project_name and o.project_id:
            project_result = await session.execute(
                select(Project.name).where(Project.id == o.project_id)
            )
            project_name = project_result.scalar_one_or_none()
        
        # Get supplier name
        supplier_name = o.supplier_name
        if not supplier_name and o.supplier_id:
            supplier_result = await session.execute(
                select(Supplier.name).where(Supplier.id == o.supplier_id)
            )
            supplier_name = supplier_result.scalar_one_or_none()
        
        # Get request number
        request_number = o.request_number
        if not request_number and o.request_id:
            request_result = await session.execute(
                select(MaterialRequest.request_number).where(MaterialRequest.id == o.request_id)
            )
            request_number = request_result.scalar_one_or_none()
        
        # Get order items from PurchaseOrderItem table
        items_result = await session.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.order_id == o.id)
        )
        items = list(items_result.scalars().all())
        
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
            "items_count": len(items),
            "items": [
                {
                    "id": str(item.id),
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit or "قطعة",
                    "unit_price": item.unit_price or 0,
                    "total_price": item.total_price or 0,
                    "delivered_quantity": item.delivered_quantity or 0,
                    "remaining_quantity": item.quantity - (item.delivered_quantity or 0)
                }
                for item in items
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
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    تأكيد استلام العناصر
    يقوم تلقائياً بتحديث تتبع التوريد
    """
    from database import PurchaseOrder, PurchaseOrderItem
    from sqlalchemy import select, update
    
    # Get user attributes safely
    user_role = current_user.role if hasattr(current_user, 'role') else current_user.get("role", "")
    user_id = str(current_user.id) if hasattr(current_user, 'id') else current_user.get("id", "")
    user_name = current_user.name if hasattr(current_user, 'name') else current_user.get("name", "Unknown")
    
    # التحقق من الصلاحيات
    allowed_roles = ["system_admin", "procurement_manager", "delivery_tracker"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية تأكيد الاستلام"
        )
    
    # Get the order
    order_result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == str(order_id))
    )
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="أمر الشراء غير موجود"
        )
    
    # Update supplier receipt number if provided
    if request.supplier_receipt_number:
        order.supplier_receipt_number = request.supplier_receipt_number
    
    if request.delivery_notes:
        order.delivery_notes = request.delivery_notes
    
    # Get all order items
    items_result = await session.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.order_id == str(order_id))
    )
    order_items = {item.name: item for item in items_result.scalars().all()}
    
    # Update delivered quantities
    all_fully_delivered = True
    items_updated = 0
    
    for delivery_item in request.items:
        item_name = delivery_item.name
        if not item_name and delivery_item.item_id:
            # Try to find by ID
            item_result = await session.execute(
                select(PurchaseOrderItem).where(PurchaseOrderItem.id == delivery_item.item_id)
            )
            found_item = item_result.scalar_one_or_none()
            if found_item:
                item_name = found_item.name
        
        if item_name and item_name in order_items:
            item = order_items[item_name]
            new_delivered = (item.delivered_quantity or 0) + delivery_item.quantity_delivered
            item.delivered_quantity = min(int(new_delivered), item.quantity)  # Cap at max quantity
            items_updated += 1
            
            if item.delivered_quantity < item.quantity:
                all_fully_delivered = False
        else:
            all_fully_delivered = False
    
    # Check if there are items not yet fully delivered
    for item in order_items.values():
        if (item.delivered_quantity or 0) < item.quantity:
            all_fully_delivered = False
            break
    
    # Update order status
    if all_fully_delivered:
        order.status = "delivered"
        order.delivered_at = datetime.now(timezone.utc)
    else:
        order.status = "partially_delivered"
    
    order.received_by_id = user_id
    order.received_by_name = user_name
    
    await session.commit()
    
    return {
        "message": "تم تأكيد الاستلام بنجاح",
        "status": order.status,
        "fully_delivered": all_fully_delivered,
        "items_updated": items_updated
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

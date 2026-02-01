"""
Orders API v2 - Using Service Layer (Clean)
API أوامر الشراء V2 - باستخدام طبقة الخدمات (نظيف)

Architecture: Route -> Service -> Repository
- Routes: HTTP handling, auth, response formatting
- Services: Business logic
- Repositories: Data access

NO direct SQL in routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from typing import List as ListType
from uuid import UUID
from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from database import PurchaseOrder, PurchaseOrderItem, MaterialRequest
from database.connection import get_postgres_session
from sqlalchemy import select

# Import Services via DI
from app.services import OrderService
from app.dependencies import get_order_service
from app.config import PaginationConfig, to_iso_string
from routes.v2_auth_routes import get_current_user


router = APIRouter(prefix="/api/v2/orders", tags=["Orders V2"])

# Pagination
MAX_LIMIT = PaginationConfig.MAX_PAGE_SIZE
DEFAULT_LIMIT = PaginationConfig.DEFAULT_PAGE_SIZE


# ==================== Schemas ====================

class OrderItemResponse(BaseModel):
    id: str
    name: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    delivered_quantity: float
    catalog_item_id: Optional[str]
    item_code: Optional[str]


class OrderResponse(BaseModel):
    id: str
    order_number: Optional[str]
    order_seq: Optional[int]
    request_id: Optional[str]
    request_number: Optional[str]
    items: List[OrderItemResponse]
    project_id: Optional[str]
    project_name: Optional[str]
    supplier_id: Optional[str]
    supplier_name: Optional[str]
    category_id: Optional[str]
    category_name: Optional[str]
    manager_id: Optional[str]
    manager_name: Optional[str]
    supervisor_name: Optional[str]
    engineer_name: Optional[str]
    status: str
    needs_gm_approval: bool
    approved_by_name: Optional[str]
    gm_approved_by_name: Optional[str]
    total_amount: float
    notes: Optional[str]
    supplier_invoice_number: Optional[str]
    expected_delivery_date: Optional[str]
    # حقول الدور والنموذج
    floor_id: Optional[str] = None
    floor_name: Optional[str] = None
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    created_at: Optional[str]
    approved_at: Optional[str]
    printed_at: Optional[str]

    class Config:
        from_attributes = True


class OrderStatsResponse(BaseModel):
    total: int
    pending: int
    approved: int
    delivered: int
    rejected: int


class OrdersListResponse(BaseModel):
    """Paginated orders response"""
    items: List[OrderResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


# ==================== Helper ====================

def order_to_response(order: PurchaseOrder, items: List[dict]) -> dict:
    """Convert Order model to response dict"""
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "order_seq": order.order_seq,
        "request_id": order.request_id,
        "request_number": order.request_number,
        "items": items,
        "project_id": order.project_id,
        "project_name": order.project_name,
        "supplier_id": order.supplier_id,
        "supplier_name": order.supplier_name,
        "category_id": order.category_id,
        "category_name": order.category_name,
        "manager_id": order.manager_id,
        "manager_name": order.manager_name,
        "supervisor_name": getattr(order, 'supervisor_name', None),
        "engineer_name": getattr(order, 'engineer_name', None),
        "status": order.status or "pending_approval",
        "needs_gm_approval": order.needs_gm_approval or False,
        "approved_by_name": order.approved_by_name,
        "gm_approved_by_name": order.gm_approved_by_name,
        "total_amount": order.total_amount or 0,
        "notes": order.notes,
        "supplier_invoice_number": order.supplier_invoice_number,
        "expected_delivery_date": order.expected_delivery_date,
        # حقول الدور والنموذج
        "floor_id": getattr(order, 'floor_id', None),
        "floor_name": getattr(order, 'floor_name', None),
        "template_id": getattr(order, 'template_id', None),
        "template_name": getattr(order, 'template_name', None),
        "created_at": to_iso_string(order.created_at),
        "approved_at": to_iso_string(order.approved_at),
        "printed_at": to_iso_string(order.printed_at)
    }


async def get_orders_with_items_via_service(
    order_service: OrderService,
    orders: List[PurchaseOrder]
) -> List[dict]:
    """Get orders with their items via Service layer"""
    if not orders:
        return []
    
    order_ids = [str(o.id) for o in orders]
    items_map = await order_service.get_orders_items_batch(order_ids)
    
    return [
        order_to_response(order, items_map.get(str(order.id), []))
        for order in orders
    ]


# ==================== Routes ====================

@router.get("/", response_model=OrdersListResponse)
async def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    status_filter: Optional[str] = None,
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """
    الحصول على جميع أوامر الشراء مع الأصناف
    Uses: OrderService -> OrderRepository
    Real pagination with total count
    """
    limit = min(limit, MAX_LIMIT)
    
    # Get total count
    total = await order_service.count_orders(status_filter)
    
    if status_filter:
        orders = await order_service.get_orders_by_status(status_filter)
        orders = orders[skip:skip + limit]
    else:
        orders = await order_service.get_all_orders(skip, limit)
    
    items = await get_orders_with_items_via_service(order_service, orders)
    
    return OrdersListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(items)) < total
    )


@router.get("/stats", response_model=OrderStatsResponse)
async def get_order_stats(
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """الحصول على إحصائيات أوامر الشراء"""
    return await order_service.get_order_stats()


@router.get("/pending", response_model=List[OrderResponse])
async def get_pending_orders(
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """الحصول على أوامر الشراء المعلقة"""
    orders = await order_service.get_orders_by_status("pending_approval")
    gm_pending = await order_service.get_orders_by_status("pending_gm_approval")
    
    return await get_orders_with_items_via_service(order_service, orders + gm_pending)


@router.get("/approved", response_model=List[OrderResponse])
async def get_approved_orders(
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """الحصول على أوامر الشراء المعتمدة"""
    approved = await order_service.get_orders_by_status("approved")
    printed = await order_service.get_orders_by_status("printed")
    shipped = await order_service.get_orders_by_status("shipped")
    
    return await get_orders_with_items_via_service(order_service, approved + printed + shipped)


@router.get("/pending-delivery", response_model=List[OrderResponse])
async def get_pending_delivery_orders(
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """الحصول على أوامر الشراء بانتظار التسليم"""
    orders = await order_service.get_pending_delivery_orders()
    return await get_orders_with_items_via_service(order_service, orders)


@router.get("/by-project/{project_id}", response_model=List[OrderResponse])
async def get_orders_by_project(
    project_id: UUID,
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """الحصول على أوامر الشراء لمشروع محدد"""
    orders = await order_service.get_orders_by_project(project_id)
    return await get_orders_with_items_via_service(order_service, orders)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """الحصول على أمر شراء محدد مع الأصناف"""
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="أمر الشراء غير موجود"
        )
    
    items = await order_service.get_order_items(str(order.id))
    return order_to_response(order, items)


@router.post("/{order_id}/approve")
async def approve_order(
    order_id: UUID,
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """اعتماد أمر شراء"""
    user_id = current_user.get("id") if isinstance(current_user, dict) else str(current_user.id)
    
    order = await order_service.approve_order(order_id, approved_by=user_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="أمر الشراء غير موجود"
        )
    
    return {"message": "تم اعتماد أمر الشراء بنجاح", "status": order.status}


@router.post("/{order_id}/reject")
async def reject_order(
    order_id: UUID,
    reason: str = "",
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """رفض أمر شراء"""
    user_id = current_user.get("id") if isinstance(current_user, dict) else str(current_user.id)
    
    order = await order_service.reject_order(
        order_id,
        rejected_by=user_id,
        rejection_reason=reason
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="أمر الشراء غير موجود"
        )
    
    return {"message": "تم رفض أمر الشراء", "status": order.status}


# ==================== Additional Order Endpoints ====================

from pydantic import BaseModel

class OrderItemCreate(BaseModel):
    name: str
    quantity: float
    unit: str
    unit_price: float = 0
    catalog_item_id: Optional[str] = None

class OrderCreate(BaseModel):
    project_id: str
    supplier_id: str
    request_id: Optional[str] = None
    category_id: Optional[str] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    items: ListType[OrderItemCreate] = []

class OrderFromRequestCreate(BaseModel):
    """إنشاء أمر شراء من طلب موجود"""
    request_id: str
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    selected_items: ListType[int] = []  # Item indices
    item_prices: ListType[dict] = []  # [{"index": 0, "unit_price": 10}, ...]
    category_id: Optional[str] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    expected_delivery_date: Optional[str] = None


@router.post("/from-request", status_code=status.HTTP_201_CREATED)
async def create_order_from_request(
    data: OrderFromRequestCreate,
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """إنشاء أمر شراء من طلب موجود"""
    from datetime import datetime, timezone
    from database import PurchaseOrder, MaterialRequestItem, Project, Supplier
    from sqlalchemy import select
    import uuid as uuid_lib
    
    session = order_service.order_repo.session
    
    # Get request
    request_result = await session.execute(
        select(MaterialRequest).where(MaterialRequest.id == data.request_id)
    )
    request = request_result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    # Get request items
    items_result = await session.execute(
        select(MaterialRequestItem).where(MaterialRequestItem.request_id == data.request_id)
    )
    request_items = list(items_result.scalars().all())
    
    # If no items selected, use all items
    selected_indices = data.selected_items if data.selected_items else list(range(len(request_items)))
    
    # Create price map from item_prices
    price_map = {}
    for price_item in data.item_prices:
        if isinstance(price_item, dict):
            price_map[price_item.get("index", 0)] = price_item.get("unit_price", 0)
    
    # Get supplier info
    supplier_name = data.supplier_name or ""
    if data.supplier_id:
        supplier_result = await session.execute(
            select(Supplier).where(Supplier.id == data.supplier_id)
        )
        supplier = supplier_result.scalar_one_or_none()
        if supplier:
            supplier_name = supplier.name
    
    # Generate order number
    count_result = await session.execute(
        select(func.count()).select_from(PurchaseOrder)
    )
    count = count_result.scalar_one() or 0
    order_number = f"PO-{count + 1:05d}"
    
    # Create order
    order = PurchaseOrder(
        id=str(uuid_lib.uuid4()),
        order_number=order_number,
        request_id=data.request_id,
        project_id=request.project_id,
        project_name=request.project_name,
        supplier_id=data.supplier_id,
        supplier_name=supplier_name,
        category_id=data.category_id,
        manager_id=str(current_user.id) if hasattr(current_user, 'id') else None,
        manager_name=current_user.name if hasattr(current_user, 'name') else "النظام",
        supervisor_name=request.supervisor_name,
        engineer_name=request.engineer_name,
        status="pending",
        total_amount=0,
        notes=data.notes,
        terms_conditions=data.terms_conditions,
        expected_delivery_date=data.expected_delivery_date,
        # نقل حقول الدور والنموذج من الطلب
        floor_id=getattr(request, 'floor_id', None),
        floor_name=getattr(request, 'floor_name', None),
        template_id=getattr(request, 'template_id', None),
        template_name=getattr(request, 'template_name', None),
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    
    session.add(order)
    await session.flush()
    
    # Import ItemAlias for alias lookup
    from database import ItemAlias
    
    # Create order items from selected request items
    total_amount = 0
    for idx in selected_indices:
        if idx < len(request_items):
            req_item = request_items[idx]
            unit_price = price_map.get(idx, 0)
            total_price = unit_price * req_item.quantity
            total_amount += total_price
            
            # First check if request item already has catalog_item_id
            catalog_item_id = req_item.catalog_item_id if hasattr(req_item, 'catalog_item_id') else None
            item_code = None
            
            # If not linked, check if item name has an alias linked to catalog
            if not catalog_item_id:
                alias_result = await session.execute(
                    select(ItemAlias).where(ItemAlias.alias_name == req_item.name)
                )
                alias = alias_result.scalar_one_or_none()
                if alias:
                    catalog_item_id = alias.catalog_item_id
            
            # Get item_code from catalog if we have catalog_item_id
            if catalog_item_id:
                from database import PriceCatalogItem
                cat_result = await session.execute(
                    select(PriceCatalogItem).where(PriceCatalogItem.id == catalog_item_id)
                )
                cat_item = cat_result.scalar_one_or_none()
                if cat_item:
                    item_code = cat_item.item_code
            
            order_item = PurchaseOrderItem(
                id=str(uuid_lib.uuid4()),
                order_id=order.id,
                name=req_item.name,
                quantity=req_item.quantity,
                unit=req_item.unit,
                unit_price=unit_price,
                total_price=total_price,
                delivered_quantity=0,
                item_index=idx,
                catalog_item_id=catalog_item_id,
                item_code=item_code
            )
            session.add(order_item)
    
    # Update order total
    order.total_amount = total_amount
    
    # التحقق من حد الموافقة للمدير العام
    from database.models import SystemSetting
    approval_limit_result = await session.execute(
        select(SystemSetting).where(SystemSetting.key == "approval_limit")
    )
    approval_setting = approval_limit_result.scalar_one_or_none()
    approval_limit = float(approval_setting.value) if approval_setting and approval_setting.value else 20000
    
    if total_amount > approval_limit:
        order.needs_gm_approval = True
        order.status = "pending_gm_approval"
    else:
        order.needs_gm_approval = False
        order.status = "pending_approval"
    
    # Update request status
    request.status = "po_issued"
    request.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    await session.commit()
    
    return {
        "message": "تم إنشاء أمر الشراء بنجاح" + (" - بانتظار موافقة المدير العام" if order.needs_gm_approval else ""),
        "order_id": order.id,
        "order_number": order_number,
        "total_amount": total_amount,
        "needs_gm_approval": order.needs_gm_approval
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """إنشاء أمر شراء جديد"""
    from datetime import datetime
    from database import get_postgres_session, PurchaseOrder, Project, Supplier
    from sqlalchemy import select
    import uuid as uuid_lib
    
    session = order_service.order_repo.session
    
    # Get project
    project_result = await session.execute(
        select(Project).where(Project.id == data.project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    # Get supplier
    supplier_result = await session.execute(
        select(Supplier).where(Supplier.id == data.supplier_id)
    )
    supplier = supplier_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="المورد غير موجود")
    
    # Generate order number
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    order_number = f"PO-{now.strftime('%Y%m%d')}-{str(uuid_lib.uuid4())[:8].upper()}"
    
    # Calculate total
    total_amount = sum(item.quantity * item.unit_price for item in data.items)
    
    # التحقق من حد الموافقة للمدير العام
    from database.models import SystemSetting
    approval_limit_result = await session.execute(
        select(SystemSetting).where(SystemSetting.key == "approval_limit")
    )
    approval_setting = approval_limit_result.scalar_one_or_none()
    approval_limit = float(approval_setting.value) if approval_setting and approval_setting.value else 20000
    
    needs_gm = total_amount > approval_limit
    order_status = "pending_gm_approval" if needs_gm else "pending_approval"
    
    # Parse delivery date
    delivery_date = None
    if data.expected_delivery_date:
        try:
            delivery_date = datetime.fromisoformat(data.expected_delivery_date.replace('Z', '+00:00'))
        except:
            pass
    
    # Create order
    order = PurchaseOrder(
        id=str(uuid_lib.uuid4()),
        order_number=order_number,
        request_id=data.request_id,
        project_id=data.project_id,
        project_name=project.name,
        supplier_id=data.supplier_id,
        supplier_name=supplier.name,
        category_id=data.category_id,
        total_amount=total_amount,
        status=order_status,
        needs_gm_approval=needs_gm,
        notes=data.notes,
        terms_conditions=data.terms_conditions,
        expected_delivery_date=delivery_date,
        manager_id=str(current_user.id),
        manager_name=current_user.name,
        created_at=now,
        updated_at=now
    )
    session.add(order)
    
    # Create items
    for idx, item in enumerate(data.items):
        order_item = PurchaseOrderItem(
            id=str(uuid_lib.uuid4()),
            order_id=order.id,
            name=item.name,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price,
            catalog_item_id=item.catalog_item_id,
            item_index=idx
        )
        session.add(order_item)
    
    await session.commit()
    
    return {
        "message": "تم إنشاء أمر الشراء بنجاح" + (" - بانتظار موافقة المدير العام" if needs_gm else ""),
        "order_id": order.id,
        "order_number": order_number,
        "needs_gm_approval": needs_gm
    }


@router.put("/{order_id}")
async def update_order(
    order_id: UUID,
    data: dict,
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """تحديث أمر شراء - بما في ذلك أسعار الأصناف"""
    from database import PurchaseOrder
    from sqlalchemy import select
    
    session = order_service.order_repo.session
    
    result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == str(order_id))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="أمر الشراء غير موجود")
    
    # Update allowed fields
    allowed_fields = ["notes", "terms_conditions", "expected_delivery_date", 
                      "supplier_name", "supplier_id", "category_id", "supplier_invoice_number"]
    for field in allowed_fields:
        if field in data and data[field] is not None:
            setattr(order, field, data[field])
    
    # Update item prices if provided
    item_prices = data.get("item_prices", [])
    if item_prices:
        # Get all items for this order
        items_result = await session.execute(
            select(PurchaseOrderItem)
            .where(PurchaseOrderItem.order_id == str(order_id))
            .order_by(PurchaseOrderItem.created_at)
        )
        items = items_result.scalars().all()
        
        # Update prices
        new_total = 0
        for price_info in item_prices:
            idx = price_info.get("index", -1)
            unit_price = price_info.get("unit_price", 0)
            
            if 0 <= idx < len(items):
                item = items[idx]
                item.unit_price = unit_price
                item.total_price = unit_price * (item.quantity or 0)
                new_total += item.total_price
        
        # Update order total
        order.total_amount = new_total
    
    from datetime import datetime, timezone
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.commit()
    
    return {"message": "تم تحديث أمر الشراء بنجاح", "total_amount": order.total_amount}


@router.put("/{order_id}/items/{item_id}/catalog-link")
async def link_item_to_catalog(
    order_id: UUID,
    item_id: str,
    data: dict,
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """ربط عنصر بالكتالوج وإنشاء اسم بديل"""
    from database import ItemAlias, PriceCatalogItem
    from sqlalchemy import select
    import uuid as uuid_lib
    from datetime import datetime, timezone
    
    session = order_service.order_repo.session
    
    result = await session.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="العنصر غير موجود")
    
    catalog_item_id = data.get("catalog_item_id")
    item.catalog_item_id = catalog_item_id
    
    # Get catalog item name
    catalog_item_name = ""
    if catalog_item_id:
        cat_result = await session.execute(
            select(PriceCatalogItem).where(PriceCatalogItem.id == catalog_item_id)
        )
        cat_item = cat_result.scalar_one_or_none()
        if cat_item:
            catalog_item_name = cat_item.name
            
            # Create alias if item name is different from catalog name
            if item.name and item.name.strip() != cat_item.name.strip():
                # Check if alias already exists
                alias_check = await session.execute(
                    select(ItemAlias).where(
                        ItemAlias.alias_name == item.name,
                        ItemAlias.catalog_item_id == catalog_item_id
                    )
                )
                existing_alias = alias_check.scalar_one_or_none()
                
                if not existing_alias:
                    # Create new alias
                    user_id = str(current_user.id) if hasattr(current_user, 'id') else "system"
                    user_name = current_user.name if hasattr(current_user, 'name') else "النظام"
                    
                    new_alias = ItemAlias(
                        id=str(uuid_lib.uuid4()),
                        alias_name=item.name,
                        catalog_item_id=catalog_item_id,
                        catalog_item_name=catalog_item_name,
                        usage_count=1,
                        created_by=user_id,
                        created_by_name=user_name,
                        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
                    )
                    session.add(new_alias)
    
    await session.commit()
    
    return {"message": "تم ربط العنصر بالكتالوج", "alias_created": catalog_item_name != "" and item.name != catalog_item_name}


@router.post("/{order_id}/sync-prices")
async def sync_order_prices(
    order_id: UUID,
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """مزامنة أسعار أمر الشراء مع الكتالوج"""
    from database import PurchaseOrder, PriceCatalogItem
    from sqlalchemy import select
    
    session = order_service.order_repo.session
    
    # Get order
    result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == str(order_id))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="أمر الشراء غير موجود")
    
    # Get items
    items_result = await session.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.order_id == str(order_id))
    )
    items = items_result.scalars().all()
    
    updated_count = 0
    for item in items:
        if item.catalog_item_id:
            catalog_result = await session.execute(
                select(PriceCatalogItem).where(PriceCatalogItem.id == item.catalog_item_id)
            )
            catalog_item = catalog_result.scalar_one_or_none()
            
            if catalog_item:
                item.unit_price = catalog_item.price
                item.total_price = item.quantity * catalog_item.price
                updated_count += 1
    
    # Update order total
    order.total_amount = sum(item.total_price or 0 for item in items)
    
    from datetime import datetime, timezone
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.commit()
    
    return {
        "message": f"تم تحديث أسعار {updated_count} عنصر",
        "updated_items": updated_count,
        "new_total": order.total_amount
    }



# ==================== Print & Invoice ====================

@router.put("/{order_id}/print")
async def mark_order_printed(
    order_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """تسجيل طباعة أمر الشراء"""
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="أمر الشراء غير موجود"
        )
    
    # Update print status
    from datetime import datetime, timezone
    order.is_printed = True
    order.printed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.commit()
    
    return {"message": "تم تسجيل الطباعة بنجاح"}


class SupplierInvoiceUpdate(BaseModel):
    supplier_invoice_number: str


@router.put("/{order_id}/supplier-invoice")
async def update_supplier_invoice(
    order_id: UUID,
    data: SupplierInvoiceUpdate,
    session: AsyncSession = Depends(get_postgres_session),
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """تحديث رقم فاتورة المورد"""
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="أمر الشراء غير موجود"
        )
    
    from datetime import datetime, timezone
    order.supplier_invoice_number = data.supplier_invoice_number
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.commit()
    
    return {"message": "تم تحديث رقم الفاتورة بنجاح"}



# ==================== Procurement Confirmation ====================

@router.post("/{order_id}/procurement-confirm")
async def procurement_confirm_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
    current_user = Depends(get_current_user)
):
    """
    تأكيد أمر الشراء من مدير المشتريات بعد موافقة المدير العام
    """
    from database.models import UserRole
    
    # التحقق من الصلاحيات
    if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.PROCUREMENT_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط مدير المشتريات يمكنه تأكيد أوامر الشراء"
        )
    
    # الحصول على الأمر
    result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == str(order_id))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="أمر الشراء غير موجود")
    
    # التحقق من حالة الأمر
    if order.status != "pending_procurement_confirmation":
        raise HTTPException(
            status_code=400, 
            detail=f"لا يمكن تأكيد أمر في حالة: {order.status}. يجب أن يكون بانتظار تأكيد المشتريات"
        )
    
    # تحديث الحالة
    order.status = "approved"
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    await session.commit()
    
    # تسجيل في سجل المراجعة
    try:
        from app.audit_logger import audit_log, AuditAction
        await audit_log(
            session=session,
            user_id=current_user.id,
            user_name=current_user.name,
            action=AuditAction.APPROVAL,
            entity_type="purchase_order",
            entity_id=str(order_id),
            details={
                "order_number": order.order_number,
                "action": "procurement_confirmation",
                "message": "تم تأكيد أمر الشراء من مدير المشتريات"
            }
        )
    except Exception as e:
        print(f"Audit log error: {e}")
    
    return {
        "message": "تم تأكيد أمر الشراء بنجاح",
        "order_id": str(order_id),
        "order_number": order.order_number,
        "new_status": "approved"
    }


# ==================== Delete Order (with Permission) ====================

class DeleteOrderReason(BaseModel):
    reason: str


@router.delete("/{order_id}")
async def delete_order(
    order_id: UUID,
    data: DeleteOrderReason,
    session: AsyncSession = Depends(get_postgres_session),
    order_service: OrderService = Depends(get_order_service),
    current_user = Depends(get_current_user)
):
    """
    حذف أمر الشراء (للمشتريات مع الصلاحية)
    
    الشروط:
    - المستخدم يجب أن يكون مدير مشتريات أو مدير النظام
    - مدير المشتريات يحتاج صلاحية من مدير النظام
    - يتم تسجيل الحذف في سجل التدقيق
    - يتم إرجاع الطلب المرتبط لحالته السابقة (approved_by_engineer أو partially_ordered)
    """
    from routes.v2_auth_routes import UserRole
    from app.audit_logger import audit_log, AuditAction
    from app.repositories.settings_repository import SettingsRepository
    from database import PurchaseOrder
    
    # Check permission
    if current_user.role == UserRole.SYSTEM_ADMIN:
        # System admin always has permission
        pass
    elif current_user.role == UserRole.PROCUREMENT_MANAGER:
        # Check if procurement manager has delete permission
        settings_repo = SettingsRepository(session)
        setting = await settings_repo.get_setting("procurement_can_delete_orders")
        can_delete = setting.value if setting else "false"
        
        if can_delete != "true":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية حذف أوامر الشراء. تواصل مع مدير النظام لمنحك الصلاحية."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="صلاحيات غير كافية لحذف أوامر الشراء"
        )
    
    # Get order
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="أمر الشراء غير موجود"
        )
    
    # Store request_id before deletion
    request_id = order.request_id
    request_status_updated = False
    new_request_status = None
    
    # Prepare audit data
    order_data = {
        "order_number": order.order_number,
        "request_id": request_id,
        "project_name": order.project_name,
        "supplier_name": order.supplier_name,
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": str(order.created_at),
        "delete_reason": data.reason,
        "items_count": 0
    }
    
    # Get order items before deletion
    items_result = await session.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.order_id == str(order_id))
    )
    items = items_result.scalars().all()
    order_data["items_count"] = len(items)
    order_data["items"] = [
        {
            "name": item.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price": item.unit_price,
            "total_price": item.total_price
        }
        for item in items
    ]
    
    # Delete items first
    for item in items:
        await session.delete(item)
    
    # Delete order
    await session.delete(order)
    
    # Update the related request status
    if request_id:
        # Check if there are other orders for this request
        other_orders_result = await session.execute(
            select(func.count(PurchaseOrder.id))
            .where(PurchaseOrder.request_id == request_id)
            .where(PurchaseOrder.id != str(order_id))
        )
        other_orders_count = other_orders_result.scalar() or 0
        
        # Get the request
        request_result = await session.execute(
            select(MaterialRequest).where(MaterialRequest.id == request_id)
        )
        request = request_result.scalar_one_or_none()
        
        if request:
            if other_orders_count > 0:
                # There are other orders, set to partially_ordered
                new_request_status = "partially_ordered"
            else:
                # No other orders, return to approved_by_engineer
                new_request_status = "approved_by_engineer"
            
            request.status = new_request_status
            request.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            request_status_updated = True
            order_data["request_status_updated"] = True
            order_data["new_request_status"] = new_request_status
    
    # Log to audit
    await audit_log.log(
        session=session,
        action=AuditAction.ORDER_DELETE,
        user_id=str(current_user.id),
        user_name=current_user.name,
        user_role=current_user.role,
        entity_type="purchase_order",
        entity_id=str(order_id),
        description=f"حذف أمر الشراء {order.order_number} - السبب: {data.reason}" + 
                    (f" - تم إرجاع الطلب للحالة: {new_request_status}" if request_status_updated else ""),
        changes=order_data
    )
    
    await session.commit()
    
    response = {
        "message": f"تم حذف أمر الشراء {order.order_number} بنجاح",
        "order_number": order.order_number,
        "deleted_by": current_user.name
    }
    
    if request_status_updated:
        response["request_status_updated"] = True
        response["new_request_status"] = new_request_status
        response["request_message"] = f"تم إرجاع الطلب للحالة: {'معتمد من المهندس' if new_request_status == 'approved_by_engineer' else 'صدر منه أوامر جزئية'}"
    
    return response


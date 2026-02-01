"""
Requests API v2 - Using Service Layer (Clean)
API طلبات المواد V2 - باستخدام طبقة الخدمات (نظيف)

Architecture: Route -> Service -> Repository
- Routes: HTTP handling, auth, response formatting
- Services: Business logic
- Repositories: Data access

NO direct SQL in routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import select

from database import MaterialRequest, Project, User

# Import Services via DI
from app.services import RequestService
from app.dependencies import get_request_service
from app.config import PaginationConfig, to_iso_string
from routes.v2_auth_routes import get_current_user
from database.connection import get_postgres_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v2/requests", tags=["Requests V2"])

# Pagination
MAX_LIMIT = PaginationConfig.MAX_PAGE_SIZE
DEFAULT_LIMIT = PaginationConfig.DEFAULT_PAGE_SIZE


# ==================== Schemas ====================

class RequestItemResponse(BaseModel):
    name: str
    quantity: float  # Changed to float to support fractional quantities
    unit: str
    estimated_price: Optional[float]
    catalog_item_id: Optional[str] = None


class RequestResponse(BaseModel):
    id: str
    request_number: Optional[str]
    request_seq: Optional[int]
    items: List[RequestItemResponse]
    project_id: Optional[str]
    project_name: Optional[str]
    reason: Optional[str]
    supervisor_id: Optional[str]
    supervisor_name: Optional[str]
    engineer_id: Optional[str]
    engineer_name: Optional[str]
    status: str
    rejection_reason: Optional[str]
    expected_delivery_date: Optional[str]
    # حقول الدور والنموذج
    floor_id: Optional[str] = None
    floor_name: Optional[str] = None
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class RequestStatsResponse(BaseModel):
    total: int
    pending: int
    approved: int
    rejected: int
    ordered: int


class RequestsListResponse(BaseModel):
    """Paginated requests response"""
    items: List[RequestResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


# ==================== Request Create/Update Schemas ====================

class RequestItemCreate(BaseModel):
    name: str
    quantity: float  # Changed to float to support fractional quantities
    unit: str = "قطعة"
    estimated_price: Optional[float] = None
    catalog_item_id: Optional[str] = None  # Link to catalog item


class RequestCreate(BaseModel):
    items: List[RequestItemCreate]
    project_id: str
    reason: str
    engineer_id: str
    expected_delivery_date: Optional[str] = None


class RequestUpdate(BaseModel):
    items: List[RequestItemCreate]
    project_id: str
    reason: str
    engineer_id: str


# ==================== Helper ====================

def request_to_response(req: MaterialRequest, items: List[dict]) -> dict:
    """Convert MaterialRequest model to response dict"""
    return {
        "id": str(req.id),
        "request_number": req.request_number,
        "request_seq": req.request_seq,
        "items": items,
        "project_id": str(req.project_id) if req.project_id else None,
        "project_name": req.project_name,
        "reason": req.reason,
        "supervisor_id": str(req.supervisor_id) if req.supervisor_id else None,
        "supervisor_name": req.supervisor_name,
        "engineer_id": str(req.engineer_id) if req.engineer_id else None,
        "engineer_name": req.engineer_name,
        "status": req.status or "pending_engineer",
        "rejection_reason": req.rejection_reason,
        "manager_rejection_reason": getattr(req, 'manager_rejection_reason', None),
        "rejected_by_manager_id": getattr(req, 'rejected_by_manager_id', None),
        "expected_delivery_date": req.expected_delivery_date,
        "created_at": to_iso_string(req.created_at),
        "updated_at": to_iso_string(req.updated_at)
    }


async def get_requests_with_items_via_service(
    request_service: RequestService,
    requests: List[MaterialRequest]
) -> List[dict]:
    """Get requests with their items via Service layer"""
    if not requests:
        return []
    
    request_ids = [str(r.id) for r in requests]
    items_map = await request_service.get_requests_items_batch(request_ids)
    
    return [
        request_to_response(req, items_map.get(str(req.id), []))
        for req in requests
    ]


# ==================== Routes ====================

@router.get("/", response_model=RequestsListResponse)
async def get_all_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    status_filter: Optional[str] = None,
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """
    الحصول على جميع الطلبات مع الأصناف
    Uses: RequestService -> RequestRepository
    Real pagination with total count
    """
    limit = min(limit, MAX_LIMIT)
    
    # Get total count
    total = await request_service.count_requests(status_filter)
    
    if status_filter:
        requests = await request_service.get_requests_by_status(status_filter)
        requests = requests[skip:skip + limit]
    else:
        requests = await request_service.get_all_requests(skip, limit)
    
    items = await get_requests_with_items_via_service(request_service, requests)
    
    return RequestsListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(items)) < total
    )


@router.get("/stats", response_model=RequestStatsResponse)
async def get_request_stats(
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """الحصول على إحصائيات الطلبات"""
    return await request_service.get_request_stats()


# ==================== Create Request ====================

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_request(
    data: RequestCreate,
    session: AsyncSession = Depends(get_postgres_session),
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """
    إنشاء طلب مواد جديد
    Create a new material request
    - المهندس يتم تعيينه أوتوماتيكياً من المشروع إذا كان محدداً
    - رقم الطلب: PREFIX-PROJECT_CODE-SEQUENCE
    """
    # Get user info
    user_id = current_user.get("id") if isinstance(current_user, dict) else str(current_user.id)
    user_name = current_user.get("name", "") if isinstance(current_user, dict) else current_user.name
    supervisor_prefix = current_user.get("supervisor_prefix") if isinstance(current_user, dict) else getattr(current_user, 'supervisor_prefix', None)
    
    # Get project info
    project_result = await session.execute(
        select(Project).where(Project.id == data.project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المشروع غير موجود"
        )
    
    # تحديد المهندس: من المشروع أو من البيانات المرسلة
    engineer_id = data.engineer_id
    engineer_name = None
    
    # إذا كان المشروع له مهندس معين، استخدمه تلقائياً
    if hasattr(project, 'engineer_id') and project.engineer_id:
        engineer_id = project.engineer_id
        engineer_name = getattr(project, 'engineer_name', None)
    
    # Get engineer info if not already set from project
    if not engineer_name and engineer_id:
        engineer_result = await session.execute(
            select(User).where(User.id == engineer_id)
        )
        engineer = engineer_result.scalar_one_or_none()
        if not engineer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="المهندس غير موجود"
            )
        engineer_name = engineer.name
    
    if not engineer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="يجب تحديد المهندس للمشروع"
        )
    
    # Create request with project code
    project_code = getattr(project, 'code', None) or project.name[:10]
    request = await request_service.create_request(
        project_id=data.project_id,
        project_name=project.name,
        reason=data.reason,
        supervisor_id=user_id,
        supervisor_name=user_name,
        engineer_id=engineer_id,
        engineer_name=engineer_name,
        expected_delivery_date=data.expected_delivery_date,
        supervisor_prefix=supervisor_prefix,
        project_code=project_code  # إضافة كود المشروع لرقم الطلب
    )
    
    # Add items
    items_data = [item.model_dump() for item in data.items]
    await request_service.add_request_items(str(request.id), items_data)
    
    # Get items for response
    items = await request_service.get_request_items(str(request.id))
    
    return {
        "message": "تم إنشاء الطلب بنجاح",
        "request": request_to_response(request, items)
    }


@router.get("/pending", response_model=List[RequestResponse])
async def get_pending_requests(
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """الحصول على الطلبات المعلقة"""
    requests = await request_service.get_pending_engineer_requests()
    return await get_requests_with_items_via_service(request_service, requests)


@router.get("/by-status/{status_value}", response_model=List[RequestResponse])
async def get_requests_by_status(
    status_value: str,
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """الحصول على الطلبات حسب الحالة"""
    requests = await request_service.get_requests_by_status(status_value)
    return await get_requests_with_items_via_service(request_service, requests)


@router.get("/by-project/{project_id}", response_model=List[RequestResponse])
async def get_requests_by_project(
    project_id: UUID,
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """الحصول على طلبات مشروع محدد"""
    requests = await request_service.get_requests_by_project(project_id)
    return await get_requests_with_items_via_service(request_service, requests)


@router.get("/{request_id}", response_model=RequestResponse)
async def get_request(
    request_id: UUID,
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """الحصول على طلب محدد مع الأصناف"""
    request = await request_service.get_request(request_id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود"
        )
    
    items = await request_service.get_request_items(str(request.id))
    return request_to_response(request, items)


@router.put("/{request_id}/edit")
async def edit_request(
    request_id: UUID,
    data: RequestUpdate,
    session: AsyncSession = Depends(get_postgres_session),
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """
    تعديل طلب مواد
    Edit a material request
    """
    # Check if request exists
    request = await request_service.get_request(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود"
        )
    
    # Get project info
    project_result = await session.execute(
        select(Project).where(Project.id == data.project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المشروع غير موجود"
        )
    
    # Get engineer info
    engineer_result = await session.execute(
        select(User).where(User.id == data.engineer_id)
    )
    engineer = engineer_result.scalar_one_or_none()
    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المهندس غير موجود"
        )
    
    # Update request
    await request_service.update_request(request_id, {
        "project_id": data.project_id,
        "project_name": project.name,
        "reason": data.reason,
        "engineer_id": data.engineer_id,
        "engineer_name": engineer.name
    })
    
    # Update items
    items_data = [item.model_dump() for item in data.items]
    await request_service.update_request_items(str(request_id), items_data)
    
    # Get updated request
    updated_request = await request_service.get_request(request_id)
    items = await request_service.get_request_items(str(request_id))
    
    return {
        "message": "تم تعديل الطلب بنجاح",
        "request": request_to_response(updated_request, items)
    }


@router.get("/{request_id}/remaining-items")
async def get_remaining_items(
    request_id: UUID,
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """
    الحصول على العناصر المتبقية للطلب (التي لم تُصدر بأوامر شراء بعد)
    Get remaining items for a request (not yet included in purchase orders)
    Includes automatic alias lookup for unlinked items
    """
    from database import MaterialRequestItem, PurchaseOrderItem, PurchaseOrder, ItemAlias
    from sqlalchemy import select, and_
    
    session = request_service.request_repo.session
    
    # Get request
    request = await request_service.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    # Get all request items with catalog_item_id
    items_result = await session.execute(
        select(MaterialRequestItem)
        .where(MaterialRequestItem.request_id == str(request_id))
        .order_by(MaterialRequestItem.item_index)
    )
    request_items = items_result.scalars().all()
    
    # Get all purchase orders for this request
    orders_result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.request_id == str(request_id))
    )
    orders = orders_result.scalars().all()
    
    # Get all PO items and track ordered quantities per item index
    ordered_quantities = {}
    for order in orders:
        po_items_result = await session.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.order_id == order.id)
        )
        for po_item in po_items_result.scalars().all():
            idx = po_item.item_index
            if idx not in ordered_quantities:
                ordered_quantities[idx] = 0
            ordered_quantities[idx] += po_item.quantity
    
    # Calculate remaining items with alias lookup
    remaining_items = []
    for item in request_items:
        ordered = ordered_quantities.get(item.item_index, 0)
        remaining_qty = item.quantity - ordered
        
        if remaining_qty > 0:
            catalog_item_id = item.catalog_item_id
            
            # If no catalog_item_id, look for alias match
            if not catalog_item_id:
                alias_result = await session.execute(
                    select(ItemAlias).where(ItemAlias.alias_name == item.name)
                )
                alias = alias_result.scalar_one_or_none()
                if alias:
                    catalog_item_id = alias.catalog_item_id
            
            remaining_items.append({
                "index": item.item_index,
                "name": item.name,
                "quantity": remaining_qty,
                "original_quantity": item.quantity,
                "ordered_quantity": ordered,
                "unit": item.unit,
                "estimated_price": item.estimated_price,
                "catalog_item_id": catalog_item_id  # Include catalog link from item or alias!
            })
    
    return {
        "request_id": str(request_id),
        "request_number": request.request_number,
        "remaining_items": remaining_items
    }


@router.post("/{request_id}/approve")
async def approve_request(
    request_id: UUID,
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """اعتماد طلب من المهندس"""
    user_id = current_user.get("id") if isinstance(current_user, dict) else str(current_user.id)
    
    request = await request_service.approve_request(request_id, approved_by=user_id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود"
        )
    
    return {"message": "تم اعتماد الطلب بنجاح", "status": request.status}


@router.post("/{request_id}/reject")
async def reject_request(
    request_id: UUID,
    reason: str = "",
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """رفض طلب"""
    user_id = current_user.get("id") if isinstance(current_user, dict) else str(current_user.id)
    
    request = await request_service.reject_request(
        request_id,
        rejected_by=user_id,
        reason=reason
    )
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود"
        )
    
    return {"message": "تم رفض الطلب", "status": request.status}


@router.post("/{request_id}/reject-by-manager")
async def reject_request_by_manager(
    request_id: UUID,
    data: dict,
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """رفض طلب من مدير المشتريات وإعادته للمهندس"""
    user_id = current_user.get("id") if isinstance(current_user, dict) else str(current_user.id)
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    
    # Only procurement_manager or general_manager can reject
    if user_role not in ["procurement_manager", "general_manager", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك برفض الطلبات"
        )
    
    reason = data.get("reason", "")
    
    request = await request_service.update_request(
        request_id,
        {
            "status": "rejected_by_manager",
            "manager_rejection_reason": reason,
            "rejected_by_manager_id": user_id
        }
    )
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود"
        )
    
    return {"message": "تم رفض الطلب وإعادته للمهندس", "status": request.status}


@router.post("/{request_id}/resubmit")
async def resubmit_request(
    request_id: UUID,
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """إعادة إرسال طلب مرفوض"""
    request = await request_service.update_request(
        request_id,
        {"status": "pending_engineer"}
    )
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود"
        )
    
    return {"message": "تم إعادة إرسال الطلب", "status": request.status}


# ==================== Create RFQ from Request ====================

class CreateRFQFromRequestModel(BaseModel):
    supplier_ids: Optional[List[str]] = []
    submission_deadline: Optional[str] = None
    validity_period: int = 30
    payment_terms: Optional[str] = None
    delivery_location: Optional[str] = None
    notes: Optional[str] = None


@router.post("/{request_id}/create-rfq")
async def create_rfq_from_request(
    request_id: UUID,
    data: CreateRFQFromRequestModel,
    request_service: RequestService = Depends(get_request_service),
    current_user = Depends(get_current_user)
):
    """إنشاء طلب عرض سعر (RFQ) من طلب المواد"""
    from database.connection import get_postgres_session
    from app.services.rfq_service import RFQService
    from datetime import datetime
    
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "procurement_manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط مدير المشتريات يمكنه إنشاء طلب عرض سعر"
        )
    
    # Get request details
    request_obj = await request_service.get_request(request_id)
    if not request_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود"
        )
    
    if request_obj.status not in ["approved", "approved_by_engineer", "approved_for_rfq"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="يجب أن يكون الطلب معتمداً لإنشاء طلب عرض سعر"
        )
    
    user_id = current_user.get("id") if isinstance(current_user, dict) else str(current_user.id)
    user_name = current_user.get("name") if isinstance(current_user, dict) else current_user.name
    
    # Get items from request
    items = []
    request_items = await request_service.get_request_items(str(request_id))
    for item in request_items:
        items.append({
            "item_name": item.get("name", ""),
            "quantity": item.get("quantity", 1),
            "unit": item.get("unit", "قطعة"),
            "estimated_price": item.get("estimated_price") or item.get("unit_price")
        })
    
    # Parse deadline
    submission_deadline = None
    if data.submission_deadline:
        try:
            submission_deadline = datetime.fromisoformat(data.submission_deadline.replace('Z', '+00:00'))
        except:
            pass
    
    # Create RFQ
    async for session in get_postgres_session():
        rfq_service = RFQService(session)
        
        result = await rfq_service.create_rfq(
            title=f"طلب عرض سعر - {request_obj.request_number}",
            created_by=user_id,
            created_by_name=user_name,
            description=request_obj.reason or f"طلب عرض سعر مرتبط بالطلب رقم {request_obj.request_number}",
            request_id=str(request_obj.id),
            request_number=request_obj.request_number,
            project_id=str(request_obj.project_id) if request_obj.project_id else None,
            project_name=request_obj.project_name,
            submission_deadline=submission_deadline,
            validity_period=data.validity_period,
            payment_terms=data.payment_terms,
            delivery_location=data.delivery_location,
            notes=data.notes,
            items=items,
            supplier_ids=data.supplier_ids
        )
        
        await session.commit()
        
        return {
            "message": f"تم إنشاء طلب عرض السعر بنجاح",
            "rfq": result
        }

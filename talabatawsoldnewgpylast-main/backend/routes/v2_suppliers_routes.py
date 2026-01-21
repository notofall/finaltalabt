"""
Suppliers API v2 - Using Service Layer (Clean)
API الموردين V2 - باستخدام طبقة الخدمات (نظيف)

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

from database import Supplier

# Import Services via DI
from app.services import SupplierService
from app.dependencies import get_supplier_service
from app.config import PaginationConfig, to_iso_string
from routes.v2_auth_routes import get_current_user


router = APIRouter(prefix="/api/v2/suppliers", tags=["Suppliers V2"])

# Pagination
MAX_LIMIT = PaginationConfig.MAX_PAGE_SIZE
DEFAULT_LIMIT = PaginationConfig.DEFAULT_PAGE_SIZE


# ==================== Schemas ====================

class SupplierCreate(BaseModel):
    name: str
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    notes: str = ""


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class SupplierResponse(BaseModel):
    id: str
    name: str
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    created_at: Optional[str]
    total_orders: int = 0
    total_amount: float = 0

    class Config:
        from_attributes = True


class SuppliersListResponse(BaseModel):
    """Paginated suppliers response"""
    items: List[SupplierResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


# ==================== Helper ====================

def supplier_to_response(supplier: Supplier, stats: dict = None) -> dict:
    """Convert Supplier model to response dict"""
    base = {
        "id": str(supplier.id),
        "name": supplier.name,
        "contact_person": supplier.contact_person,
        "phone": supplier.phone,
        "email": supplier.email,
        "address": supplier.address,
        "notes": supplier.notes,
        "created_at": to_iso_string(supplier.created_at),
    }
    if stats:
        base.update(stats)
    else:
        base["total_orders"] = 0
        base["total_amount"] = 0
    return base


# ==================== Routes ====================

@router.get("/", response_model=SuppliersListResponse)
async def get_all_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user = Depends(get_current_user)
):
    """
    الحصول على جميع الموردين
    Uses: SupplierService -> SupplierRepository
    Real pagination with total count
    """
    limit = min(limit, MAX_LIMIT)
    
    # Get total count
    total = await supplier_service.count_suppliers()
    
    suppliers = await supplier_service.get_all_suppliers(skip, limit)
    items = [supplier_to_response(s) for s in suppliers]
    
    return SuppliersListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(items)) < total
    )


@router.get("/active", response_model=List[SupplierResponse])
async def get_active_suppliers(
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user = Depends(get_current_user)
):
    """الحصول على الموردين النشطين"""
    suppliers = await supplier_service.get_active_suppliers()
    return [supplier_to_response(s) for s in suppliers]


@router.get("/summary")
async def get_suppliers_summary(
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user = Depends(get_current_user)
):
    """الحصول على ملخص الموردين"""
    return await supplier_service.get_suppliers_summary()


@router.get("/search")
async def search_suppliers(
    q: str,
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user = Depends(get_current_user)
):
    """البحث عن موردين"""
    suppliers = await supplier_service.search_suppliers(q)
    return [supplier_to_response(s) for s in suppliers]


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: UUID,
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user = Depends(get_current_user)
):
    """الحصول على مورد محدد"""
    supplier = await supplier_service.get_supplier(supplier_id)
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المورد غير موجود"
        )
    
    return supplier_to_response(supplier)


@router.post("/", response_model=SupplierResponse)
async def create_supplier(
    supplier_data: SupplierCreate,
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user = Depends(get_current_user)
):
    """إنشاء مورد جديد"""
    supplier = await supplier_service.create_supplier(
        name=supplier_data.name,
        contact_person=supplier_data.contact_person,
        phone=supplier_data.phone,
        email=supplier_data.email,
        address=supplier_data.address
    )
    
    return supplier_to_response(supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user = Depends(get_current_user)
):
    """تحديث مورد"""
    update_data = {k: v for k, v in supplier_data.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا توجد بيانات للتحديث"
        )
    
    supplier = await supplier_service.update_supplier(supplier_id, update_data)
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المورد غير موجود"
        )
    
    return supplier_to_response(supplier)


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: UUID,
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user = Depends(get_current_user)
):
    """حذف مورد"""
    success = await supplier_service.delete_supplier(supplier_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المورد غير موجود"
        )
    
    return {"message": "تم حذف المورد بنجاح"}

"""
V2 RFQ Routes - طلبات عروض الأسعار
/api/v2/rfq/*
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_postgres_session
from routes.v2_auth_routes import get_current_user
from app.services.rfq_service import RFQService
from app.services.pdf_generator import generate_rfq_pdf

router = APIRouter(prefix="/api/v2/rfq", tags=["RFQ - طلبات عروض الأسعار"])


# ==================== Pydantic Models ====================

class RFQItemCreate(BaseModel):
    item_name: str
    item_code: Optional[str] = None
    description: Optional[str] = None
    quantity: float = 1
    unit: str = "قطعة"
    catalog_item_id: Optional[str] = None
    estimated_price: Optional[float] = None


class RFQCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    validity_period: int = 30
    payment_terms: Optional[str] = None
    delivery_location: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[RFQItemCreate]] = []
    supplier_ids: Optional[List[str]] = []


class RFQUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    validity_period: Optional[int] = None
    payment_terms: Optional[str] = None
    delivery_location: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None


class QuotationItemCreate(BaseModel):
    rfq_item_id: str
    item_name: str
    item_code: Optional[str] = None
    quantity: float
    unit: str = "قطعة"
    unit_price: float
    notes: Optional[str] = None


class SupplierQuotationCreate(BaseModel):
    supplier_id: str
    items: List[QuotationItemCreate]
    discount_percentage: float = 0
    vat_percentage: float = 15
    validity_date: Optional[datetime] = None
    delivery_days: Optional[int] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class WhatsAppRequest(BaseModel):
    company_name: str = "شركتنا"


# ==================== RFQ Endpoints ====================

@router.get("/stats")
async def get_rfq_stats(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get RFQ statistics"""
    if current_user.role not in ["procurement_manager", "general_manager", "system_admin"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بعرض الإحصائيات")
    
    service = RFQService(session)
    return await service.get_stats()


@router.get("/")
async def get_all_rfqs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get all RFQs with pagination and filters"""
    if current_user.role not in ["procurement_manager", "general_manager", "system_admin"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بعرض طلبات عروض الأسعار")
    
    service = RFQService(session)
    return await service.get_all_rfqs(skip, limit, status, project_id)


@router.post("/")
async def create_rfq(
    rfq_data: RFQCreate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Create new RFQ"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه إنشاء طلب عرض سعر")
    
    service = RFQService(session)
    
    items = [item.model_dump() for item in rfq_data.items] if rfq_data.items else None
    
    result = await service.create_rfq(
        title=rfq_data.title,
        created_by=str(current_user.id),
        created_by_name=current_user.name,
        description=rfq_data.description,
        project_id=rfq_data.project_id,
        project_name=rfq_data.project_name,
        submission_deadline=rfq_data.submission_deadline,
        validity_period=rfq_data.validity_period,
        payment_terms=rfq_data.payment_terms,
        delivery_location=rfq_data.delivery_location,
        delivery_terms=rfq_data.delivery_terms,
        notes=rfq_data.notes,
        items=items,
        supplier_ids=rfq_data.supplier_ids
    )
    
    return result


@router.get("/{rfq_id}")
async def get_rfq_details(
    rfq_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get RFQ details with items and suppliers"""
    if current_user.role not in ["procurement_manager", "general_manager", "system_admin"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بعرض التفاصيل")
    
    service = RFQService(session)
    result = await service.get_rfq_details(rfq_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="طلب عرض السعر غير موجود")
    
    return result


@router.put("/{rfq_id}")
async def update_rfq(
    rfq_id: str,
    update_data: RFQUpdate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Update RFQ"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه تعديل طلب عرض السعر")
    
    service = RFQService(session)
    
    # Filter out None values
    data = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    result = await service.update_rfq(rfq_id, data)
    
    if not result:
        raise HTTPException(status_code=404, detail="طلب عرض السعر غير موجود")
    
    return result


@router.delete("/{rfq_id}")
async def delete_rfq(
    rfq_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Delete RFQ"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه حذف طلب عرض السعر")
    
    service = RFQService(session)
    success = await service.delete_rfq(rfq_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="طلب عرض السعر غير موجود")
    
    return {"message": "تم حذف طلب عرض السعر بنجاح"}


@router.post("/{rfq_id}/send")
async def send_rfq(
    rfq_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Mark RFQ as sent"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه إرسال طلب عرض السعر")
    
    service = RFQService(session)
    result = await service.send_rfq(rfq_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="طلب عرض السعر غير موجود")
    
    return result


@router.post("/{rfq_id}/close")
async def close_rfq(
    rfq_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Close RFQ"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه إغلاق طلب عرض السعر")
    
    service = RFQService(session)
    result = await service.close_rfq(rfq_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="طلب عرض السعر غير موجود")
    
    return result


# ==================== RFQ Items Endpoints ====================

@router.post("/{rfq_id}/items")
async def add_rfq_item(
    rfq_id: str,
    item: RFQItemCreate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Add item to RFQ"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه إضافة أصناف")
    
    service = RFQService(session)
    result = await service.add_item_to_rfq(
        rfq_id=rfq_id,
        item_name=item.item_name,
        quantity=item.quantity,
        unit=item.unit,
        item_code=item.item_code,
        description=item.description,
        catalog_item_id=item.catalog_item_id,
        estimated_price=item.estimated_price
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="طلب عرض السعر غير موجود")
    
    return result


@router.put("/items/{item_id}")
async def update_rfq_item(
    item_id: str,
    item: RFQItemCreate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Update RFQ item"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه تعديل الأصناف")
    
    service = RFQService(session)
    result = await service.update_rfq_item(item_id, item.model_dump())
    
    if not result:
        raise HTTPException(status_code=404, detail="الصنف غير موجود")
    
    return result


@router.delete("/items/{item_id}")
async def delete_rfq_item(
    item_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Delete RFQ item"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه حذف الأصناف")
    
    service = RFQService(session)
    success = await service.delete_rfq_item(item_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="الصنف غير موجود")
    
    return {"message": "تم حذف الصنف بنجاح"}


# ==================== RFQ Suppliers Endpoints ====================

@router.post("/{rfq_id}/suppliers/{supplier_id}")
async def add_supplier_to_rfq(
    rfq_id: str,
    supplier_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Add supplier to RFQ"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه إضافة موردين")
    
    service = RFQService(session)
    result = await service.add_supplier_to_rfq(rfq_id, supplier_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="طلب عرض السعر أو المورد غير موجود")
    
    return result


@router.delete("/suppliers/{rfq_supplier_id}")
async def remove_supplier_from_rfq(
    rfq_supplier_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Remove supplier from RFQ"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه إزالة الموردين")
    
    service = RFQService(session)
    success = await service.remove_supplier_from_rfq(rfq_supplier_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="المورد غير موجود")
    
    return {"message": "تم إزالة المورد بنجاح"}


@router.post("/suppliers/{rfq_supplier_id}/whatsapp-sent")
async def mark_whatsapp_sent(
    rfq_supplier_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Mark supplier as sent via WhatsApp"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه تحديث حالة الإرسال")
    
    service = RFQService(session)
    result = await service.mark_whatsapp_sent(rfq_supplier_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="المورد غير موجود")
    
    return result


@router.get("/{rfq_id}/whatsapp-link/{supplier_id}")
async def get_whatsapp_link(
    rfq_id: str,
    supplier_id: str,
    company_name: str = Query("شركتنا"),
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Generate WhatsApp link for supplier"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه إنشاء روابط واتساب")
    
    service = RFQService(session)
    
    rfq = await service.get_rfq_details(rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="طلب عرض السعر غير موجود")
    
    # Find supplier phone
    supplier_phone = None
    for s in rfq["suppliers"]:
        if s["supplier_id"] == supplier_id:
            supplier_phone = s["supplier_phone"]
            break
    
    if not supplier_phone:
        raise HTTPException(status_code=404, detail="رقم هاتف المورد غير متوفر")
    
    link = service.generate_whatsapp_link(
        phone=supplier_phone,
        rfq_number=rfq["rfq_number"],
        title=rfq["title"],
        company_name=company_name
    )
    
    return {"whatsapp_link": link}


# ==================== Supplier Quotations Endpoints ====================

@router.post("/{rfq_id}/quotations")
async def create_supplier_quotation(
    rfq_id: str,
    quotation: SupplierQuotationCreate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Create supplier quotation for RFQ"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه إدخال عروض الأسعار")
    
    service = RFQService(session)
    
    items = [item.model_dump() for item in quotation.items]
    
    result = await service.create_supplier_quotation(
        rfq_id=rfq_id,
        supplier_id=quotation.supplier_id,
        entered_by=str(current_user.id),
        entered_by_name=current_user.name,
        items=items,
        discount_percentage=quotation.discount_percentage,
        vat_percentage=quotation.vat_percentage,
        validity_date=quotation.validity_date,
        delivery_days=quotation.delivery_days,
        payment_terms=quotation.payment_terms,
        notes=quotation.notes
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="طلب عرض السعر أو المورد غير موجود")
    
    return result


@router.get("/quotations/{quotation_id}")
async def get_quotation_details(
    quotation_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get supplier quotation details"""
    if current_user.role not in ["procurement_manager", "general_manager", "system_admin"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بعرض التفاصيل")
    
    service = RFQService(session)
    result = await service.get_quotation_details(quotation_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="عرض السعر غير موجود")
    
    return result


@router.post("/quotations/{quotation_id}/accept")
async def accept_quotation(
    quotation_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Accept supplier quotation"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه قبول عروض الأسعار")
    
    service = RFQService(session)
    result = await service.accept_quotation(quotation_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="عرض السعر غير موجود")
    
    return {"message": "تم قبول عرض السعر", "status": "accepted"}


@router.post("/quotations/{quotation_id}/reject")
async def reject_quotation(
    quotation_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Reject supplier quotation"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه رفض عروض الأسعار")
    
    service = RFQService(session)
    result = await service.reject_quotation(quotation_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="عرض السعر غير موجود")
    
    return {"message": "تم رفض عرض السعر", "status": "rejected"}


# ==================== Approve & Create Order ====================

class ApproveQuotationRequest(BaseModel):
    pass  # No additional fields needed for approval


class CreateOrderFromQuotationRequest(BaseModel):
    notes: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    update_catalog: bool = True


@router.post("/quotations/{quotation_id}/approve")
async def approve_quotation_as_winner(
    quotation_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Approve quotation as winner - marks this as the winning bid"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه اعتماد العرض الفائز")
    
    service = RFQService(session)
    result = await service.approve_quotation(
        quotation_id=quotation_id,
        approved_by=str(current_user.id),
        approved_by_name=current_user.name
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="عرض السعر غير موجود")
    
    return {
        "message": "تم اعتماد العرض كفائز",
        "quotation": result
    }


@router.post("/quotations/{quotation_id}/create-order")
async def create_order_from_quotation(
    quotation_id: str,
    request_data: CreateOrderFromQuotationRequest,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Create purchase order from approved quotation and update catalog prices"""
    if current_user.role != "procurement_manager":
        raise HTTPException(status_code=403, detail="فقط مدير المشتريات يمكنه إصدار أمر الشراء")
    
    service = RFQService(session)
    result = await service.create_order_from_quotation(
        quotation_id=quotation_id,
        created_by=str(current_user.id),
        created_by_name=current_user.name,
        notes=request_data.notes,
        expected_delivery_date=request_data.expected_delivery_date,
        update_catalog=request_data.update_catalog
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="عرض السعر غير موجود")
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


# ==================== Comparison Endpoint ====================

@router.get("/{rfq_id}/compare")
async def compare_quotations(
    rfq_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Compare all quotations for an RFQ"""
    if current_user.role not in ["procurement_manager", "general_manager", "system_admin"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بمقارنة العروض")
    
    service = RFQService(session)
    return await service.compare_quotations(rfq_id)


# ==================== PDF Export Endpoint ====================

@router.get("/{rfq_id}/pdf")
async def download_rfq_pdf(
    rfq_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Download RFQ as PDF"""
    if current_user.role not in ["procurement_manager", "general_manager", "system_admin"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بتحميل الملف")
    
    service = RFQService(session)
    rfq = await service.get_rfq_details(rfq_id)
    
    if not rfq:
        raise HTTPException(status_code=404, detail="طلب عرض السعر غير موجود")
    
    # Get company settings (optional)
    company_settings = None
    try:
        from app.services.settings_service import SettingsService
        from app.repositories.settings_repository import SettingsRepository
        settings_repo = SettingsRepository(session)
        settings_service = SettingsService(settings_repo)
        company_settings = await settings_service.get_company_settings()
    except Exception as e:
        print(f"Could not load company settings: {e}")
    
    # Generate PDF
    pdf_buffer = generate_rfq_pdf(rfq, company_settings)
    
    filename = f"RFQ-{rfq['rfq_number']}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/{rfq_id}/compare/pdf")
async def download_comparison_pdf(
    rfq_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Download quotation comparison as PDF"""
    if current_user.role not in ["procurement_manager", "general_manager", "system_admin"]:
        raise HTTPException(status_code=403, detail="غير مصرح لك بتحميل الملف")
    
    service = RFQService(session)
    
    # Get comparison data
    comparison = await service.compare_quotations(rfq_id)
    
    if not comparison or "error" in comparison:
        raise HTTPException(status_code=404, detail="لا توجد بيانات للمقارنة")
    
    # Get RFQ details for additional info
    rfq = await service.get_rfq_details(rfq_id)
    if rfq:
        comparison['rfq_number'] = rfq.get('rfq_number', '')
        comparison['rfq_title'] = rfq.get('title', '')
    
    # Get company settings (optional)
    company_settings = None
    try:
        from app.services.settings_service import SettingsService
        from app.repositories.settings_repository import SettingsRepository
        settings_repo = SettingsRepository(session)
        settings_service = SettingsService(settings_repo)
        company_settings = await settings_service.get_company_settings()
    except Exception as e:
        print(f"Could not load company settings: {e}")
    
    # Generate PDF
    from app.services.pdf_generator import generate_comparison_pdf
    pdf_buffer = generate_comparison_pdf(comparison, company_settings)
    
    rfq_number = comparison.get('rfq_number', rfq_id)
    filename = f"Comparison-{rfq_number}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

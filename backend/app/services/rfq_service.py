"""
RFQ Service - طبقة منطق العمل لنظام طلبات عروض الأسعار
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.repositories.rfq_repository import RFQRepository
from app.services.base import BaseService


class RFQService(BaseService):
    """Service for RFQ business logic"""
    
    def __init__(self, session: AsyncSession):
        self.repository = RFQRepository(session)
        self.session = session
    
    # ==================== RFQ Operations ====================
    
    async def create_rfq(
        self,
        title: str,
        created_by: str,
        created_by_name: str,
        description: Optional[str] = None,
        request_id: Optional[str] = None,
        request_number: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        submission_deadline: Optional[datetime] = None,
        validity_period: int = 30,
        payment_terms: Optional[str] = None,
        delivery_location: Optional[str] = None,
        delivery_terms: Optional[str] = None,
        notes: Optional[str] = None,
        items: Optional[List[Dict]] = None,
        supplier_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create new RFQ with items and suppliers"""
        
        # Generate RFQ number
        rfq_number = await self.repository.get_next_rfq_number()
        
        # Create RFQ
        rfq_data = {
            "id": str(uuid.uuid4()),
            "rfq_number": rfq_number,
            "title": title,
            "description": description,
            "request_id": request_id,
            "request_number": request_number,
            "project_id": project_id,
            "project_name": project_name,
            "status": "draft",
            "submission_deadline": submission_deadline,
            "validity_period": validity_period,
            "payment_terms": payment_terms,
            "delivery_location": delivery_location,
            "delivery_terms": delivery_terms,
            "notes": notes,
            "created_by": created_by,
            "created_by_name": created_by_name,
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None)
        }
        
        rfq = await self.repository.create_rfq(rfq_data)
        
        # Add items
        if items:
            for idx, item in enumerate(items):
                item_data = {
                    "id": str(uuid.uuid4()),
                    "rfq_id": rfq.id,
                    "item_name": item.get("item_name"),
                    "item_code": item.get("item_code"),
                    "description": item.get("description"),
                    "quantity": item.get("quantity", 1),
                    "unit": item.get("unit", "قطعة"),
                    "catalog_item_id": item.get("catalog_item_id"),
                    "estimated_price": item.get("estimated_price"),
                    "item_index": idx
                }
                await self.repository.add_rfq_item(item_data)
        
        # Add suppliers
        if supplier_ids:
            for supplier_id in supplier_ids:
                supplier = await self.repository.get_supplier_by_id(supplier_id)
                if supplier:
                    supplier_data = {
                        "id": str(uuid.uuid4()),
                        "rfq_id": rfq.id,
                        "supplier_id": supplier_id,
                        "supplier_name": supplier.name,
                        "supplier_phone": supplier.phone,
                        "supplier_email": supplier.email
                    }
                    await self.repository.add_rfq_supplier(supplier_data)
        
        return await self.get_rfq_details(rfq.id)
    
    async def get_rfq_details(self, rfq_id: str) -> Optional[Dict[str, Any]]:
        """Get RFQ with all details (items and suppliers)"""
        rfq = await self.repository.get_rfq_by_id(rfq_id)
        if not rfq:
            return None
        
        items = await self.repository.get_rfq_items(rfq_id)
        suppliers = await self.repository.get_rfq_suppliers(rfq_id)
        quotations = await self.repository.get_quotations_by_rfq(rfq_id)
        
        return {
            "id": rfq.id,
            "rfq_number": rfq.rfq_number,
            "title": rfq.title,
            "description": rfq.description,
            "project_id": rfq.project_id,
            "project_name": rfq.project_name,
            "status": rfq.status,
            "submission_deadline": rfq.submission_deadline.isoformat() if rfq.submission_deadline else None,
            "validity_period": rfq.validity_period,
            "payment_terms": rfq.payment_terms,
            "delivery_location": rfq.delivery_location,
            "delivery_terms": rfq.delivery_terms,
            "notes": rfq.notes,
            "created_by": rfq.created_by,
            "created_by_name": rfq.created_by_name,
            "created_at": rfq.created_at.isoformat() if rfq.created_at else None,
            "updated_at": rfq.updated_at.isoformat() if rfq.updated_at else None,
            "sent_at": rfq.sent_at.isoformat() if rfq.sent_at else None,
            "closed_at": rfq.closed_at.isoformat() if rfq.closed_at else None,
            "request_id": rfq.request_id if hasattr(rfq, 'request_id') else None,
            "request_number": rfq.request_number if hasattr(rfq, 'request_number') else None,
            "items": [
                {
                    "id": item.id,
                    "item_name": item.item_name,
                    "item_code": item.item_code,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "catalog_item_id": item.catalog_item_id,
                    "estimated_price": item.estimated_price,
                    "item_index": item.item_index
                }
                for item in items
            ],
            "suppliers": [
                {
                    "id": s.id,
                    "supplier_id": s.supplier_id,
                    "supplier_name": s.supplier_name,
                    "supplier_phone": s.supplier_phone,
                    "supplier_email": s.supplier_email,
                    "sent_via_whatsapp": s.sent_via_whatsapp,
                    "sent_at": s.sent_at.isoformat() if s.sent_at else None,
                    "quotation_received": s.quotation_received
                }
                for s in suppliers
            ],
            "quotations_count": len(quotations),
            "quotations": [
                {
                    "id": q.id,
                    "quotation_number": q.quotation_number,
                    "supplier_id": q.supplier_id,
                    "supplier_name": q.supplier_name,
                    "status": q.status,
                    "final_amount": q.final_amount,
                    "delivery_days": q.delivery_days,
                    "is_winner": q.is_winner if hasattr(q, 'is_winner') else False,
                    "order_id": q.order_id if hasattr(q, 'order_id') else None,
                    "order_number": q.order_number if hasattr(q, 'order_number') else None,
                    "created_at": q.created_at.isoformat() if q.created_at else None
                }
                for q in quotations
            ]
        }
    
    async def get_all_rfqs(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all RFQs with pagination"""
        rfqs = await self.repository.get_all_rfqs(skip, limit, status, project_id)
        total = await self.repository.count_rfqs(status, project_id)
        
        items = []
        for rfq in rfqs:
            rfq_suppliers = await self.repository.get_rfq_suppliers(rfq.id)
            rfq_items = await self.repository.get_rfq_items(rfq.id)
            quotations = await self.repository.get_quotations_by_rfq(rfq.id)
            
            items.append({
                "id": rfq.id,
                "rfq_number": rfq.rfq_number,
                "title": rfq.title,
                "project_name": rfq.project_name,
                "status": rfq.status,
                "submission_deadline": rfq.submission_deadline.isoformat() if rfq.submission_deadline else None,
                "created_at": rfq.created_at.isoformat() if rfq.created_at else None,
                "items_count": len(rfq_items),
                "suppliers_count": len(rfq_suppliers),
                "quotations_count": len(quotations)
            })
        
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total
        }
    
    async def update_rfq(
        self,
        rfq_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update RFQ"""
        rfq = await self.repository.update_rfq(rfq_id, update_data)
        if not rfq:
            return None
        return await self.get_rfq_details(rfq_id)
    
    async def delete_rfq(self, rfq_id: str) -> bool:
        """Delete RFQ"""
        return await self.repository.delete_rfq(rfq_id)
    
    async def send_rfq(self, rfq_id: str) -> Optional[Dict[str, Any]]:
        """Mark RFQ as sent"""
        update_data = {
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).replace(tzinfo=None)
        }
        return await self.update_rfq(rfq_id, update_data)
    
    async def close_rfq(self, rfq_id: str) -> Optional[Dict[str, Any]]:
        """Close RFQ"""
        update_data = {
            "status": "closed",
            "closed_at": datetime.now(timezone.utc).replace(tzinfo=None)
        }
        return await self.update_rfq(rfq_id, update_data)
    
    # ==================== RFQ Items ====================
    
    async def add_item_to_rfq(
        self,
        rfq_id: str,
        item_name: str,
        quantity: float,
        unit: str = "قطعة",
        item_code: Optional[str] = None,
        description: Optional[str] = None,
        catalog_item_id: Optional[str] = None,
        estimated_price: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Add item to RFQ"""
        rfq = await self.repository.get_rfq_by_id(rfq_id)
        if not rfq:
            return None
        
        # Get current items to determine index
        items = await self.repository.get_rfq_items(rfq_id)
        
        item_data = {
            "id": str(uuid.uuid4()),
            "rfq_id": rfq_id,
            "item_name": item_name,
            "item_code": item_code,
            "description": description,
            "quantity": quantity,
            "unit": unit,
            "catalog_item_id": catalog_item_id,
            "estimated_price": estimated_price,
            "item_index": len(items)
        }
        
        item = await self.repository.add_rfq_item(item_data)
        return {
            "id": item.id,
            "item_name": item.item_name,
            "item_code": item.item_code,
            "description": item.description,
            "quantity": item.quantity,
            "unit": item.unit,
            "catalog_item_id": item.catalog_item_id,
            "estimated_price": item.estimated_price,
            "item_index": item.item_index
        }
    
    async def update_rfq_item(
        self,
        item_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update RFQ item"""
        item = await self.repository.update_rfq_item(item_id, update_data)
        if not item:
            return None
        return {
            "id": item.id,
            "item_name": item.item_name,
            "item_code": item.item_code,
            "description": item.description,
            "quantity": item.quantity,
            "unit": item.unit,
            "catalog_item_id": item.catalog_item_id,
            "estimated_price": item.estimated_price,
            "item_index": item.item_index
        }
    
    async def delete_rfq_item(self, item_id: str) -> bool:
        """Delete RFQ item"""
        return await self.repository.delete_rfq_item(item_id)
    
    # ==================== RFQ Suppliers ====================
    
    async def add_supplier_to_rfq(
        self,
        rfq_id: str,
        supplier_id: str
    ) -> Optional[Dict[str, Any]]:
        """Add supplier to RFQ"""
        rfq = await self.repository.get_rfq_by_id(rfq_id)
        if not rfq:
            return None
        
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            return None
        
        supplier_data = {
            "id": str(uuid.uuid4()),
            "rfq_id": rfq_id,
            "supplier_id": supplier_id,
            "supplier_name": supplier.name,
            "supplier_phone": supplier.phone,
            "supplier_email": supplier.email
        }
        
        rfq_supplier = await self.repository.add_rfq_supplier(supplier_data)
        return {
            "id": rfq_supplier.id,
            "supplier_id": rfq_supplier.supplier_id,
            "supplier_name": rfq_supplier.supplier_name,
            "supplier_phone": rfq_supplier.supplier_phone,
            "supplier_email": rfq_supplier.supplier_email,
            "sent_via_whatsapp": rfq_supplier.sent_via_whatsapp,
            "quotation_received": rfq_supplier.quotation_received
        }
    
    async def mark_whatsapp_sent(
        self,
        rfq_supplier_id: str
    ) -> Optional[Dict[str, Any]]:
        """Mark supplier as sent via WhatsApp"""
        update_data = {
            "sent_via_whatsapp": True,
            "sent_at": datetime.now(timezone.utc).replace(tzinfo=None)
        }
        supplier = await self.repository.update_rfq_supplier(rfq_supplier_id, update_data)
        if not supplier:
            return None
        
        # Update RFQ status to sent if not already
        rfq = await self.repository.get_rfq_by_id(supplier.rfq_id)
        if rfq and rfq.status == "draft":
            await self.repository.update_rfq(rfq.id, {
                "status": "sent",
                "sent_at": datetime.now(timezone.utc).replace(tzinfo=None)
            })
        
        return {
            "id": supplier.id,
            "supplier_id": supplier.supplier_id,
            "supplier_name": supplier.supplier_name,
            "sent_via_whatsapp": supplier.sent_via_whatsapp,
            "sent_at": supplier.sent_at.isoformat() if supplier.sent_at else None
        }
    
    async def remove_supplier_from_rfq(self, rfq_supplier_id: str) -> bool:
        """Remove supplier from RFQ"""
        return await self.repository.remove_rfq_supplier(rfq_supplier_id)
    
    # ==================== Supplier Quotations ====================
    
    async def create_supplier_quotation(
        self,
        rfq_id: str,
        supplier_id: str,
        entered_by: str,
        entered_by_name: str,
        items: List[Dict],
        discount_percentage: float = 0,
        vat_percentage: float = 15,
        validity_date: Optional[datetime] = None,
        delivery_days: Optional[int] = None,
        payment_terms: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create supplier quotation for an RFQ"""
        rfq = await self.repository.get_rfq_by_id(rfq_id)
        if not rfq:
            return None
        
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            return None
        
        # Calculate totals
        total_amount = sum(item.get("unit_price", 0) * item.get("quantity", 0) for item in items)
        discount_amount = total_amount * (discount_percentage / 100)
        subtotal = total_amount - discount_amount
        vat_amount = subtotal * (vat_percentage / 100)
        final_amount = subtotal + vat_amount
        
        # Generate quotation number
        quotation_number = await self.repository.get_next_quotation_number()
        
        quotation_data = {
            "id": str(uuid.uuid4()),
            "quotation_number": quotation_number,
            "rfq_id": rfq_id,
            "rfq_number": rfq.rfq_number,
            "supplier_id": supplier_id,
            "supplier_name": supplier.name,
            "status": "pending",
            "total_amount": total_amount,
            "discount_percentage": discount_percentage,
            "discount_amount": discount_amount,
            "vat_percentage": vat_percentage,
            "vat_amount": vat_amount,
            "final_amount": final_amount,
            "validity_date": validity_date,
            "delivery_days": delivery_days,
            "payment_terms": payment_terms,
            "notes": notes,
            "entered_by": entered_by,
            "entered_by_name": entered_by_name,
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None)
        }
        
        quotation = await self.repository.create_supplier_quotation(quotation_data)
        
        # Add items
        for item in items:
            item_data = {
                "id": str(uuid.uuid4()),
                "quotation_id": quotation.id,
                "rfq_item_id": item.get("rfq_item_id"),
                "item_name": item.get("item_name"),
                "item_code": item.get("item_code"),
                "quantity": item.get("quantity", 1),
                "unit": item.get("unit", "قطعة"),
                "unit_price": item.get("unit_price", 0),
                "total_price": item.get("unit_price", 0) * item.get("quantity", 1),
                "notes": item.get("notes")
            }
            await self.repository.add_quotation_item(item_data)
        
        # Update RFQ supplier status
        rfq_suppliers = await self.repository.get_rfq_suppliers(rfq_id)
        for s in rfq_suppliers:
            if s.supplier_id == supplier_id:
                await self.repository.update_rfq_supplier(s.id, {"quotation_received": True})
                break
        
        # Update RFQ status to received
        if rfq.status in ["draft", "sent"]:
            await self.repository.update_rfq(rfq_id, {"status": "received"})
        
        return await self.get_quotation_details(quotation.id)
    
    async def get_quotation_details(self, quotation_id: str) -> Optional[Dict[str, Any]]:
        """Get supplier quotation details"""
        quotation = await self.repository.get_supplier_quotation_by_id(quotation_id)
        if not quotation:
            return None
        
        items = await self.repository.get_quotation_items(quotation_id)
        
        return {
            "id": quotation.id,
            "quotation_number": quotation.quotation_number,
            "rfq_id": quotation.rfq_id,
            "rfq_number": quotation.rfq_number,
            "supplier_id": quotation.supplier_id,
            "supplier_name": quotation.supplier_name,
            "status": quotation.status,
            "total_amount": quotation.total_amount,
            "discount_percentage": quotation.discount_percentage,
            "discount_amount": quotation.discount_amount,
            "vat_percentage": quotation.vat_percentage,
            "vat_amount": quotation.vat_amount,
            "final_amount": quotation.final_amount,
            "validity_date": quotation.validity_date.isoformat() if quotation.validity_date else None,
            "delivery_days": quotation.delivery_days,
            "payment_terms": quotation.payment_terms,
            "notes": quotation.notes,
            "entered_by": quotation.entered_by,
            "entered_by_name": quotation.entered_by_name,
            "is_winner": quotation.is_winner if hasattr(quotation, 'is_winner') else False,
            "approved_at": quotation.approved_at.isoformat() if hasattr(quotation, 'approved_at') and quotation.approved_at else None,
            "approved_by_name": quotation.approved_by_name if hasattr(quotation, 'approved_by_name') else None,
            "order_id": quotation.order_id if hasattr(quotation, 'order_id') else None,
            "order_number": quotation.order_number if hasattr(quotation, 'order_number') else None,
            "created_at": quotation.created_at.isoformat() if quotation.created_at else None,
            "items": [
                {
                    "id": item.id,
                    "rfq_item_id": item.rfq_item_id,
                    "item_name": item.item_name,
                    "item_code": item.item_code,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "notes": item.notes
                }
                for item in items
            ]
        }
    
    async def accept_quotation(self, quotation_id: str) -> Optional[Dict[str, Any]]:
        """Accept a supplier quotation"""
        return await self.repository.update_supplier_quotation(
            quotation_id, 
            {"status": "accepted", "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)}
        )
    
    async def reject_quotation(self, quotation_id: str) -> Optional[Dict[str, Any]]:
        """Reject a supplier quotation"""
        return await self.repository.update_supplier_quotation(
            quotation_id,
            {"status": "rejected", "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)}
        )
    
    # ==================== Comparison ====================
    
    async def compare_quotations(self, rfq_id: str) -> Dict[str, Any]:
        """Compare all quotations for an RFQ"""
        rfq = await self.repository.get_rfq_by_id(rfq_id)
        if not rfq:
            return {"error": "RFQ not found"}
        
        rfq_items = await self.repository.get_rfq_items(rfq_id)
        quotations = await self.repository.get_quotations_by_rfq(rfq_id)
        
        # Build comparison matrix
        comparison = {
            "rfq_id": rfq_id,
            "rfq_number": rfq.rfq_number,
            "rfq_title": rfq.title,
            "items": [],
            "suppliers": [],
            "summary": {
                "lowest_total": None,
                "lowest_supplier": None,
                "highest_total": None,
                "highest_supplier": None
            }
        }
        
        # Get supplier info
        for q in quotations:
            q_items = await self.repository.get_quotation_items(q.id)
            comparison["suppliers"].append({
                "quotation_id": q.id,
                "supplier_id": q.supplier_id,
                "supplier_name": q.supplier_name,
                "final_amount": q.final_amount,
                "delivery_days": q.delivery_days,
                "status": q.status
            })
        
        # Build item comparison
        for rfq_item in rfq_items:
            item_comparison = {
                "item_id": rfq_item.id,
                "item_name": rfq_item.item_name,
                "item_code": rfq_item.item_code,
                "quantity": rfq_item.quantity,
                "unit": rfq_item.unit,
                "estimated_price": rfq_item.estimated_price,
                "prices": []
            }
            
            for q in quotations:
                q_items = await self.repository.get_quotation_items(q.id)
                price_info = {
                    "supplier_name": q.supplier_name,
                    "unit_price": None,
                    "total_price": None
                }
                
                for qi in q_items:
                    if qi.rfq_item_id == rfq_item.id:
                        price_info["unit_price"] = qi.unit_price
                        price_info["total_price"] = qi.total_price
                        break
                
                item_comparison["prices"].append(price_info)
            
            comparison["items"].append(item_comparison)
        
        # Summary
        comparison["summary"]["total_quotations"] = len(quotations)
        
        if quotations:
            sorted_quotes = sorted(quotations, key=lambda x: x.final_amount)
            comparison["summary"]["lowest_total"] = sorted_quotes[0].final_amount
            comparison["summary"]["lowest_supplier"] = sorted_quotes[0].supplier_name
            comparison["summary"]["highest_total"] = sorted_quotes[-1].final_amount
            comparison["summary"]["highest_supplier"] = sorted_quotes[-1].supplier_name
        
        return comparison
    
    # ==================== Statistics ====================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get RFQ statistics"""
        return await self.repository.get_rfq_stats()
    
    # ==================== WhatsApp Link Generation ====================
    
    def generate_whatsapp_link(
        self,
        phone: str,
        rfq_number: str,
        title: str,
        company_name: str = "شركتنا"
    ) -> str:
        """Generate WhatsApp link for sending RFQ"""
        # Clean phone number
        clean_phone = phone.replace(" ", "").replace("-", "").replace("+", "")
        if clean_phone.startswith("0"):
            clean_phone = "966" + clean_phone[1:]  # Saudi Arabia code
        elif not clean_phone.startswith("966"):
            clean_phone = "966" + clean_phone
        
        # Message template
        message = f"""السلام عليكم ورحمة الله وبركاته

نود إشعاركم بأنه تم إرسال طلب عرض سعر رقم: {rfq_number}

الموضوع: {title}

المرسل من: {company_name}

نأمل منكم التكرم بإرسال عرض السعر في أقرب وقت ممكن.

مرفق ملف PDF لتفاصيل الطلب.

مع أطيب التحيات"""
        
        # URL encode message
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        
        return f"https://wa.me/{clean_phone}?text={encoded_message}"
    
    # ==================== Approve Quotation & Create Order ====================
    
    async def approve_quotation(
        self,
        quotation_id: str,
        approved_by: str,
        approved_by_name: str
    ) -> Optional[Dict[str, Any]]:
        """Approve a supplier quotation as winner"""
        quotation = await self.repository.get_supplier_quotation_by_id(quotation_id)
        if not quotation:
            return None
        
        # Mark this quotation as winner
        update_data = {
            "status": "accepted",
            "is_winner": True,
            "approved_at": datetime.now(timezone.utc).replace(tzinfo=None),
            "approved_by": approved_by,
            "approved_by_name": approved_by_name,
            "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
        }
        
        await self.repository.update_supplier_quotation(quotation_id, update_data)
        
        # Reject other quotations for this RFQ
        all_quotations = await self.repository.get_quotations_by_rfq(quotation.rfq_id)
        for q in all_quotations:
            if q.id != quotation_id and q.status == "pending":
                await self.repository.update_supplier_quotation(q.id, {
                    "status": "rejected",
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
                })
        
        return await self.get_quotation_details(quotation_id)
    
    async def create_order_from_quotation(
        self,
        quotation_id: str,
        created_by: str,
        created_by_name: str,
        notes: Optional[str] = None,
        expected_delivery_date: Optional[datetime] = None,
        update_catalog: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Create purchase order from approved quotation and optionally update catalog"""
        from sqlalchemy import select, func
        from database.models import PurchaseOrder, PurchaseOrderItem, PriceCatalogItem, MaterialRequest
        
        quotation = await self.repository.get_supplier_quotation_by_id(quotation_id)
        if not quotation:
            return {"error": "عرض السعر غير موجود"}
        
        if quotation.status != "accepted" or not quotation.is_winner:
            return {"error": "يجب اعتماد العرض أولاً"}
        
        if quotation.order_id:
            return {"error": "تم إصدار أمر شراء مسبقاً لهذا العرض"}
        
        # Get RFQ details
        rfq = await self.repository.get_rfq_by_id(quotation.rfq_id)
        if not rfq:
            return {"error": "طلب عرض السعر غير موجود"}
        
        # Check if RFQ is linked to a request
        rfq_request_id = rfq.request_id if hasattr(rfq, 'request_id') else None
        rfq_request_number = rfq.request_number if hasattr(rfq, 'request_number') else None
        
        if not rfq_request_id:
            return {"error": "لا يمكن إصدار أمر شراء من RFQ غير مرتبط بطلب مواد. يرجى إنشاء RFQ من طلب معتمد."}
        
        # Get quotation items
        quotation_items = await self.repository.get_quotation_items(quotation_id)
        
        # Generate order number with new format
        from app.utils.sequence_generator import generate_po_number
        order_number = await generate_po_number(self.session)
        
        # Get order count for sequence
        count_result = await self.session.execute(
            select(func.count()).select_from(PurchaseOrder)
        )
        order_count = count_result.scalar_one() or 0
        
        # Calculate order total
        total_amount = quotation.final_amount
        
        # الحصول على حد الموافقة من الإعدادات
        from database.models import SystemSetting
        approval_limit_result = await self.session.execute(
            select(SystemSetting).where(SystemSetting.key == "approval_limit")
        )
        approval_setting = approval_limit_result.scalar_one_or_none()
        approval_limit = float(approval_setting.value) if approval_setting and approval_setting.value else 20000
        
        # Determine if GM approval is needed
        needs_gm_approval = total_amount > approval_limit
        order_status = "pending_gm_approval" if needs_gm_approval else "pending_approval"
        
        # Create purchase order
        order_id = str(uuid.uuid4())
        order = PurchaseOrder(
            id=order_id,
            order_number=order_number,
            order_seq=order_count + 1,
            request_id=rfq_request_id,
            request_number=rfq_request_number,
            project_id=rfq.project_id if hasattr(rfq, 'project_id') else None,
            project_name=rfq.project_name if hasattr(rfq, 'project_name') and rfq.project_name else "غير محدد",
            supplier_id=quotation.supplier_id,
            supplier_name=quotation.supplier_name,
            manager_id=created_by,
            manager_name=created_by_name,
            status="pending",
            needs_gm_approval=needs_gm_approval,
            total_amount=total_amount,
            notes=notes or quotation.notes,
            expected_delivery_date=expected_delivery_date
        )
        self.session.add(order)
        
        # Track used codes in this batch to avoid duplicates
        used_codes = set()
        
        # Add order items
        for qi in quotation_items:
            order_item = PurchaseOrderItem(
                id=str(uuid.uuid4()),
                order_id=order_id,
                name=qi.item_name,
                item_code=qi.item_code,
                quantity=qi.quantity,
                unit=qi.unit,
                unit_price=qi.unit_price,
                total_price=qi.total_price,
                delivered_quantity=0
            )
            self.session.add(order_item)
            
            # Update catalog prices if enabled
            if update_catalog and qi.unit_price > 0:
                await self._update_catalog_price(
                    item_name=qi.item_name,
                    unit_price=qi.unit_price,
                    supplier_id=quotation.supplier_id,
                    supplier_name=quotation.supplier_name,
                    created_by=created_by,
                    created_by_name=created_by_name,
                    used_codes=used_codes
                )
        
        # Update quotation with order info
        await self.repository.update_supplier_quotation(quotation_id, {
            "order_id": order_id,
            "order_number": order_number,
            "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
        })
        
        # Close RFQ
        await self.repository.update_rfq(rfq.id, {
            "status": "closed",
            "closed_at": datetime.now(timezone.utc).replace(tzinfo=None)
        })
        
        # Update the original material request status to "issued"
        if rfq_request_id:
            request_result = await self.session.execute(
                select(MaterialRequest).where(MaterialRequest.id == rfq_request_id)
            )
            material_request = request_result.scalar_one_or_none()
            if material_request:
                material_request.status = "issued"
                material_request.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        await self.session.flush()
        
        return {
            "success": True,
            "order_id": order_id,
            "order_number": order_number,
            "quotation_id": quotation_id,
            "supplier_name": quotation.supplier_name,
            "total_amount": total_amount,
            "needs_gm_approval": needs_gm_approval,
            "catalog_updated": update_catalog,
            "items_count": len(quotation_items)
        }
    
    async def _update_catalog_price(
        self,
        item_name: str,
        unit_price: float,
        supplier_id: str,
        supplier_name: str,
        created_by: str,
        created_by_name: str,
        category_name: str = None,
        category_code: str = None,
        unit: str = "قطعة",
        used_codes: set = None
    ):
        """Update or create catalog item with new price"""
        from sqlalchemy import select, func
        from database.models import PriceCatalogItem
        
        if used_codes is None:
            used_codes = set()
        
        # Try to find existing catalog item by name
        result = await self.session.execute(
            select(PriceCatalogItem).where(
                PriceCatalogItem.name.ilike(f"%{item_name}%")
            ).limit(1)
        )
        catalog_item = result.scalar_one_or_none()
        
        if catalog_item:
            # Update existing item
            catalog_item.price = unit_price
            catalog_item.supplier_id = supplier_id
            catalog_item.supplier_name = supplier_name
            catalog_item.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            # Generate item code based on category code or default
            item_code = None
            prefix = category_code if category_code else "0"
            
            # Count items with this prefix pattern
            count_result = await self.session.execute(
                select(func.count(PriceCatalogItem.id))
                .where(PriceCatalogItem.item_code.like(f"{prefix}-%"))
            )
            count = count_result.scalar_one() or 0
            
            # Generate unique code (considering codes used in this batch)
            next_num = count + 1
            item_code = f"{prefix}-{next_num:04d}"
            
            # Make sure the code is unique (not used in current batch)
            while item_code in used_codes:
                next_num += 1
                item_code = f"{prefix}-{next_num:04d}"
            
            used_codes.add(item_code)
            
            # Create new catalog item with code
            new_item = PriceCatalogItem(
                id=str(uuid.uuid4()),
                item_code=item_code,
                name=item_name,
                price=unit_price,
                unit=unit,
                category_name=category_name,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                is_active=True,
                created_by=created_by,
                created_by_name=created_by_name,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            self.session.add(new_item)


# Dependency injection
async def get_rfq_service(session: AsyncSession) -> RFQService:
    return RFQService(session)

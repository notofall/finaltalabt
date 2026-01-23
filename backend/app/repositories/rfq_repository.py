"""
RFQ Repository - طبقة الوصول لقاعدة البيانات لنظام طلبات عروض الأسعار
"""
from typing import Optional, List
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from database.models import (
    QuotationRequest, QuotationRequestItem, QuotationRequestSupplier,
    SupplierQuotation, SupplierQuotationItem, Supplier
)


class RFQRepository:
    """Repository for RFQ operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== RFQ CRUD ====================
    
    async def get_next_rfq_number(self) -> str:
        """Generate next RFQ number (RFQ-YY-####)"""
        from app.utils.sequence_generator import generate_rfq_number
        return await generate_rfq_number(self.session)
    
    async def create_rfq(self, rfq_data: dict) -> QuotationRequest:
        """Create new RFQ"""
        rfq = QuotationRequest(**rfq_data)
        self.session.add(rfq)
        await self.session.flush()
        return rfq
    
    async def get_rfq_by_id(self, rfq_id: str) -> Optional[QuotationRequest]:
        """Get RFQ by ID"""
        result = await self.session.execute(
            select(QuotationRequest).where(QuotationRequest.id == rfq_id)
        )
        return result.scalar_one_or_none()
    
    async def get_rfq_by_number(self, rfq_number: str) -> Optional[QuotationRequest]:
        """Get RFQ by number"""
        result = await self.session.execute(
            select(QuotationRequest).where(QuotationRequest.rfq_number == rfq_number)
        )
        return result.scalar_one_or_none()
    
    async def get_all_rfqs(
        self, 
        skip: int = 0, 
        limit: int = 20,
        status: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[QuotationRequest]:
        """Get all RFQs with filters"""
        query = select(QuotationRequest)
        
        if status:
            query = query.where(QuotationRequest.status == status)
        if project_id:
            query = query.where(QuotationRequest.project_id == project_id)
        
        query = query.order_by(QuotationRequest.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_rfqs(
        self, 
        status: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> int:
        """Count RFQs"""
        query = select(func.count(QuotationRequest.id))
        
        if status:
            query = query.where(QuotationRequest.status == status)
        if project_id:
            query = query.where(QuotationRequest.project_id == project_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def update_rfq(self, rfq_id: str, update_data: dict) -> Optional[QuotationRequest]:
        """Update RFQ"""
        rfq = await self.get_rfq_by_id(rfq_id)
        if not rfq:
            return None
        
        for key, value in update_data.items():
            if hasattr(rfq, key):
                setattr(rfq, key, value)
        
        rfq.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.session.flush()
        return rfq
    
    async def delete_rfq(self, rfq_id: str) -> bool:
        """Delete RFQ (cascade deletes items and suppliers)"""
        rfq = await self.get_rfq_by_id(rfq_id)
        if not rfq:
            return False
        
        await self.session.delete(rfq)
        return True
    
    # ==================== RFQ Items ====================
    
    async def add_rfq_item(self, item_data: dict) -> QuotationRequestItem:
        """Add item to RFQ"""
        item = QuotationRequestItem(**item_data)
        self.session.add(item)
        await self.session.flush()
        return item
    
    async def get_rfq_items(self, rfq_id: str) -> List[QuotationRequestItem]:
        """Get all items for an RFQ"""
        result = await self.session.execute(
            select(QuotationRequestItem)
            .where(QuotationRequestItem.rfq_id == rfq_id)
            .order_by(QuotationRequestItem.item_index)
        )
        return list(result.scalars().all())
    
    async def update_rfq_item(self, item_id: str, update_data: dict) -> Optional[QuotationRequestItem]:
        """Update RFQ item"""
        result = await self.session.execute(
            select(QuotationRequestItem).where(QuotationRequestItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            return None
        
        for key, value in update_data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        await self.session.flush()
        return item
    
    async def delete_rfq_item(self, item_id: str) -> bool:
        """Delete RFQ item"""
        result = await self.session.execute(
            select(QuotationRequestItem).where(QuotationRequestItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            return False
        
        await self.session.delete(item)
        return True
    
    # ==================== RFQ Suppliers ====================
    
    async def add_rfq_supplier(self, supplier_data: dict) -> QuotationRequestSupplier:
        """Add supplier to RFQ"""
        rfq_supplier = QuotationRequestSupplier(**supplier_data)
        self.session.add(rfq_supplier)
        await self.session.flush()
        return rfq_supplier
    
    async def get_rfq_suppliers(self, rfq_id: str) -> List[QuotationRequestSupplier]:
        """Get all suppliers for an RFQ"""
        result = await self.session.execute(
            select(QuotationRequestSupplier)
            .where(QuotationRequestSupplier.rfq_id == rfq_id)
        )
        return list(result.scalars().all())
    
    async def update_rfq_supplier(self, supplier_id: str, update_data: dict) -> Optional[QuotationRequestSupplier]:
        """Update RFQ supplier"""
        result = await self.session.execute(
            select(QuotationRequestSupplier).where(QuotationRequestSupplier.id == supplier_id)
        )
        supplier = result.scalar_one_or_none()
        if not supplier:
            return None
        
        for key, value in update_data.items():
            if hasattr(supplier, key):
                setattr(supplier, key, value)
        
        await self.session.flush()
        return supplier
    
    async def remove_rfq_supplier(self, supplier_id: str) -> bool:
        """Remove supplier from RFQ"""
        result = await self.session.execute(
            select(QuotationRequestSupplier).where(QuotationRequestSupplier.id == supplier_id)
        )
        supplier = result.scalar_one_or_none()
        if not supplier:
            return False
        
        await self.session.delete(supplier)
        return True
    
    # ==================== Supplier Quotations ====================
    
    async def get_next_quotation_number(self) -> str:
        """Generate next supplier quotation number (SQ-YY-####)"""
        from app.utils.sequence_generator import generate_quotation_number
        return await generate_quotation_number(self.session)
    
    async def create_supplier_quotation(self, quotation_data: dict) -> SupplierQuotation:
        """Create supplier quotation"""
        quotation = SupplierQuotation(**quotation_data)
        self.session.add(quotation)
        await self.session.flush()
        return quotation
    
    async def get_supplier_quotation_by_id(self, quotation_id: str) -> Optional[SupplierQuotation]:
        """Get supplier quotation by ID"""
        result = await self.session.execute(
            select(SupplierQuotation).where(SupplierQuotation.id == quotation_id)
        )
        return result.scalar_one_or_none()
    
    async def get_quotations_by_rfq(self, rfq_id: str) -> List[SupplierQuotation]:
        """Get all supplier quotations for an RFQ"""
        result = await self.session.execute(
            select(SupplierQuotation)
            .where(SupplierQuotation.rfq_id == rfq_id)
            .order_by(SupplierQuotation.final_amount)
        )
        return list(result.scalars().all())
    
    async def update_supplier_quotation(self, quotation_id: str, update_data: dict) -> Optional[SupplierQuotation]:
        """Update supplier quotation"""
        quotation = await self.get_supplier_quotation_by_id(quotation_id)
        if not quotation:
            return None
        
        for key, value in update_data.items():
            if hasattr(quotation, key):
                setattr(quotation, key, value)
        
        quotation.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.session.flush()
        return quotation
    
    async def delete_supplier_quotation(self, quotation_id: str) -> bool:
        """Delete supplier quotation"""
        quotation = await self.get_supplier_quotation_by_id(quotation_id)
        if not quotation:
            return False
        
        await self.session.delete(quotation)
        return True
    
    # ==================== Supplier Quotation Items ====================
    
    async def add_quotation_item(self, item_data: dict) -> SupplierQuotationItem:
        """Add item to supplier quotation"""
        item = SupplierQuotationItem(**item_data)
        self.session.add(item)
        await self.session.flush()
        return item
    
    async def get_quotation_items(self, quotation_id: str) -> List[SupplierQuotationItem]:
        """Get all items for a supplier quotation"""
        result = await self.session.execute(
            select(SupplierQuotationItem)
            .where(SupplierQuotationItem.quotation_id == quotation_id)
        )
        return list(result.scalars().all())
    
    async def update_quotation_item(self, item_id: str, update_data: dict) -> Optional[SupplierQuotationItem]:
        """Update quotation item"""
        result = await self.session.execute(
            select(SupplierQuotationItem).where(SupplierQuotationItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            return None
        
        for key, value in update_data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        await self.session.flush()
        return item
    
    # ==================== Statistics ====================
    
    async def get_rfq_stats(self) -> dict:
        """Get RFQ statistics"""
        # Total count
        total_result = await self.session.execute(
            select(func.count(QuotationRequest.id))
        )
        total = total_result.scalar() or 0
        
        # Count by status
        draft_result = await self.session.execute(
            select(func.count(QuotationRequest.id))
            .where(QuotationRequest.status == "draft")
        )
        draft = draft_result.scalar() or 0
        
        sent_result = await self.session.execute(
            select(func.count(QuotationRequest.id))
            .where(QuotationRequest.status == "sent")
        )
        sent = sent_result.scalar() or 0
        
        received_result = await self.session.execute(
            select(func.count(QuotationRequest.id))
            .where(QuotationRequest.status == "received")
        )
        received = received_result.scalar() or 0
        
        closed_result = await self.session.execute(
            select(func.count(QuotationRequest.id))
            .where(QuotationRequest.status == "closed")
        )
        closed = closed_result.scalar() or 0
        
        # Total quotations received
        quotations_result = await self.session.execute(
            select(func.count(SupplierQuotation.id))
        )
        total_quotations = quotations_result.scalar() or 0
        
        return {
            "total_rfqs": total,
            "draft": draft,
            "sent": sent,
            "received": received,
            "closed": closed,
            "total_quotations": total_quotations
        }
    
    async def get_supplier_by_id(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by ID"""
        result = await self.session.execute(
            select(Supplier).where(Supplier.id == supplier_id)
        )
        return result.scalar_one_or_none()

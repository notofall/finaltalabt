"""
GM Repository - Data access layer for General Manager operations
مستودع المدير العام - طبقة الوصول للبيانات
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import PurchaseOrder, PurchaseOrderItem


class GMRepository:
    """Repository for GM data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_pending_gm_orders(self) -> List[PurchaseOrder]:
        """Get orders pending GM approval"""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.status == "pending_gm_approval")
            .order_by(desc(PurchaseOrder.created_at))
        )
        return list(result.scalars().all())
    
    async def get_all_orders(
        self, 
        approval_type: Optional[str] = None
    ) -> List[PurchaseOrder]:
        """Get all orders with optional filter"""
        query = select(PurchaseOrder)
        
        if approval_type == "gm_approved":
            query = query.where(PurchaseOrder.gm_approved_by.isnot(None))
        elif approval_type == "manager_approved":
            query = query.where(
                and_(
                    PurchaseOrder.approved_by.isnot(None),
                    PurchaseOrder.gm_approved_by.is_(None)
                )
            )
        elif approval_type == "pending":
            query = query.where(PurchaseOrder.status == "pending_gm_approval")
        
        query = query.order_by(desc(PurchaseOrder.created_at))
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_order_by_id(self, order_id: str) -> Optional[PurchaseOrder]:
        """Get order by ID"""
        result = await self.session.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_order_items(self, order_id: str) -> List[PurchaseOrderItem]:
        """Get items for an order"""
        result = await self.session.execute(
            select(PurchaseOrderItem)
            .where(PurchaseOrderItem.order_id == order_id)
            .order_by(PurchaseOrderItem.item_index)
        )
        return list(result.scalars().all())
    
    async def approve_order(
        self, 
        order: PurchaseOrder, 
        user_id: str, 
        user_name: str
    ) -> PurchaseOrder:
        """Approve order by GM"""
        now = datetime.now(timezone.utc)
        order.status = "approved"
        order.gm_approved_by = user_id
        order.gm_approved_by_name = user_name
        order.gm_approved_at = now
        order.updated_at = now
        await self.session.commit()
        return order
    
    async def reject_order(
        self, 
        order: PurchaseOrder, 
        reason: str
    ) -> PurchaseOrder:
        """Reject order by GM"""
        order.status = "rejected_by_gm"
        order.rejection_reason = reason
        order.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return order
    
    # ==================== Statistics ====================
    
    async def get_pending_count(self) -> int:
        """Count pending GM approval orders"""
        result = await self.session.execute(
            select(func.count(PurchaseOrder.id))
            .where(PurchaseOrder.status == "pending_gm_approval")
        )
        return result.scalar() or 0
    
    async def get_approved_count(self) -> int:
        """Count GM approved orders"""
        result = await self.session.execute(
            select(func.count(PurchaseOrder.id))
            .where(PurchaseOrder.gm_approved_by.isnot(None))
        )
        return result.scalar() or 0
    
    async def get_rejected_count(self) -> int:
        """Count GM rejected orders"""
        result = await self.session.execute(
            select(func.count(PurchaseOrder.id))
            .where(PurchaseOrder.status == "rejected_by_gm")
        )
        return result.scalar() or 0
    
    async def get_total_approved_amount(self) -> float:
        """Get total amount of GM approved orders"""
        result = await self.session.execute(
            select(func.sum(PurchaseOrder.total_amount))
            .where(PurchaseOrder.gm_approved_by.isnot(None))
        )
        return result.scalar() or 0.0
    
    async def get_pending_amount(self) -> float:
        """Get total amount pending GM approval"""
        result = await self.session.execute(
            select(func.sum(PurchaseOrder.total_amount))
            .where(PurchaseOrder.status == "pending_gm_approval")
        )
        return result.scalar() or 0.0

"""
Order Repository
فصل طبقة الوصول لقاعدة البيانات لأوامر الشراء
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import PurchaseOrder, PurchaseOrderItem
from .base import BaseRepository


class OrderRepository(BaseRepository[PurchaseOrder]):
    """Repository for PurchaseOrder entity"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[PurchaseOrder]:
        """Get order by ID"""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.id == str(id))
        )
        return result.scalar_one_or_none()
    
    async def get_by_order_number(self, order_number: str) -> Optional[PurchaseOrder]:
        """Get order by order number"""
        result = await self.session.execute(
            select(PurchaseOrder).where(PurchaseOrder.order_number == order_number)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[PurchaseOrder]:
        """Get all orders with pagination"""
        result = await self.session.execute(
            select(PurchaseOrder)
            .offset(skip)
            .limit(limit)
            .order_by(PurchaseOrder.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_status(self, status: str) -> List[PurchaseOrder]:
        """Get orders by status"""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.status == status)
            .order_by(PurchaseOrder.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_project(self, project_id: UUID) -> List[PurchaseOrder]:
        """Get orders by project"""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.project_id == str(project_id))
            .order_by(PurchaseOrder.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_supplier(self, supplier_id: UUID) -> List[PurchaseOrder]:
        """Get orders by supplier"""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.supplier_id == str(supplier_id))
            .order_by(PurchaseOrder.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_pending_delivery(self) -> List[PurchaseOrder]:
        """Get orders pending delivery"""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.status.in_(['approved', 'shipped', 'partially_delivered']))
            .order_by(PurchaseOrder.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def create(self, order: PurchaseOrder) -> PurchaseOrder:
        """Create new order"""
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order
    
    async def update(self, id: UUID, order_data: dict) -> Optional[PurchaseOrder]:
        """Update order"""
        order = await self.get_by_id(id)
        if order:
            for key, value in order_data.items():
                if hasattr(order, key) and key != 'items':
                    setattr(order, key, value)
            await self.session.flush()
            await self.session.refresh(order)
        return order
    
    async def update_status(self, id: UUID, status: str) -> Optional[PurchaseOrder]:
        """Update order status"""
        return await self.update(id, {"status": status})
    
    async def delete(self, id: UUID) -> bool:
        """Delete order"""
        order = await self.get_by_id(id)
        if order:
            await self.session.delete(order)
            await self.session.flush()
            return True
        return False
    
    async def count(self) -> int:
        """Count total orders"""
        result = await self.session.execute(
            select(func.count(PurchaseOrder.id))
        )
        return result.scalar_one()
    
    async def count_by_status(self, status: str) -> int:
        """Count orders by status"""
        result = await self.session.execute(
            select(func.count(PurchaseOrder.id))
            .where(PurchaseOrder.status == status)
        )
        return result.scalar_one()
    
    async def get_total_amount_by_project(self, project_id: UUID) -> float:
        """Get total order amount for a project"""
        result = await self.session.execute(
            select(func.sum(PurchaseOrder.total_amount))
            .where(PurchaseOrder.project_id == str(project_id))
        )
        return result.scalar_one() or 0.0
    
    async def generate_order_number(self, prefix: str = "PO") -> str:
        """Generate unique order number in format PO-YY-####"""
        from app.utils.sequence_generator import generate_po_number
        return await generate_po_number(self.session)
    
    async def get_order_items(self, order_id: str) -> List[dict]:
        """Get items for a specific order"""
        result = await self.session.execute(
            select(PurchaseOrderItem)
            .where(PurchaseOrderItem.order_id == order_id)
            .order_by(PurchaseOrderItem.item_index)
        )
        items = result.scalars().all()
        
        return [
            {
                "id": str(item.id),
                "name": item.name,
                "quantity": item.quantity or 0,
                "unit": item.unit or "قطعة",
                "unit_price": item.unit_price or 0,
                "total_price": item.total_price or 0,
                "delivered_quantity": item.delivered_quantity or 0,
                "catalog_item_id": item.catalog_item_id,
                "item_code": item.item_code
            }
            for item in items
        ]
    
    async def get_orders_items_batch(self, order_ids: List[str]) -> dict:
        """Get items for multiple orders in one query"""
        if not order_ids:
            return {}
        
        result = await self.session.execute(
            select(PurchaseOrderItem)
            .where(PurchaseOrderItem.order_id.in_(order_ids))
            .order_by(PurchaseOrderItem.order_id, PurchaseOrderItem.item_index)
        )
        all_items = result.scalars().all()
        
        # Group items by order_id
        items_map = {}
        for item in all_items:
            if item.order_id not in items_map:
                items_map[item.order_id] = []
            items_map[item.order_id].append({
                "id": str(item.id),
                "name": item.name,
                "quantity": item.quantity or 0,
                "unit": item.unit or "قطعة",
                "unit_price": item.unit_price or 0,
                "total_price": item.total_price or 0,
                "delivered_quantity": item.delivered_quantity or 0,
                "catalog_item_id": item.catalog_item_id,
                "item_code": item.item_code
            })
        
        return items_map

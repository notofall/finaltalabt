"""
Order Service
فصل منطق العمل لأوامر الشراء
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from database import PurchaseOrder, PurchaseOrderItem
from app.repositories.order_repository import OrderRepository
from app.repositories.supply_repository import SupplyRepository
from .base import BaseService


class OrderService(BaseService[PurchaseOrder]):
    """Service for purchase order operations"""
    
    def __init__(
        self, 
        order_repository: OrderRepository,
        supply_repository: Optional[SupplyRepository] = None
    ):
        self.order_repo = order_repository
        self.supply_repo = supply_repository
    
    async def get_order(self, order_id: UUID) -> Optional[PurchaseOrder]:
        """Get order by ID"""
        return await self.order_repo.get_by_id(order_id)
    
    async def get_all_orders(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[PurchaseOrder]:
        """Get all orders with pagination"""
        return await self.order_repo.get_all(skip, limit)
    
    async def get_orders_by_status(self, status: str) -> List[PurchaseOrder]:
        """Get orders by status"""
        return await self.order_repo.get_by_status(status)
    
    async def get_orders_by_project(self, project_id: UUID) -> List[PurchaseOrder]:
        """Get orders for a specific project"""
        return await self.order_repo.get_by_project(project_id)
    
    async def get_pending_delivery_orders(self) -> List[PurchaseOrder]:
        """Get orders pending delivery"""
        return await self.order_repo.get_pending_delivery()
    
    async def create_order(
        self,
        request_id: UUID,
        supplier_id: UUID,
        project_id: UUID,
        items: List[dict],
        created_by: str,
        notes: str = ""
    ) -> PurchaseOrder:
        """Create new purchase order"""
        # Generate order number
        order_number = await self.order_repo.generate_order_number()
        
        # Calculate total amount
        total_amount = sum(
            (item.get("quantity", 0) * item.get("unit_price", 0))
            for item in items
        )
        
        # Create order
        order = PurchaseOrder(
            order_number=order_number,
            request_id=str(request_id),
            supplier_id=str(supplier_id),
            project_id=str(project_id),
            total_amount=total_amount,
            status="pending",
            notes=notes,
            created_by=created_by,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        # Add items
        for item_data in items:
            item = PurchaseOrderItem(
                catalog_item_id=item_data.get("catalog_item_id"),
                item_name=item_data.get("item_name"),
                quantity=item_data.get("quantity", 0),
                unit_price=item_data.get("unit_price", 0),
                unit=item_data.get("unit", ""),
                total_price=item_data.get("quantity", 0) * item_data.get("unit_price", 0)
            )
            order.items.append(item)
        
        return await self.order_repo.create(order)
    
    async def approve_order(
        self, 
        order_id: UUID, 
        approved_by: str
    ) -> Optional[PurchaseOrder]:
        """Approve order"""
        return await self.order_repo.update(order_id, {
            "status": "approved",
            "approved_by": approved_by,
            "approved_at": datetime.now(timezone.utc).replace(tzinfo=None)
        })
    
    async def reject_order(
        self, 
        order_id: UUID, 
        rejected_by: str,
        rejection_reason: str = ""
    ) -> Optional[PurchaseOrder]:
        """Reject order"""
        return await self.order_repo.update(order_id, {
            "status": "rejected",
            "rejected_by": rejected_by,
            "rejection_reason": rejection_reason
        })
    
    async def confirm_delivery(
        self,
        order_id: UUID,
        delivered_items: List[dict],
        confirmed_by: str
    ) -> Optional[PurchaseOrder]:
        """
        Confirm delivery and update supply tracking
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return None
        
        # Check if all items delivered
        all_delivered = True
        for item in order.items:
            delivered = next(
                (d for d in delivered_items if d.get("item_id") == str(item.id)),
                None
            )
            if delivered:
                delivered_qty = delivered.get("quantity_delivered", 0)
                item.quantity_delivered = (item.quantity_delivered or 0) + delivered_qty
                
                if item.quantity_delivered < item.quantity:
                    all_delivered = False
                
                # Update supply tracking if available
                if self.supply_repo and order.project_id and item.catalog_item_id:
                    await self.supply_repo.update_received_quantity(
                        UUID(order.project_id),
                        UUID(item.catalog_item_id),
                        delivered_qty
                    )
            else:
                if (item.quantity_delivered or 0) < item.quantity:
                    all_delivered = False
        
        # Update order status
        new_status = "delivered" if all_delivered else "partially_delivered"
        return await self.order_repo.update(order_id, {
            "status": new_status,
            "delivered_at": datetime.now(timezone.utc).replace(tzinfo=None) if all_delivered else None
        })
    
    async def get_order_stats(self) -> dict:
        """Get order statistics"""
        total = await self.order_repo.count()
        pending = await self.order_repo.count_by_status("pending")
        approved = await self.order_repo.count_by_status("approved")
        delivered = await self.order_repo.count_by_status("delivered")
        rejected = await self.order_repo.count_by_status("rejected")
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "delivered": delivered,
            "rejected": rejected
        }
    
    async def get_order_items(self, order_id: str) -> List[dict]:
        """Get items for a specific order via Repository"""
        return await self.order_repo.get_order_items(order_id)
    
    async def get_orders_items_batch(self, order_ids: List[str]) -> dict:
        """Get items for multiple orders via Repository"""
        return await self.order_repo.get_orders_items_batch(order_ids)
    
    async def count_orders(self, status_filter: Optional[str] = None) -> int:
        """Count total orders, optionally filtered by status"""
        if status_filter:
            return await self.order_repo.count_by_status(status_filter)
        return await self.order_repo.count()

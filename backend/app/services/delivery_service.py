"""
Delivery Service
فصل منطق العمل لتتبع التسليم
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from database import PurchaseOrder, DeliveryRecord
from app.repositories.order_repository import OrderRepository
from app.repositories.supply_repository import SupplyRepository
from .base import BaseService


class DeliveryService(BaseService):
    """Service for delivery tracking operations"""
    
    def __init__(
        self, 
        order_repository: OrderRepository,
        supply_repository: SupplyRepository
    ):
        self.order_repo = order_repository
        self.supply_repo = supply_repository
    
    async def get_pending_deliveries(self) -> List[PurchaseOrder]:
        """Get all orders pending delivery"""
        return await self.order_repo.get_pending_delivery()
    
    async def get_delivery_stats(self) -> dict:
        """Get delivery statistics"""
        pending = await self.order_repo.get_pending_delivery()
        
        shipped = [o for o in pending if o.status == "shipped"]
        partially_delivered = [o for o in pending if o.status == "partially_delivered"]
        approved = [o for o in pending if o.status == "approved"]
        
        return {
            "total_pending": len(pending),
            "shipped": len(shipped),
            "partially_delivered": len(partially_delivered),
            "awaiting_shipment": len(approved)
        }
    
    async def mark_as_shipped(
        self, 
        order_id: UUID,
        shipped_by: str,
        tracking_number: str = ""
    ) -> Optional[PurchaseOrder]:
        """Mark order as shipped"""
        return await self.order_repo.update(order_id, {
            "status": "shipped",
            "shipped_at": datetime.now(timezone.utc).replace(tzinfo=None),
            "tracking_number": tracking_number
        })
    
    async def confirm_receipt(
        self,
        order_id: UUID,
        items: List[dict],
        confirmed_by: str
    ) -> dict:
        """
        Confirm receipt of items and auto-deduct from supply tracking
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        supply_updated_count = 0
        all_delivered = True
        
        # Process each item
        for item in order.items:
            delivered_item = next(
                (d for d in items if d.get("item_id") == str(item.id)),
                None
            )
            
            if delivered_item:
                qty_delivered = delivered_item.get("quantity_delivered", 0)
                item.quantity_delivered = (item.quantity_delivered or 0) + qty_delivered
                
                # Auto-deduct from supply tracking
                if order.project_id and item.catalog_item_id:
                    supply = await self.supply_repo.update_received_quantity(
                        UUID(order.project_id),
                        UUID(item.catalog_item_id),
                        qty_delivered
                    )
                    if supply:
                        supply_updated_count += 1
            
            if (item.quantity_delivered or 0) < item.quantity:
                all_delivered = False
        
        # Update order status
        new_status = "delivered" if all_delivered else "partially_delivered"
        await self.order_repo.update(order_id, {
            "status": new_status,
            "delivered_at": datetime.now(timezone.utc).replace(tzinfo=None) if all_delivered else None
        })
        
        return {
            "success": True,
            "status": new_status,
            "fully_delivered": all_delivered,
            "supply_items_updated": supply_updated_count
        }
    
    async def get_project_supply_status(self, project_id: UUID) -> dict:
        """Get supply status for a project"""
        return await self.supply_repo.get_project_summary(project_id)

"""
GM Service - Business logic for General Manager operations
خدمة المدير العام - منطق العمل

Architecture: Route -> Service -> Repository
"""
from typing import Optional, List, Dict
from app.repositories.gm_repository import GMRepository
from app.config import to_iso_string


class GMService:
    """Service layer for GM operations"""
    
    def __init__(self, repository: GMRepository):
        self.repository = repository
    
    # ==================== Orders ====================
    
    async def get_pending_orders(self) -> List[Dict]:
        """Get orders pending GM approval"""
        orders = await self.repository.get_pending_gm_orders()
        return await self._format_orders_with_items(orders)
    
    async def get_all_orders(
        self, 
        approval_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all orders with optional filter"""
        orders = await self.repository.get_all_orders(approval_type)
        return await self._format_orders_with_items(orders)
    
    async def approve_order(
        self, 
        order_id: str, 
        user_id: str, 
        user_name: str
    ) -> Dict:
        """Approve order by GM"""
        order = await self.repository.get_order_by_id(order_id)
        if not order:
            raise ValueError("أمر الشراء غير موجود")
        
        if order.status != "pending_gm_approval":
            raise ValueError("أمر الشراء ليس في انتظار موافقة المدير العام")
        
        await self.repository.approve_order(order, user_id, user_name)
        return {"message": "تم اعتماد أمر الشراء بنجاح", "status": "approved"}
    
    async def reject_order(
        self, 
        order_id: str, 
        reason: str
    ) -> Dict:
        """Reject order by GM"""
        order = await self.repository.get_order_by_id(order_id)
        if not order:
            raise ValueError("أمر الشراء غير موجود")
        
        if order.status != "pending_gm_approval":
            raise ValueError("أمر الشراء ليس في انتظار موافقة المدير العام")
        
        await self.repository.reject_order(order, reason)
        return {"message": "تم رفض أمر الشراء", "status": "rejected_by_gm"}
    
    # ==================== Statistics ====================
    
    async def get_stats(self) -> Dict:
        """Get GM dashboard statistics"""
        pending_count = await self.repository.get_pending_count()
        approved_count = await self.repository.get_approved_count()
        rejected_count = await self.repository.get_rejected_count()
        total_approved_amount = await self.repository.get_total_approved_amount()
        pending_amount = await self.repository.get_pending_amount()
        
        return {
            "pending_orders": pending_count,
            "approved_orders": approved_count,
            "rejected_orders": rejected_count,
            "total_approved_amount": float(total_approved_amount),
            "pending_amount": float(pending_amount)
        }
    
    # ==================== Helpers ====================
    
    async def _format_orders_with_items(
        self, 
        orders: list
    ) -> List[Dict]:
        """Format orders with items for response"""
        result = []
        for order in orders:
            items = await self.repository.get_order_items(order.id)
            result.append(self._format_order(order, items))
        return result
    
    def _format_order(self, order, items: list) -> Dict:
        """Format single order for response"""
        return {
            "id": order.id,
            "order_number": order.order_number,
            "request_number": order.request_number,
            "project_name": order.project_name,
            "supplier_name": order.supplier_name,
            "category_name": order.category_name,
            "total_amount": order.total_amount,
            "status": order.status,
            "manager_name": order.manager_name,
            "supervisor_name": order.supervisor_name,
            "engineer_name": order.engineer_name,
            "approved_by_name": getattr(order, 'approved_by_name', None),
            "gm_approved_by_name": getattr(order, 'gm_approved_by_name', None),
            "notes": order.notes,
            "terms_conditions": order.terms_conditions,
            "expected_delivery_date": to_iso_string(order.expected_delivery_date),
            "created_at": to_iso_string(order.created_at),
            "approved_at": to_iso_string(order.approved_at),
            "gm_approved_at": to_iso_string(order.gm_approved_at),
            "items_count": len(items),
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                }
                for item in items
            ]
        }

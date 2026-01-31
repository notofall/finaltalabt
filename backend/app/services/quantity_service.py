"""
Quantity Service - Business logic for planned quantities
"""
from typing import Dict, List, Optional
from datetime import datetime
from app.repositories.quantity_repository import QuantityRepository
from app.services.base import BaseService


class QuantityService(BaseService):
    """Service layer for quantity operations"""
    
    def __init__(self, repository: QuantityRepository):
        self.repository = repository
    
    # ==================== CATALOG ITEMS ====================
    
    async def get_catalog_items(
        self,
        search: Optional[str] = None,
        supplier_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Get catalog items for planning"""
        items, total = await self.repository.get_catalog_items(
            search=search,
            supplier_id=supplier_id,
            page=page,
            page_size=page_size
        )
        
        return {
            "items": [
                {
                    "id": item.id,
                    "item_code": item.item_code,
                    "name": item.name,
                    "description": item.description,
                    "unit": item.unit,
                    "supplier_id": item.supplier_id,
                    "supplier_name": item.supplier_name,
                    "price": item.price,
                    "currency": item.currency,
                    "category_id": item.category_id,
                    "category_name": item.category_name
                }
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    # ==================== BUDGET CATEGORIES ====================
    
    async def get_budget_categories_by_project(self, project_id: str) -> List[Dict]:
        """Get budget categories for a project"""
        categories = await self.repository.get_budget_categories_by_project(project_id)
        return [
            {
                "id": cat.id,
                "code": cat.code,
                "name": cat.name,
                "estimated_budget": cat.estimated_budget
            }
            for cat in categories
        ]
    
    async def get_all_budget_categories(self) -> Dict:
        """Get all budget categories"""
        categories = await self.repository.get_all_budget_categories()
        return {
            "categories": [
                {
                    "id": cat.id,
                    "code": cat.code,
                    "name": cat.name,
                    "project_id": cat.project_id,
                    "estimated_budget": cat.estimated_budget
                }
                for cat in categories
            ]
        }
    
    # ==================== PLANNED QUANTITIES ====================
    
    async def get_planned_quantities(
        self,
        project_id: Optional[str] = None,
        catalog_item_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Get planned quantities with pagination"""
        items, total = await self.repository.get_planned_quantities(
            project_id=project_id,
            catalog_item_id=catalog_item_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size
        )
        
        return {
            "items": [self._format_planned_quantity(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def create_planned_quantity(
        self,
        catalog_item_id: str,
        project_id: str,
        planned_quantity: float,
        user_id: str,
        user_name: str,
        expected_order_date: Optional[str] = None,
        priority: int = 2,
        notes: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Dict:
        """Create a new planned quantity"""
        # Get catalog item
        catalog_item = await self.repository.get_catalog_item_by_id(catalog_item_id)
        if not catalog_item:
            raise ValueError("الصنف غير موجود في الكتالوج")
        
        # Get project
        project = await self.repository.get_project_by_id(project_id)
        if not project:
            raise ValueError("المشروع غير موجود")
        
        # Parse date
        parsed_date = None
        if expected_order_date:
            try:
                parsed_date = datetime.fromisoformat(expected_order_date.replace('Z', '+00:00'))
            except:
                parsed_date = None
        
        data = {
            "catalog_item_id": catalog_item_id,
            "item_code": catalog_item.item_code,
            "item_name": catalog_item.name,
            "description": catalog_item.description,
            "unit": catalog_item.unit,
            "unit_price": catalog_item.price,
            "supplier_name": catalog_item.supplier_name,
            "project_id": project_id,
            "project_name": project.name,
            "planned_quantity": planned_quantity,
            "remaining_quantity": planned_quantity,
            "ordered_quantity": 0,
            "expected_order_date": parsed_date,
            "priority": priority,
            "notes": notes,
            "category_id": category_id or catalog_item.category_id,
            "category_name": catalog_item.category_name,
            "status": "pending",
            "created_by": user_id,
            "created_by_name": user_name
        }
        
        quantity = await self.repository.create_planned_quantity(data)
        return self._format_planned_quantity(quantity)
    
    async def update_planned_quantity(
        self,
        quantity_id: str,
        updates: Dict
    ) -> Optional[Dict]:
        """Update a planned quantity"""
        # Parse date if provided
        if 'expected_order_date' in updates and updates['expected_order_date']:
            try:
                updates['expected_order_date'] = datetime.fromisoformat(
                    updates['expected_order_date'].replace('Z', '+00:00')
                )
            except:
                updates['expected_order_date'] = None
        
        quantity = await self.repository.update_planned_quantity(quantity_id, updates)
        if quantity:
            return self._format_planned_quantity(quantity)
        return None
    
    async def delete_planned_quantity(self, quantity_id: str) -> bool:
        """Delete a planned quantity"""
        return await self.repository.delete_planned_quantity(quantity_id)
    
    # ==================== DASHBOARD & REPORTS ====================
    
    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        return await self.repository.get_dashboard_stats()
    
    async def get_summary_report(self, project_id: Optional[str] = None) -> Dict:
        """Get summary report - returns structured data matching frontend"""
        return await self.repository.get_summary_report(project_id)
    
    async def get_alerts(self, days_threshold: int = 7) -> Dict:
        """Get alerts - returns structured data matching frontend (overdue, due_soon, high_priority)"""
        return await self.repository.get_alerts(days_threshold)
    
    # ==================== HELPERS ====================
    
    def _format_planned_quantity(self, item) -> Dict:
        """Format planned quantity for response"""
        return {
            "id": item.id,
            "item_name": item.item_name,
            "item_code": item.item_code,
            "unit": item.unit,
            "description": item.description,
            "planned_quantity": item.planned_quantity,
            "ordered_quantity": item.ordered_quantity,
            "remaining_quantity": item.remaining_quantity,
            "project_id": item.project_id,
            "project_name": item.project_name,
            "category_id": item.category_id,
            "category_name": item.category_name,
            "catalog_item_id": item.catalog_item_id,
            "supplier_name": getattr(item, 'supplier_name', None),
            "unit_price": getattr(item, 'unit_price', None),
            "expected_order_date": item.expected_order_date.isoformat() if item.expected_order_date else None,
            "status": item.status,
            "priority": item.priority,
            "notes": item.notes,
            "created_by": item.created_by,
            "created_by_name": item.created_by_name,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        }

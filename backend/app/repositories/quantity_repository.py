"""
Quantity Repository - Repository layer for planned quantities
"""
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from database import PlannedQuantity, PriceCatalogItem, BudgetCategory, Project
from datetime import datetime, timedelta, timezone
import uuid


class QuantityRepository:
    """Repository for planned quantities operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== CATALOG ITEMS ====================
    
    async def get_catalog_items(
        self,
        search: Optional[str] = None,
        supplier_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[PriceCatalogItem], int]:
        """Get catalog items for planning with pagination"""
        query = select(PriceCatalogItem).where(PriceCatalogItem.is_active == True)
        
        if search:
            query = query.where(
                or_(
                    PriceCatalogItem.name.ilike(f"%{search}%"),
                    PriceCatalogItem.description.ilike(f"%{search}%"),
                    PriceCatalogItem.item_code.ilike(f"%{search}%")
                )
            )
        
        if supplier_id:
            query = query.where(PriceCatalogItem.supplier_id == supplier_id)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.order_by(
            PriceCatalogItem.item_code.asc().nullslast(),
            PriceCatalogItem.name
        ).offset(offset).limit(page_size)
        
        result = await self.session.execute(query)
        return result.scalars().all(), total
    
    async def get_catalog_item_by_id(self, item_id: str) -> Optional[PriceCatalogItem]:
        """Get a single catalog item"""
        result = await self.session.execute(
            select(PriceCatalogItem).where(PriceCatalogItem.id == item_id)
        )
        return result.scalar_one_or_none()
    
    # ==================== BUDGET CATEGORIES ====================
    
    async def get_budget_categories_by_project(self, project_id: str) -> List[BudgetCategory]:
        """Get budget categories for a project"""
        result = await self.session.execute(
            select(BudgetCategory)
            .where(BudgetCategory.project_id == project_id)
            .order_by(BudgetCategory.name)
        )
        return result.scalars().all()
    
    async def get_all_budget_categories(self) -> List[BudgetCategory]:
        """Get all budget categories"""
        result = await self.session.execute(
            select(BudgetCategory).order_by(BudgetCategory.name)
        )
        return result.scalars().all()
    
    # ==================== PLANNED QUANTITIES ====================
    
    async def get_planned_quantities(
        self,
        project_id: Optional[str] = None,
        catalog_item_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[PlannedQuantity], int]:
        """Get planned quantities with filters and pagination"""
        query = select(PlannedQuantity)
        
        if project_id:
            query = query.where(PlannedQuantity.project_id == project_id)
        
        if catalog_item_id:
            query = query.where(PlannedQuantity.catalog_item_id == catalog_item_id)
        
        if status:
            query = query.where(PlannedQuantity.status == status)
        
        if search:
            query = query.where(
                or_(
                    PlannedQuantity.item_name.ilike(f"%{search}%"),
                    PlannedQuantity.item_code.ilike(f"%{search}%")
                )
            )
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.order_by(desc(PlannedQuantity.created_at)).offset(offset).limit(page_size)
        
        result = await self.session.execute(query)
        return result.scalars().all(), total
    
    async def get_planned_quantity_by_id(self, quantity_id: str) -> Optional[PlannedQuantity]:
        """Get a single planned quantity"""
        result = await self.session.execute(
            select(PlannedQuantity).where(PlannedQuantity.id == quantity_id)
        )
        return result.scalar_one_or_none()
    
    async def create_planned_quantity(self, data: Dict) -> PlannedQuantity:
        """Create a new planned quantity"""
        quantity = PlannedQuantity(
            id=str(uuid.uuid4()),
            **data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.session.add(quantity)
        await self.session.commit()
        await self.session.refresh(quantity)
        return quantity
    
    async def update_planned_quantity(
        self, 
        quantity_id: str, 
        updates: Dict
    ) -> Optional[PlannedQuantity]:
        """Update a planned quantity"""
        quantity = await self.get_planned_quantity_by_id(quantity_id)
        if not quantity:
            return None
        
        for key, value in updates.items():
            if hasattr(quantity, key) and value is not None:
                setattr(quantity, key, value)
        
        quantity.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(quantity)
        return quantity
    
    async def delete_planned_quantity(self, quantity_id: str) -> bool:
        """Delete a planned quantity"""
        quantity = await self.get_planned_quantity_by_id(quantity_id)
        if not quantity:
            return False
        
        await self.session.delete(quantity)
        await self.session.commit()
        return True
    
    # ==================== DASHBOARD STATS ====================
    
    async def get_dashboard_stats(self) -> Dict:
        """Get quantity engineer dashboard statistics"""
        # Total planned items
        total_result = await self.session.execute(
            select(func.count()).select_from(PlannedQuantity)
        )
        total_planned = total_result.scalar() or 0
        
        # Pending items
        pending_result = await self.session.execute(
            select(func.count()).select_from(PlannedQuantity)
            .where(PlannedQuantity.status == 'pending')
        )
        pending_count = pending_result.scalar() or 0
        
        # Items with remaining quantity
        remaining_result = await self.session.execute(
            select(func.count()).select_from(PlannedQuantity)
            .where(PlannedQuantity.remaining_quantity > 0)
        )
        with_remaining = remaining_result.scalar() or 0
        
        # High priority items
        high_priority_result = await self.session.execute(
            select(func.count()).select_from(PlannedQuantity)
            .where(PlannedQuantity.priority == 1)
        )
        high_priority = high_priority_result.scalar() or 0
        
        return {
            "total_planned_items": total_planned,
            "pending_items": pending_count,
            "items_with_remaining": with_remaining,
            "high_priority_items": high_priority
        }
    
    # ==================== REPORTS ====================
    
    async def get_summary_report(self, project_id: Optional[str] = None) -> Dict:
        """Get summary report for planned quantities"""
        query = select(PlannedQuantity)
        
        if project_id:
            query = query.where(PlannedQuantity.project_id == project_id)
        
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        total_planned_qty = sum(item.planned_quantity or 0 for item in items)
        total_ordered_qty = sum(item.ordered_quantity or 0 for item in items)
        total_remaining_qty = sum(item.remaining_quantity or 0 for item in items)
        
        # Status breakdown
        status_counts = {}
        for item in items:
            status = item.status or 'unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_items": len(items),
            "total_planned_quantity": total_planned_qty,
            "total_ordered_quantity": total_ordered_qty,
            "total_remaining_quantity": total_remaining_qty,
            "status_breakdown": status_counts
        }
    
    async def get_alerts(self, days_threshold: int = 7) -> List[Dict]:
        """Get alerts for items needing attention"""
        threshold_date = datetime.utcnow() + timedelta(days=days_threshold)
        
        # Items with expected order date coming soon
        result = await self.session.execute(
            select(PlannedQuantity)
            .where(
                and_(
                    PlannedQuantity.expected_order_date <= threshold_date,
                    PlannedQuantity.remaining_quantity > 0,
                    PlannedQuantity.status != 'completed'
                )
            )
            .order_by(PlannedQuantity.expected_order_date)
            .limit(20)
        )
        items = result.scalars().all()
        
        return [
            {
                "id": item.id,
                "item_name": item.item_name,
                "project_name": item.project_name,
                "remaining_quantity": item.remaining_quantity,
                "expected_order_date": item.expected_order_date.isoformat() if item.expected_order_date else None,
                "priority": item.priority,
                "alert_type": "upcoming_order"
            }
            for item in items
        ]
    
    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

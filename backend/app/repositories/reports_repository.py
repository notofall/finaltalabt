"""
Reports Repository - Data access layer for reports and analytics
مستودع التقارير - طبقة الوصول للبيانات
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import (
    PurchaseOrder, PurchaseOrderItem, Project, BudgetCategory,
    Supplier, MaterialRequest, PriceCatalogItem
)


class ReportsRepository:
    """Repository for reports data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== Dashboard Stats ====================
    
    async def count_projects(self) -> int:
        """Count total projects"""
        result = await self.session.execute(
            select(func.count()).select_from(Project)
        )
        return result.scalar() or 0
    
    async def count_active_projects(self) -> int:
        """Count active projects"""
        result = await self.session.execute(
            select(func.count()).select_from(Project)
            .where(Project.status == "active")
        )
        return result.scalar() or 0
    
    async def count_orders(self) -> int:
        """Count total orders"""
        result = await self.session.execute(
            select(func.count()).select_from(PurchaseOrder)
        )
        return result.scalar() or 0
    
    async def count_orders_by_status(self, statuses: List[str]) -> int:
        """Count orders by status list"""
        result = await self.session.execute(
            select(func.count()).select_from(PurchaseOrder)
            .where(PurchaseOrder.status.in_(statuses))
        )
        return result.scalar() or 0
    
    async def get_approved_orders_total(self) -> float:
        """Get total amount of approved orders"""
        result = await self.session.execute(
            select(func.sum(PurchaseOrder.total_amount))
            .where(PurchaseOrder.status == "approved")
        )
        return result.scalar() or 0
    
    async def count_requests(self) -> int:
        """Count total material requests"""
        result = await self.session.execute(
            select(func.count()).select_from(MaterialRequest)
        )
        return result.scalar() or 0
    
    async def count_pending_requests(self) -> int:
        """Count pending material requests"""
        result = await self.session.execute(
            select(func.count()).select_from(MaterialRequest)
            .where(MaterialRequest.status == "pending")
        )
        return result.scalar() or 0
    
    async def count_suppliers(self) -> int:
        """Count total suppliers"""
        result = await self.session.execute(
            select(func.count()).select_from(Supplier)
        )
        return result.scalar() or 0
    
    async def count_recent_orders(self, days: int = 7) -> int:
        """Count orders in last N days"""
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) - timedelta(days=days)
        result = await self.session.execute(
            select(func.count()).select_from(PurchaseOrder)
            .where(PurchaseOrder.created_at >= cutoff)
        )
        return result.scalar() or 0
    
    # ==================== Budget Reports ====================
    
    async def get_budget_categories(
        self, 
        project_id: Optional[str] = None
    ) -> List[BudgetCategory]:
        """Get budget categories"""
        query = select(BudgetCategory)
        if project_id:
            query = query.where(BudgetCategory.project_id == project_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_spent_by_category(self, category_id: str) -> float:
        """Get spent amount for a budget category"""
        result = await self.session.execute(
            select(func.sum(PurchaseOrder.total_amount))
            .where(
                and_(
                    PurchaseOrder.category_id == category_id,
                    PurchaseOrder.status == "approved"
                )
            )
        )
        return result.scalar() or 0
    
    # ==================== Project Reports ====================
    
    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()
    
    async def get_projects_by_ids(self, project_ids: List[str]) -> List[Project]:
        """Get projects by list of IDs"""
        if not project_ids:
            return []
        result = await self.session.execute(
            select(Project).where(Project.id.in_(project_ids))
        )
        return list(result.scalars().all())
    
    async def get_orders_by_project(self, project_id: str) -> List[PurchaseOrder]:
        """Get orders for project"""
        result = await self.session.execute(
            select(PurchaseOrder).where(PurchaseOrder.project_id == project_id)
        )
        return list(result.scalars().all())
    
    async def get_budget_categories_by_project(
        self, 
        project_id: str
    ) -> List[BudgetCategory]:
        """Get budget categories for project"""
        result = await self.session.execute(
            select(BudgetCategory).where(BudgetCategory.project_id == project_id)
        )
        return list(result.scalars().all())
    
    async def get_requests_by_project(
        self, 
        project_id: str
    ) -> List[MaterialRequest]:
        """Get material requests for project"""
        result = await self.session.execute(
            select(MaterialRequest).where(MaterialRequest.project_id == project_id)
        )
        return list(result.scalars().all())
    
    # ==================== Cost Savings ====================
    
    async def get_approved_orders_with_limit(
        self, 
        limit: int = 100
    ) -> List[PurchaseOrder]:
        """Get recent approved orders"""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.status == "approved")
            .order_by(desc(PurchaseOrder.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_order_items(self, order_id: str) -> List[PurchaseOrderItem]:
        """Get items for an order"""
        result = await self.session.execute(
            select(PurchaseOrderItem)
            .where(PurchaseOrderItem.order_id == order_id)
        )
        return list(result.scalars().all())
    
    async def get_catalog_item(
        self, 
        item_id: str
    ) -> Optional[PriceCatalogItem]:
        """Get catalog item by ID"""
        result = await self.session.execute(
            select(PriceCatalogItem).where(PriceCatalogItem.id == item_id)
        )
        return result.scalar_one_or_none()
    
    # ==================== Advanced Reports ====================
    
    async def get_orders_with_filters(
        self,
        project_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PurchaseOrder]:
        """Get orders with filters"""
        filters = []
        
        if project_id:
            filters.append(PurchaseOrder.project_id == project_id)
        if supplier_id:
            filters.append(PurchaseOrder.supplier_id == supplier_id)
        if start_date:
            filters.append(PurchaseOrder.created_at >= start_date)
        if end_date:
            filters.append(PurchaseOrder.created_at <= end_date)
        
        query = select(PurchaseOrder)
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_requests_with_filters(
        self,
        project_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[MaterialRequest]:
        """Get material requests with filters"""
        filters = []
        
        if project_id:
            filters.append(MaterialRequest.project_id == project_id)
        if start_date:
            filters.append(MaterialRequest.created_at >= start_date)
        if end_date:
            filters.append(MaterialRequest.created_at <= end_date)
        
        query = select(MaterialRequest)
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_price_variance_items(
        self, 
        item_name: Optional[str] = None
    ) -> List[PurchaseOrderItem]:
        """Get order items for price variance analysis"""
        query = select(PurchaseOrderItem)
        
        if item_name:
            query = query.where(PurchaseOrderItem.name.ilike(f"%{item_name}%"))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

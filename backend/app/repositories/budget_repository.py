"""
Budget Repository
فصل طبقة الوصول لقاعدة البيانات للميزانيات
"""
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import BudgetCategory, DefaultBudgetCategory


class BudgetRepository:
    """Repository for Budget Categories (handles both Default and Project categories)"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== Default Budget Categories ====================
    
    async def get_all_default_categories(self) -> List[DefaultBudgetCategory]:
        """Get all default budget categories"""
        result = await self.session.execute(
            select(DefaultBudgetCategory).order_by(DefaultBudgetCategory.created_at)
        )
        return list(result.scalars().all())
    
    async def get_default_category_by_id(self, category_id: str) -> Optional[DefaultBudgetCategory]:
        """Get default category by ID"""
        result = await self.session.execute(
            select(DefaultBudgetCategory).where(DefaultBudgetCategory.id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def create_default_category(self, category: DefaultBudgetCategory) -> DefaultBudgetCategory:
        """Create default budget category"""
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category
    
    async def update_default_category(self, category_id: str, data: dict) -> Optional[DefaultBudgetCategory]:
        """Update default budget category"""
        category = await self.get_default_category_by_id(category_id)
        if category:
            for key, value in data.items():
                if hasattr(category, key) and value is not None:
                    setattr(category, key, value)
            await self.session.flush()
            await self.session.refresh(category)
        return category
    
    async def delete_default_category(self, category_id: str) -> bool:
        """Delete default budget category"""
        category = await self.get_default_category_by_id(category_id)
        if category:
            await self.session.delete(category)
            await self.session.flush()
            return True
        return False
    
    async def count_default_categories(self) -> int:
        """Count default categories"""
        result = await self.session.execute(
            select(func.count(DefaultBudgetCategory.id))
        )
        return result.scalar_one()
    
    # ==================== Project Budget Categories ====================
    
    async def get_categories_by_project(self, project_id: str) -> List[BudgetCategory]:
        """Get budget categories for a project"""
        result = await self.session.execute(
            select(BudgetCategory)
            .where(BudgetCategory.project_id == project_id)
            .order_by(BudgetCategory.code)
        )
        return list(result.scalars().all())
    
    async def get_all_categories(self) -> List[BudgetCategory]:
        """Get all budget categories"""
        result = await self.session.execute(
            select(BudgetCategory).order_by(BudgetCategory.code)
        )
        return list(result.scalars().all())
    
    async def get_category_by_id(self, category_id: str) -> Optional[BudgetCategory]:
        """Get budget category by ID"""
        result = await self.session.execute(
            select(BudgetCategory).where(BudgetCategory.id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def create_category(self, category: BudgetCategory) -> BudgetCategory:
        """Create budget category"""
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category
    
    async def update_category(self, category_id: str, data: dict) -> Optional[BudgetCategory]:
        """Update budget category"""
        category = await self.get_category_by_id(category_id)
        if category:
            for key, value in data.items():
                if hasattr(category, key) and value is not None:
                    setattr(category, key, value)
            await self.session.flush()
            await self.session.refresh(category)
        return category
    
    async def delete_category(self, category_id: str) -> bool:
        """Delete budget category"""
        category = await self.get_category_by_id(category_id)
        if category:
            await self.session.delete(category)
            await self.session.flush()
            return True
        return False
    
    async def count_categories_by_project(self, project_id: str) -> int:
        """Count categories for a project"""
        result = await self.session.execute(
            select(func.count(BudgetCategory.id))
            .where(BudgetCategory.project_id == project_id)
        )
        return result.scalar_one()
    
    async def get_next_category_code(self, project_id: str) -> str:
        """Generate next category code for project"""
        count = await self.count_categories_by_project(project_id)
        return f"BC-{count + 1:03d}"

"""
Budget Service
فصل منطق العمل للميزانيات
"""
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timezone

from database import BudgetCategory, DefaultBudgetCategory
from app.repositories.budget_repository import BudgetRepository
from .base import BaseService


class BudgetService(BaseService):
    """Service for budget management"""
    
    def __init__(self, budget_repo: BudgetRepository):
        self.budget_repo = budget_repo
    
    # ==================== Default Budget Categories ====================
    
    async def get_all_default_categories(self) -> List[DefaultBudgetCategory]:
        """Get all default budget categories"""
        return await self.budget_repo.get_all_default_categories()
    
    async def get_default_category_by_id(self, category_id: str) -> Optional[DefaultBudgetCategory]:
        """Get default category by ID"""
        return await self.budget_repo.get_default_category_by_id(category_id)
    
    async def create_default_category(
        self, 
        name: str, 
        code: str = None,
        default_budget: float = 0,
        created_by: str = None,
        created_by_name: str = None
    ) -> DefaultBudgetCategory:
        """Create a new default budget category"""
        category = DefaultBudgetCategory(
            id=str(uuid4()),
            name=name,
            code=code,
            default_budget=default_budget,
            created_by=created_by,
            created_by_name=created_by_name,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        return await self.budget_repo.create_default_category(category)
    
    async def update_default_category(self, category_id: str, data: dict) -> Optional[DefaultBudgetCategory]:
        """Update default budget category"""
        return await self.budget_repo.update_default_category(category_id, data)
    
    async def delete_default_category(self, category_id: str) -> bool:
        """Delete default budget category"""
        return await self.budget_repo.delete_default_category(category_id)
    
    async def count_default_categories(self) -> int:
        """Count default categories"""
        return await self.budget_repo.count_default_categories()
    
    # ==================== Project Budget Categories ====================
    
    async def get_categories_by_project(self, project_id: str) -> List[BudgetCategory]:
        """Get budget categories for a project"""
        return await self.budget_repo.get_categories_by_project(project_id)
    
    async def get_all_categories(self) -> List[BudgetCategory]:
        """Get all budget categories"""
        return await self.budget_repo.get_all_categories()
    
    async def get_category_by_id(self, category_id: str) -> Optional[BudgetCategory]:
        """Get budget category by ID"""
        return await self.budget_repo.get_category_by_id(category_id)
    
    async def create_category(
        self, 
        name: str, 
        project_id: str, 
        estimated_budget: float,
        code: Optional[str] = None,
        project_name: str = "",
        created_by: str = "system",
        created_by_name: str = "النظام"
    ) -> BudgetCategory:
        """Create a new budget category for a project"""
        # Generate code if not provided
        if not code:
            code = await self.budget_repo.get_next_category_code(project_id)
        
        category = BudgetCategory(
            id=str(uuid4()),
            name=name,
            project_id=project_id,
            project_name=project_name,
            estimated_budget=estimated_budget,
            code=code,
            created_by=created_by,
            created_by_name=created_by_name,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        return await self.budget_repo.create_category(category)
    
    async def update_category(self, category_id: str, data: dict) -> Optional[BudgetCategory]:
        """Update budget category"""
        return await self.budget_repo.update_category(category_id, data)
    
    async def delete_category(self, category_id: str) -> bool:
        """Delete budget category"""
        return await self.budget_repo.delete_category(category_id)
    
    async def apply_defaults_to_project(self, project_id: str, project_name: str = "", created_by: str = "system", created_by_name: str = "النظام") -> List[BudgetCategory]:
        """Apply default categories to a project"""
        # Get all default categories
        defaults = await self.budget_repo.get_all_default_categories()
        
        # Check existing categories for this project
        existing = await self.budget_repo.get_categories_by_project(project_id)
        existing_names = {c.name for c in existing}
        
        created = []
        for default in defaults:
            if default.name not in existing_names:
                # Use the default category code if available
                category_code = getattr(default, 'code', None)
                category = await self.create_category(
                    name=default.name,
                    project_id=project_id,
                    estimated_budget=default.default_budget,
                    code=category_code,
                    project_name=project_name,
                    created_by=created_by,
                    created_by_name=created_by_name
                )
                created.append(category)
        
        return created
    
    async def get_project_budget_summary(self, project_id: str) -> dict:
        """Get budget summary for a project"""
        categories = await self.budget_repo.get_categories_by_project(project_id)
        
        total_estimated = sum(c.estimated_budget or 0 for c in categories)
        total_spent = sum(c.actual_spent or 0 for c in categories)
        
        return {
            "project_id": project_id,
            "categories_count": len(categories),
            "total_budget": total_estimated,
            "total_estimated": total_estimated,
            "total_spent": total_spent,
            "remaining": total_estimated - total_spent,
            "utilization_percentage": round((total_spent / total_estimated * 100) if total_estimated > 0 else 0, 2)
        }

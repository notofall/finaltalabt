"""
Project Repository
فصل طبقة الوصول لقاعدة البيانات للمشاريع
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import Project, MaterialRequest, PurchaseOrder, BudgetCategory
from .base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project entity"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[Project]:
        """Get project by ID"""
        result = await self.session.execute(
            select(Project).where(Project.id == str(id))
        )
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str) -> Optional[Project]:
        """Get project by code"""
        result = await self.session.execute(
            select(Project).where(Project.code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects with pagination"""
        result = await self.session.execute(
            select(Project)
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_active_projects(self) -> List[Project]:
        """Get all active projects"""
        result = await self.session.execute(
            select(Project).where(Project.status == "active")
        )
        return list(result.scalars().all())
    
    async def get_building_projects(self) -> List[Project]:
        """Get building projects only"""
        result = await self.session.execute(
            select(Project).where(Project.is_building_project == True)
        )
        return list(result.scalars().all())
    
    async def create(self, project: Project) -> Project:
        """Create new project"""
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)
        return project
    
    async def update(self, id: UUID, project_data: dict) -> Optional[Project]:
        """Update project"""
        project = await self.get_by_id(id)
        if project:
            for key, value in project_data.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            await self.session.flush()
            await self.session.refresh(project)
        return project
    
    async def delete(self, id: UUID) -> bool:
        """Delete project (soft delete by setting status to inactive)"""
        project = await self.get_by_id(id)
        if project:
            project.status = "inactive"
            await self.session.flush()
            return True
        return False
    
    async def count(self) -> int:
        """Count total projects"""
        result = await self.session.execute(
            select(func.count(Project.id))
        )
        return result.scalar_one()
    
    async def count_with_filter(self, status: str = None) -> int:
        """Count projects with optional status filter"""
        query = select(func.count(Project.id))
        if status:
            query = query.where(Project.status == status)
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def get_projects_with_stats_batch(
        self, 
        project_ids: List[str]
    ) -> dict:
        """
        Get stats for multiple projects in ONE query (solves N+1).
        Returns: {project_id: {total_requests, total_orders, total_budget, total_spent}}
        """
        if not project_ids:
            return {}
        
        # Request counts per project
        req_result = await self.session.execute(
            select(
                MaterialRequest.project_id,
                func.count(MaterialRequest.id)
            )
            .where(MaterialRequest.project_id.in_(project_ids))
            .group_by(MaterialRequest.project_id)
        )
        req_counts = {row[0]: row[1] for row in req_result.all()}
        
        # Order counts and spent per project
        order_result = await self.session.execute(
            select(
                PurchaseOrder.project_id,
                func.count(PurchaseOrder.id),
                func.coalesce(func.sum(PurchaseOrder.total_amount), 0)
            )
            .where(PurchaseOrder.project_id.in_(project_ids))
            .group_by(PurchaseOrder.project_id)
        )
        order_data = {row[0]: {"count": row[1], "spent": float(row[2])} for row in order_result.all()}
        
        # Budget per project
        budget_result = await self.session.execute(
            select(
                BudgetCategory.project_id,
                func.coalesce(func.sum(BudgetCategory.estimated_budget), 0)
            )
            .where(BudgetCategory.project_id.in_(project_ids))
            .group_by(BudgetCategory.project_id)
        )
        budget_data = {row[0]: float(row[1]) for row in budget_result.all()}
        
        # Build result for all projects
        result = {}
        for pid in project_ids:
            result[pid] = {
                "total_requests": req_counts.get(pid, 0),
                "total_orders": order_data.get(pid, {}).get("count", 0),
                "total_spent": order_data.get(pid, {}).get("spent", 0),
                "total_budget": budget_data.get(pid, 0)
            }
        
        return result
    
    async def get_project_full_stats(self, project_id: str) -> dict:
        """
        Get comprehensive project statistics.
        Includes: requests count, orders count, budget, spent.
        """
        # Request count
        req_result = await self.session.execute(
            select(func.count()).select_from(MaterialRequest)
            .where(MaterialRequest.project_id == project_id)
        )
        total_requests = req_result.scalar() or 0
        
        # Order count and spent
        order_result = await self.session.execute(
            select(
                func.count(),
                func.coalesce(func.sum(PurchaseOrder.total_amount), 0)
            ).select_from(PurchaseOrder)
            .where(PurchaseOrder.project_id == project_id)
        )
        order_row = order_result.one()
        total_orders = order_row[0] or 0
        total_spent = float(order_row[1] or 0)
        
        # Budget
        budget_result = await self.session.execute(
            select(func.coalesce(func.sum(BudgetCategory.estimated_budget), 0))
            .select_from(BudgetCategory)
            .where(BudgetCategory.project_id == project_id)
        )
        total_budget = float(budget_result.scalar() or 0)
        
        return {
            "total_requests": total_requests,
            "total_orders": total_orders,
            "total_budget": total_budget,
            "total_spent": total_spent
        }
    
    async def get_project_stats(self, project_id: UUID) -> dict:
        """Get basic project statistics"""
        project = await self.get_by_id(project_id)
        if not project:
            return {}
        
        return {
            "id": str(project.id),
            "name": project.name,
            "code": project.code,
            "total_area": project.total_area or 0,
            "floors_count": project.floors_count or 0,
            "is_building_project": project.is_building_project or False
        }

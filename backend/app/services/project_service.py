"""
Project Service
فصل منطق العمل للمشاريع ونظام العمائر
"""
from typing import Optional, List
from uuid import UUID

from database import Project
from app.repositories.project_repository import ProjectRepository
from app.repositories.supply_repository import SupplyRepository
from .base import BaseService


class ProjectService(BaseService[Project]):
    """Service for project operations"""
    
    def __init__(
        self, 
        project_repository: ProjectRepository,
        supply_repository: Optional[SupplyRepository] = None
    ):
        self.project_repo = project_repository
        self.supply_repo = supply_repository
    
    async def get_project(self, project_id: UUID) -> Optional[Project]:
        """Get project by ID"""
        return await self.project_repo.get_by_id(project_id)
    
    async def get_all_projects(self) -> List[Project]:
        """Get all projects"""
        return await self.project_repo.get_all()
    
    async def get_active_projects(self) -> List[Project]:
        """Get active projects only"""
        return await self.project_repo.get_active_projects()
    
    async def get_building_projects(self) -> List[Project]:
        """Get building projects for quantity engineer"""
        # Return projects with total_area > 0 as building projects
        all_projects = await self.project_repo.get_all()
        return [p for p in all_projects if (p.total_area or 0) > 0]
    
    async def create_project(
        self,
        name: str,
        code: str = None,
        description: str = "",
        total_area: float = 0,
        floors_count: int = 0,
        owner_name: str = "",
        location: str = None,
        created_by: str = "",
        created_by_name: str = "",
        supervisor_id: str = None,
        supervisor_name: str = None,
        engineer_id: str = None,
        engineer_name: str = None
    ) -> Project:
        """Create new project"""
        from datetime import datetime, timezone
        
        # التحقق من عدم تكرار كود المشروع
        if code:
            existing = await self.project_repo.get_by_code(code)
            if existing:
                raise ValueError(f"كود المشروع '{code}' مستخدم بالفعل")
        
        project = Project(
            name=name,
            code=code,
            owner_name=owner_name or name,  # Use name as default owner_name
            description=description,
            location=location,
            total_area=total_area,
            floors_count=floors_count,
            status="active",
            supervisor_id=supervisor_id,
            supervisor_name=supervisor_name,
            engineer_id=engineer_id,
            engineer_name=engineer_name,
            created_by=created_by or "system",
            created_by_name=created_by_name or "النظام",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        return await self.project_repo.create(project)
    
    async def update_project(
        self, 
        project_id: UUID, 
        project_data: dict
    ) -> Optional[Project]:
        """Update project"""
        return await self.project_repo.update(project_id, project_data)
    
    async def delete_project(self, project_id: UUID) -> bool:
        """Delete project (soft delete)"""
        return await self.project_repo.delete(project_id)
    
    async def get_project_dashboard(self, project_id: UUID) -> dict:
        """Get project dashboard data"""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return {}
        
        result = {
            "project": {
                "id": str(project.id),
                "name": project.name,
                "code": project.code,
                "total_area": project.total_area or 0,
                "floors_count": project.floors_count or 0,
                "is_building_project": project.is_building_project or False
            }
        }
        
        # Add supply summary if available
        if self.supply_repo:
            supply_summary = await self.supply_repo.get_project_summary(project_id)
            result["supply"] = supply_summary
        
        return result
    
    async def get_projects_summary(self) -> dict:
        """Get summary of all projects"""
        all_projects = await self.project_repo.get_all()
        active = [p for p in all_projects if p.status == "active"]
        
        total_area = sum(p.total_area or 0 for p in all_projects)
        
        return {
            "total_projects": len(all_projects),
            "active_projects": len(active),
            "total_area": total_area
        }
    
    async def get_projects_with_stats_batch(self, project_ids: List[str]) -> dict:
        """Get stats for multiple projects in batch (solves N+1)"""
        return await self.project_repo.get_projects_with_stats_batch(project_ids)
    
    async def count_projects(self, status: str = None) -> int:
        """Count projects with optional status filter"""
        return await self.project_repo.count_with_filter(status)
    
    async def get_project_full_stats(self, project_id: str) -> dict:
        """Get comprehensive project statistics via Repository"""
        return await self.project_repo.get_project_full_stats(project_id)

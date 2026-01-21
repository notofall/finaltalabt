"""
Supply Tracking Repository
فصل طبقة الوصول لقاعدة البيانات لتتبع التوريد
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import SupplyTracking
from .base import BaseRepository


class SupplyRepository(BaseRepository[SupplyTracking]):
    """Repository for SupplyTracking entity"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[SupplyTracking]:
        """Get supply item by ID"""
        result = await self.session.execute(
            select(SupplyTracking).where(SupplyTracking.id == str(id))
        )
        return result.scalar_one_or_none()
    
    async def get_by_project(self, project_id: UUID) -> List[SupplyTracking]:
        """Get all supply items for a project"""
        result = await self.session.execute(
            select(SupplyTracking)
            .where(SupplyTracking.project_id == str(project_id))
        )
        return list(result.scalars().all())
    
    async def get_by_project_and_item(
        self, 
        project_id: UUID, 
        catalog_item_id: UUID
    ) -> Optional[SupplyTracking]:
        """Get supply item by project and catalog item"""
        result = await self.session.execute(
            select(SupplyTracking)
            .where(
                SupplyTracking.project_id == str(project_id),
                SupplyTracking.catalog_item_id == str(catalog_item_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[SupplyTracking]:
        """Get all supply items with pagination"""
        result = await self.session.execute(
            select(SupplyTracking)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, supply: SupplyTracking) -> SupplyTracking:
        """Create new supply tracking item"""
        self.session.add(supply)
        await self.session.flush()
        await self.session.refresh(supply)
        return supply
    
    async def update(self, id: UUID, supply_data: dict) -> Optional[SupplyTracking]:
        """Update supply item"""
        supply = await self.get_by_id(id)
        if supply:
            for key, value in supply_data.items():
                if hasattr(supply, key):
                    setattr(supply, key, value)
            await self.session.flush()
            await self.session.refresh(supply)
        return supply
    
    async def update_received_quantity(
        self, 
        project_id: UUID, 
        catalog_item_id: UUID, 
        quantity_to_add: float
    ) -> Optional[SupplyTracking]:
        """Update received quantity for a supply item"""
        supply = await self.get_by_project_and_item(project_id, catalog_item_id)
        if supply:
            supply.received_quantity = (supply.received_quantity or 0) + quantity_to_add
            await self.session.flush()
            await self.session.refresh(supply)
        return supply
    
    async def delete(self, id: UUID) -> bool:
        """Delete supply item"""
        supply = await self.get_by_id(id)
        if supply:
            await self.session.delete(supply)
            await self.session.flush()
            return True
        return False
    
    async def get_project_summary(self, project_id: UUID) -> dict:
        """Get supply summary for a project"""
        items = await self.get_by_project(project_id)
        
        total_required = sum(item.required_quantity or 0 for item in items)
        total_received = sum(item.received_quantity or 0 for item in items)
        
        completed = sum(1 for item in items 
                       if (item.received_quantity or 0) >= (item.required_quantity or 0))
        in_progress = sum(1 for item in items 
                         if 0 < (item.received_quantity or 0) < (item.required_quantity or 0))
        not_started = sum(1 for item in items 
                         if (item.received_quantity or 0) == 0)
        
        completion_rate = (total_received / total_required * 100) if total_required > 0 else 0
        
        return {
            "total_items": len(items),
            "completed_count": completed,
            "in_progress_count": in_progress,
            "not_started_count": not_started,
            "total_required": total_required,
            "total_received": total_received,
            "completion_percentage": round(completion_rate, 2)
        }

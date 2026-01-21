"""
Buildings Repository
فصل طبقة الوصول لقاعدة البيانات لنظام المباني
"""
from typing import Optional, List
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    UnitTemplate, UnitTemplateMaterial, ProjectFloor,
    ProjectAreaMaterial, SupplyTracking, Project
)


class BuildingsRepository:
    """Repository for Buildings System"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== Unit Templates ====================
    
    async def get_templates_by_project(self, project_id: str) -> List[UnitTemplate]:
        """Get all templates for a project"""
        result = await self.session.execute(
            select(UnitTemplate).where(UnitTemplate.project_id == project_id)
        )
        return list(result.scalars().all())
    
    async def get_template_by_id(self, template_id: str) -> Optional[UnitTemplate]:
        """Get template by ID"""
        result = await self.session.execute(
            select(UnitTemplate).where(UnitTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def create_template(self, template: UnitTemplate) -> UnitTemplate:
        """Create unit template"""
        self.session.add(template)
        await self.session.flush()
        await self.session.refresh(template)
        return template
    
    async def update_template(self, template_id: str, data: dict) -> Optional[UnitTemplate]:
        """Update template"""
        template = await self.get_template_by_id(template_id)
        if template:
            for key, value in data.items():
                if hasattr(template, key) and value is not None:
                    setattr(template, key, value)
            await self.session.flush()
            await self.session.refresh(template)
        return template
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete template and its materials"""
        template = await self.get_template_by_id(template_id)
        if template:
            # Delete materials first
            await self.session.execute(
                delete(UnitTemplateMaterial).where(UnitTemplateMaterial.template_id == template_id)
            )
            await self.session.delete(template)
            await self.session.flush()
            return True
        return False
    
    # ==================== Template Materials ====================
    
    async def get_template_materials(self, template_id: str) -> List[UnitTemplateMaterial]:
        """Get materials for a template"""
        result = await self.session.execute(
            select(UnitTemplateMaterial).where(UnitTemplateMaterial.template_id == template_id)
        )
        return list(result.scalars().all())
    
    async def add_template_material(self, material: UnitTemplateMaterial) -> UnitTemplateMaterial:
        """Add material to template"""
        self.session.add(material)
        await self.session.flush()
        await self.session.refresh(material)
        return material
    
    async def delete_template_material(self, material_id: str) -> bool:
        """Delete template material"""
        result = await self.session.execute(
            select(UnitTemplateMaterial).where(UnitTemplateMaterial.id == material_id)
        )
        material = result.scalar_one_or_none()
        if material:
            await self.session.delete(material)
            await self.session.flush()
            return True
        return False
    
    # ==================== Project Floors ====================
    
    async def get_floors_by_project(self, project_id: str) -> List[ProjectFloor]:
        """Get all floors for a project"""
        result = await self.session.execute(
            select(ProjectFloor)
            .where(ProjectFloor.project_id == project_id)
            .order_by(ProjectFloor.floor_number)
        )
        return list(result.scalars().all())
    
    async def get_floor_by_id(self, floor_id: str) -> Optional[ProjectFloor]:
        """Get floor by ID"""
        result = await self.session.execute(
            select(ProjectFloor).where(ProjectFloor.id == floor_id)
        )
        return result.scalar_one_or_none()
    
    async def create_floor(self, floor: ProjectFloor) -> ProjectFloor:
        """Create project floor"""
        self.session.add(floor)
        await self.session.flush()
        await self.session.refresh(floor)
        return floor
    
    async def update_floor(self, floor_id: str, data: dict) -> Optional[ProjectFloor]:
        """Update floor"""
        floor = await self.get_floor_by_id(floor_id)
        if floor:
            for key, value in data.items():
                if hasattr(floor, key) and value is not None:
                    setattr(floor, key, value)
            await self.session.flush()
            await self.session.refresh(floor)
        return floor
    
    async def delete_floor(self, floor_id: str) -> bool:
        """Delete floor"""
        floor = await self.get_floor_by_id(floor_id)
        if floor:
            await self.session.delete(floor)
            await self.session.flush()
            return True
        return False
    
    # ==================== Area Materials ====================
    
    async def get_area_materials_by_project(self, project_id: str) -> List[ProjectAreaMaterial]:
        """Get area materials for a project"""
        result = await self.session.execute(
            select(ProjectAreaMaterial).where(ProjectAreaMaterial.project_id == project_id)
        )
        return list(result.scalars().all())
    
    async def get_area_material_by_id(self, material_id: str) -> Optional[ProjectAreaMaterial]:
        """Get area material by ID"""
        result = await self.session.execute(
            select(ProjectAreaMaterial).where(ProjectAreaMaterial.id == material_id)
        )
        return result.scalar_one_or_none()
    
    async def create_area_material(self, material: ProjectAreaMaterial) -> ProjectAreaMaterial:
        """Create area material"""
        self.session.add(material)
        await self.session.flush()
        await self.session.refresh(material)
        return material
    
    async def update_area_material(self, material_id: str, data: dict) -> Optional[ProjectAreaMaterial]:
        """Update area material"""
        material = await self.get_area_material_by_id(material_id)
        if material:
            for key, value in data.items():
                if hasattr(material, key) and value is not None:
                    setattr(material, key, value)
            await self.session.flush()
            await self.session.refresh(material)
        return material
    
    async def delete_area_material(self, material_id: str) -> bool:
        """Delete area material"""
        material = await self.get_area_material_by_id(material_id)
        if material:
            await self.session.delete(material)
            await self.session.flush()
            return True
        return False
    
    # ==================== Supply Tracking ====================
    
    async def get_supply_by_project(self, project_id: str) -> List[SupplyTracking]:
        """Get supply tracking for a project"""
        result = await self.session.execute(
            select(SupplyTracking).where(SupplyTracking.project_id == project_id)
        )
        return list(result.scalars().all())
    
    async def get_supply_item_by_id(self, item_id: str) -> Optional[SupplyTracking]:
        """Get supply item by ID"""
        result = await self.session.execute(
            select(SupplyTracking).where(SupplyTracking.id == item_id)
        )
        return result.scalar_one_or_none()
    
    async def create_supply_item(self, item: SupplyTracking) -> SupplyTracking:
        """Create supply tracking item"""
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item
    
    async def update_supply_item(self, item_id: str, data: dict) -> Optional[SupplyTracking]:
        """Update supply item"""
        item = await self.get_supply_item_by_id(item_id)
        if item:
            for key, value in data.items():
                if hasattr(item, key) and value is not None:
                    setattr(item, key, value)
            await self.session.flush()
            await self.session.refresh(item)
        return item
    
    async def delete_supply_items_by_project(self, project_id: str) -> int:
        """Delete all supply items for a project"""
        result = await self.session.execute(
            delete(SupplyTracking).where(SupplyTracking.project_id == project_id)
        )
        await self.session.flush()
        return result.rowcount
    
    # ==================== Statistics ====================
    
    async def get_project_stats(self, project_id: str) -> dict:
        """Get project statistics"""
        templates = await self.get_templates_by_project(project_id)
        floors = await self.get_floors_by_project(project_id)
        
        total_units = sum(t.count for t in templates)
        total_area = sum(f.area for f in floors)
        
        return {
            "templates_count": len(templates),
            "floors_count": len(floors),
            "total_units": total_units,
            "total_area": total_area
        }

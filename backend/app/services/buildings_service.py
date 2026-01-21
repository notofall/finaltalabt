"""
Buildings Service
فصل منطق العمل لنظام المباني
"""
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timezone

from database.models import (
    UnitTemplate, UnitTemplateMaterial, ProjectFloor,
    ProjectAreaMaterial, SupplyTracking
)
from app.repositories.buildings_repository import BuildingsRepository
from .base import BaseService


class BuildingsService(BaseService):
    """Service for buildings system management"""
    
    def __init__(self, buildings_repo: BuildingsRepository):
        self.buildings_repo = buildings_repo
    
    # ==================== Unit Templates ====================
    
    async def get_templates_by_project(self, project_id: str) -> List[dict]:
        """Get all templates with materials for a project"""
        templates = await self.buildings_repo.get_templates_by_project(project_id)
        result = []
        for t in templates:
            materials = await self.buildings_repo.get_template_materials(t.id)
            result.append({
                "id": t.id,
                "code": t.code,
                "name": t.name,
                "description": t.description,
                "area": t.area,
                "rooms_count": t.rooms_count,
                "bathrooms_count": t.bathrooms_count,
                "count": t.count,
                "project_id": t.project_id,
                "materials": [{
                    "id": m.id,
                    "catalog_item_id": m.catalog_item_id,
                    "item_code": m.item_code,
                    "item_name": m.item_name,
                    "unit": m.unit,
                    "quantity_per_unit": m.quantity_per_unit,
                    "unit_price": m.unit_price
                } for m in materials],
                "created_at": t.created_at.isoformat() if t.created_at else None
            })
        return result
    
    async def get_template_by_id(self, template_id: str) -> Optional[UnitTemplate]:
        """Get template by ID"""
        return await self.buildings_repo.get_template_by_id(template_id)
    
    async def create_template(
        self,
        project_id: str,
        project_name: str,
        code: str,
        name: str,
        area: float = 0,
        rooms_count: int = 0,
        bathrooms_count: int = 0,
        count: int = 1,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        created_by_name: Optional[str] = None
    ) -> UnitTemplate:
        """Create unit template"""
        template = UnitTemplate(
            id=str(uuid4()),
            project_id=project_id,
            project_name=project_name,
            code=code,
            name=name,
            area=area,
            rooms_count=rooms_count,
            bathrooms_count=bathrooms_count,
            count=count,
            description=description,
            created_by=created_by,
            created_by_name=created_by_name,
            created_at=datetime.now(timezone.utc)
        )
        return await self.buildings_repo.create_template(template)
    
    async def update_template(self, template_id: str, data: dict) -> Optional[UnitTemplate]:
        """Update template"""
        return await self.buildings_repo.update_template(template_id, data)
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete template"""
        return await self.buildings_repo.delete_template(template_id)
    
    async def add_template_material(
        self,
        template_id: str,
        catalog_item_id: str,
        item_code: str,
        item_name: str,
        unit: str,
        quantity_per_unit: float,
        unit_price: float = 0
    ) -> UnitTemplateMaterial:
        """Add material to template"""
        material = UnitTemplateMaterial(
            id=str(uuid4()),
            template_id=template_id,
            catalog_item_id=catalog_item_id,
            item_code=item_code,
            item_name=item_name,
            unit=unit,
            quantity_per_unit=quantity_per_unit,
            unit_price=unit_price
        )
        return await self.buildings_repo.add_template_material(material)
    
    async def delete_template_material(self, material_id: str) -> bool:
        """Delete template material"""
        return await self.buildings_repo.delete_template_material(material_id)
    
    # ==================== Project Floors ====================
    
    async def get_floors_by_project(self, project_id: str) -> List[ProjectFloor]:
        """Get all floors for a project"""
        return await self.buildings_repo.get_floors_by_project(project_id)
    
    async def create_floor(
        self,
        project_id: str,
        floor_number: int,
        floor_name: str,
        area: float,
        steel_factor: float = 100,
        created_by: Optional[str] = None,
        created_by_name: Optional[str] = None
    ) -> ProjectFloor:
        """Create project floor"""
        floor = ProjectFloor(
            id=str(uuid4()),
            project_id=project_id,
            floor_number=floor_number,
            floor_name=floor_name,
            area=area,
            steel_factor=steel_factor
        )
        return await self.buildings_repo.create_floor(floor)
    
    async def update_floor(self, floor_id: str, data: dict) -> Optional[ProjectFloor]:
        """Update floor"""
        return await self.buildings_repo.update_floor(floor_id, data)
    
    async def delete_floor(self, floor_id: str) -> bool:
        """Delete floor"""
        return await self.buildings_repo.delete_floor(floor_id)
    
    # ==================== Area Materials ====================
    
    async def get_area_materials_by_project(self, project_id: str) -> List[ProjectAreaMaterial]:
        """Get area materials for a project"""
        return await self.buildings_repo.get_area_materials_by_project(project_id)
    
    async def create_area_material(
        self,
        project_id: str,
        catalog_item_id: str,
        item_name: str,
        unit: str,
        factor: float,
        unit_price: float = 0,
        created_by: Optional[str] = None,
        created_by_name: Optional[str] = None
    ) -> ProjectAreaMaterial:
        """Create area material"""
        material = ProjectAreaMaterial(
            id=str(uuid4()),
            project_id=project_id,
            catalog_item_id=catalog_item_id,
            item_name=item_name,
            unit=unit,
            factor=factor,
            unit_price=unit_price,
            created_at=datetime.now(timezone.utc)
        )
        return await self.buildings_repo.create_area_material(material)
    
    async def update_area_material(self, material_id: str, data: dict) -> Optional[ProjectAreaMaterial]:
        """Update area material"""
        return await self.buildings_repo.update_area_material(material_id, data)
    
    async def delete_area_material(self, material_id: str) -> bool:
        """Delete area material"""
        return await self.buildings_repo.delete_area_material(material_id)
    
    # ==================== Supply Tracking ====================
    
    async def get_supply_by_project(self, project_id: str) -> List[SupplyTracking]:
        """Get supply tracking for a project"""
        return await self.buildings_repo.get_supply_by_project(project_id)
    
    async def update_supply_item(self, item_id: str, data: dict) -> Optional[SupplyTracking]:
        """Update supply item"""
        return await self.buildings_repo.update_supply_item(item_id, data)
    
    # ==================== Calculations ====================
    
    async def calculate_project_quantities(self, project_id: str) -> dict:
        """Calculate all quantities for a project"""
        templates = await self.buildings_repo.get_templates_by_project(project_id)
        floors = await self.buildings_repo.get_floors_by_project(project_id)
        area_materials = await self.buildings_repo.get_area_materials_by_project(project_id)
        
        # Calculate total area
        total_area = sum(f.area for f in floors)
        
        # Calculate total units
        total_units = sum(t.count for t in templates)
        
        # Calculate steel
        steel_calculation = {
            "floors": [{
                "floor_name": f.floor_name,
                "floor_number": f.floor_number,
                "area": f.area,
                "steel_factor": f.steel_factor,
                "steel_tons": round((f.area * f.steel_factor) / 1000, 2)
            } for f in floors],
            "total_steel_tons": round(sum((f.area * f.steel_factor) / 1000 for f in floors), 2)
        }
        
        # Calculate unit materials
        unit_materials = []
        for template in templates:
            materials = await self.buildings_repo.get_template_materials(template.id)
            for m in materials:
                quantity = m.quantity_per_unit * template.count
                total_price = quantity * m.unit_price
                unit_materials.append({
                    "item_code": m.item_code,
                    "item_name": m.item_name,
                    "unit": m.unit,
                    "quantity": quantity,
                    "unit_price": m.unit_price,
                    "total_price": total_price
                })
        
        # Calculate area materials with advanced options
        area_mats = []
        for m in area_materials:
            # Get calculation method (factor or direct)
            calc_method = getattr(m, 'calculation_method', 'factor') or 'factor'
            
            # Determine area to use
            if getattr(m, 'calculation_type', 'all_floors') == 'selected_floor' and getattr(m, 'selected_floor_id', None):
                # Use specific floor area
                floor_area = next((f.area for f in floors if str(f.id) == m.selected_floor_id), 0)
                selected_floor_name = next((f.floor_name for f in floors if str(f.id) == m.selected_floor_id), "")
            else:
                # Use total area from all floors
                floor_area = total_area
                selected_floor_name = "جميع الأدوار"
            
            # Calculate base quantity
            if calc_method == 'direct':
                # Direct quantity input
                base_quantity = getattr(m, 'direct_quantity', 0) or 0
            else:
                # Calculate by factor
                base_quantity = floor_area * m.factor
            
            # Handle tile calculation (by dimensions)
            tile_width = getattr(m, 'tile_width', 0) or 0
            tile_height = getattr(m, 'tile_height', 0) or 0
            tiles_count = 0
            
            if tile_width > 0 and tile_height > 0:
                # Calculate tiles count: area / (width * height in m²)
                tile_area_m2 = (tile_width / 100) * (tile_height / 100)  # Convert cm to m
                if tile_area_m2 > 0:
                    tiles_count = floor_area / tile_area_m2
                    base_quantity = tiles_count  # Override with tiles count
            
            # Apply waste percentage
            waste_pct = getattr(m, 'waste_percentage', 0) or 0
            original_quantity = base_quantity
            quantity_with_waste = base_quantity * (1 + waste_pct / 100)
            
            total_price = quantity_with_waste * m.unit_price
            
            area_mats.append({
                "id": str(m.id),
                "item_name": m.item_name,
                "unit": m.unit,
                "calculation_method": calc_method,
                "factor": m.factor,
                "floor_name": selected_floor_name,
                "floor_area": floor_area,
                "tile_dimensions": f"{int(tile_width)}×{int(tile_height)}" if tile_width > 0 else None,
                "tiles_count": round(tiles_count) if tiles_count > 0 else None,
                "waste_percentage": waste_pct,
                "original_quantity": round(original_quantity, 2),
                "quantity": round(quantity_with_waste, 2),
                "unit_price": m.unit_price,
                "total_price": round(total_price, 2)
            })
        
        return {
            "project_id": project_id,
            "total_area": total_area,
            "total_units": total_units,
            "steel_calculation": steel_calculation,
            "materials": unit_materials,
            "area_materials": area_mats,
            "total_unit_materials_cost": sum(m["total_price"] for m in unit_materials),
            "total_area_materials_cost": sum(m["total_price"] for m in area_mats),
            "total_materials_cost": sum(m["total_price"] for m in unit_materials) + sum(m["total_price"] for m in area_mats)
        }
    
    # ==================== Statistics ====================
    
    async def get_project_stats(self, project_id: str) -> dict:
        """Get project statistics"""
        return await self.buildings_repo.get_project_stats(project_id)

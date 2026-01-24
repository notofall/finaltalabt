"""
Catalog Service
فصل منطق العمل للكتالوج
"""
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timezone

from database import PriceCatalogItem as PriceCatalog, ItemAlias
from app.repositories.catalog_repository import CatalogRepository
from .base import BaseService


class CatalogService(BaseService):
    """Service for catalog management"""
    
    def __init__(self, catalog_repo: CatalogRepository):
        self.catalog_repo = catalog_repo
    
    # ==================== Price Catalog ====================
    
    async def get_all_items(self, skip: int = 0, limit: int = 100) -> List[PriceCatalog]:
        """Get all catalog items"""
        return await self.catalog_repo.get_all_items(skip, limit)
    
    async def get_item_by_id(self, item_id: str) -> Optional[PriceCatalog]:
        """Get item by ID"""
        return await self.catalog_repo.get_item_by_id(item_id)
    
    async def get_item_by_code(self, code: str) -> Optional[PriceCatalog]:
        """Get item by code"""
        return await self.catalog_repo.get_item_by_code(code)
    
    async def search_items(self, query: str, limit: int = 50) -> List[PriceCatalog]:
        """Search items"""
        return await self.catalog_repo.search_items(query, limit)
    
    async def get_items_by_category(self, category: str) -> List[PriceCatalog]:
        """Get items by category"""
        return await self.catalog_repo.get_items_by_category(category)
    
    async def create_item(
        self,
        name: str,
        unit: str,
        price: float,
        category_name: Optional[str] = None,
        category_code: Optional[str] = None,
        item_code: Optional[str] = None,
        description: Optional[str] = None,
        supplier_id: Optional[str] = None,
        supplier_name: Optional[str] = None,
        created_by: Optional[str] = None,
        created_by_name: Optional[str] = None
    ) -> PriceCatalog:
        """Create new catalog item"""
        # Auto-generate code if not provided, based on category code
        if not item_code:
            item_code = await self.catalog_repo.get_next_code_by_category(category_code, category_name)
        
        # التحقق من عدم تكرار الكود
        if item_code:
            existing = await self.catalog_repo.get_item_by_code(item_code)
            if existing:
                raise ValueError(f"كود الصنف '{item_code}' مستخدم بالفعل")
        
        item = PriceCatalog(
            id=str(uuid4()),
            item_code=item_code,
            name=name,
            unit=unit,
            price=price,
            category_name=category_name,
            description=description,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            created_by=created_by,
            created_by_name=created_by_name,
            is_active=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        return await self.catalog_repo.create_item(item)
    
    async def update_item(self, item_id: str, data: dict) -> Optional[PriceCatalog]:
        """Update catalog item"""
        return await self.catalog_repo.update_item(item_id, data)
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete catalog item"""
        return await self.catalog_repo.delete_item(item_id)
    
    async def count_items(self) -> int:
        """Count items"""
        return await self.catalog_repo.count_items()
    
    async def get_categories(self) -> List[str]:
        """Get distinct categories"""
        return await self.catalog_repo.get_categories()
    
    # ==================== Item Aliases ====================
    
    async def get_all_aliases(self) -> List[ItemAlias]:
        """Get all aliases"""
        return await self.catalog_repo.get_all_aliases()
    
    async def find_alias(self, alias_name: str) -> Optional[ItemAlias]:
        """Find alias by name"""
        return await self.catalog_repo.find_alias(alias_name)
    
    async def create_alias(
        self,
        alias_name: str,
        catalog_item_id: str,
        created_by: Optional[str] = None
    ) -> ItemAlias:
        """Create item alias"""
        alias = ItemAlias(
            id=str(uuid4()),
            alias_name=alias_name,
            catalog_item_id=catalog_item_id,
            created_by=created_by,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        return await self.catalog_repo.create_alias(alias)
    
    async def delete_alias(self, alias_id: str) -> bool:
        """Delete alias"""
        return await self.catalog_repo.delete_alias(alias_id)
    
    async def suggest_standard_name(self, item_name: str) -> dict:
        """Suggest standard name for an item - يبحث في الأسماء البديلة والكتالوج"""
        from sqlalchemy import select, or_
        from database.models import PriceCatalogItem, ItemAlias
        
        result = {
            "found": False,
            "match_type": None,
            "catalog_item": None,
            "suggestions": []
        }
        
        suggestions = []
        
        # 1. البحث في الأسماء البديلة أولاً (تطابق تام)
        alias = await self.catalog_repo.find_alias(item_name)
        if alias:
            item = await self.catalog_repo.get_item_by_id(alias.catalog_item_id)
            if item:
                suggestions.append({
                    "id": str(item.id),
                    "item_code": item.item_code,
                    "name": item.name,
                    "unit": item.unit,
                    "price": item.price,
                    "category_name": item.category_name,
                    "alias_name": alias.alias_name,
                    "type": "alias_exact"
                })
        
        # 2. بحث في الكتالوج - إرجاع جميع النتائج المتطابقة (حتى 20)
        catalog_items = await self.catalog_repo.search_items(item_name, limit=20)
        for item in catalog_items:
            # تجنب التكرار
            if not any(s["id"] == str(item.id) for s in suggestions):
                suggestions.append({
                    "id": str(item.id),
                    "item_code": item.item_code,
                    "name": item.name,
                    "unit": item.unit,
                    "price": item.price,
                    "category_name": item.category_name,
                    "type": "catalog"
                })
        
        # 3. بحث في الأسماء البديلة (جزئي)
        aliases = await self.catalog_repo.search_aliases(item_name, limit=20)
        for alias in aliases:
            item = await self.catalog_repo.get_item_by_id(alias.catalog_item_id)
            if item:
                # تجنب التكرار
                if not any(s["id"] == str(item.id) for s in suggestions):
                    suggestions.append({
                        "id": str(item.id),
                        "item_code": item.item_code,
                        "name": item.name,
                        "unit": item.unit,
                        "price": item.price,
                        "category_name": item.category_name,
                        "alias_name": alias.alias_name,
                        "type": "alias"
                    })
        
        if suggestions:
            result["found"] = len(suggestions) > 0
            result["suggestions"] = suggestions
            # إذا كان هناك تطابق تام واحد فقط، أرجعه
            if len(suggestions) == 1:
                result["match_type"] = suggestions[0].get("type", "catalog")
                result["catalog_item"] = suggestions[0]
        
        return result
                        "item_code": item.item_code,
                        "name": item.name,
                        "alias_name": alias.alias_name,  # الاسم البديل
                        "unit": item.unit,
                        "price": item.price,
                        "category_name": item.category_name,
                        "type": "alias"
                    })
        
        result["suggestions"] = suggestions
        return result

"""
Catalog Repository
فصل طبقة الوصول لقاعدة البيانات للكتالوج
"""
from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import PriceCatalogItem as PriceCatalog, ItemAlias


class CatalogRepository:
    """Repository for Price Catalog and Item Aliases"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== Price Catalog ====================
    
    async def get_all_items(self, skip: int = 0, limit: int = 100) -> List[PriceCatalog]:
        """Get all catalog items with pagination"""
        result = await self.session.execute(
            select(PriceCatalog)
            .where(PriceCatalog.is_active == True)
            .order_by(PriceCatalog.item_code)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_item_by_id(self, item_id: str) -> Optional[PriceCatalog]:
        """Get catalog item by ID"""
        result = await self.session.execute(
            select(PriceCatalog).where(PriceCatalog.id == item_id)
        )
        return result.scalar_one_or_none()
    
    async def get_item_by_code(self, code: str) -> Optional[PriceCatalog]:
        """Get catalog item by code"""
        result = await self.session.execute(
            select(PriceCatalog).where(PriceCatalog.item_code == code)
        )
        return result.scalar_one_or_none()
    
    async def search_items(self, query: str, limit: int = 50) -> List[PriceCatalog]:
        """Search catalog items by name or code"""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(PriceCatalog)
            .where(
                PriceCatalog.is_active == True,
                or_(
                    PriceCatalog.name.ilike(search_pattern),
                    PriceCatalog.item_code.ilike(search_pattern)
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_items_by_category(self, category: str) -> List[PriceCatalog]:
        """Get catalog items by category name"""
        result = await self.session.execute(
            select(PriceCatalog)
            .where(
                PriceCatalog.is_active == True,
                PriceCatalog.category_name == category
            )
            .order_by(PriceCatalog.name)
        )
        return list(result.scalars().all())
    
    async def create_item(self, item: PriceCatalog) -> PriceCatalog:
        """Create catalog item"""
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item
    
    async def update_item(self, item_id: str, data: dict) -> Optional[PriceCatalog]:
        """Update catalog item"""
        item = await self.get_item_by_id(item_id)
        if item:
            for key, value in data.items():
                if hasattr(item, key) and value is not None:
                    setattr(item, key, value)
            await self.session.flush()
            await self.session.refresh(item)
        return item
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete catalog item (soft delete)"""
        item = await self.get_item_by_id(item_id)
        if item:
            item.is_active = False
            await self.session.flush()
            return True
        return False
    
    async def count_items(self) -> int:
        """Count total active catalog items"""
        result = await self.session.execute(
            select(func.count(PriceCatalog.id))
            .where(PriceCatalog.is_active == True)
        )
        return result.scalar_one()
    
    async def get_categories(self) -> List[str]:
        """Get distinct categories"""
        result = await self.session.execute(
            select(PriceCatalog.category_name)
            .distinct()
            .where(
                PriceCatalog.is_active == True,
                PriceCatalog.category_name.isnot(None)
            )
        )
        return [r[0] for r in result.all() if r[0]]
    
    async def get_next_code(self, category_name: Optional[str] = None) -> str:
        """Generate next item code based on category"""
        # Default category code mappings
        category_codes = {
            # Arabic categories
            "كهربائيات": "ELEC",
            "كهربائي": "ELEC",
            "ميكانيكا": "MECH",
            "ميكانيكي": "MECH",
            "سباكة": "PLMB",
            "سباكه": "PLMB",
            "مدني": "CIVL",
            "مدنيات": "CIVL",
            "دهانات": "PANT",
            "دهان": "PANT",
            "نجارة": "WOOD",
            "خشب": "WOOD",
            "حديد": "IRON",
            "معدن": "METL",
            "معدني": "METL",
            "زجاج": "GLAS",
            "ألمنيوم": "ALUM",
            "الومنيوم": "ALUM",
            "أدوات": "TOOL",
            "ادوات": "TOOL",
            "مستهلكات": "CONS",
            "عام": "GENL",
            "أخرى": "OTHR",
            "اخرى": "OTHR",
            # English categories
            "electrical": "ELEC",
            "mechanical": "MECH",
            "plumbing": "PLMB",
            "civil": "CIVL",
            "paint": "PANT",
            "wood": "WOOD",
            "iron": "IRON",
            "metal": "METL",
            "glass": "GLAS",
            "aluminum": "ALUM",
            "tools": "TOOL",
            "consumables": "CONS",
            "general": "GENL",
            "other": "OTHR",
        }
        
        # Get category code
        if category_name:
            # Try to find matching code
            category_lower = category_name.lower().strip()
            code_prefix = category_codes.get(category_lower)
            
            if not code_prefix:
                # Check if any key contains the category name
                for key, value in category_codes.items():
                    if key in category_lower or category_lower in key:
                        code_prefix = value
                        break
            
            if not code_prefix:
                # Use first 4 chars of category name
                code_prefix = category_name[:4].upper()
        else:
            code_prefix = "GENL"
        
        # Count items with this prefix
        result = await self.session.execute(
            select(func.count(PriceCatalog.id))
            .where(PriceCatalog.item_code.like(f"{code_prefix}-%"))
        )
        count = result.scalar_one()
        
        return f"{code_prefix}-{count + 1:04d}"
    
    async def get_next_code_by_category(self, category_code: Optional[str] = None, category_name: Optional[str] = None) -> str:
        """Generate next item code based on category code (e.g., 1-0001, 2-0001)"""
        if category_code:
            # Use the provided category code directly
            code_prefix = category_code.strip()
            
            # Count items with this prefix pattern (code-)
            result = await self.session.execute(
                select(func.count(PriceCatalog.id))
                .where(PriceCatalog.item_code.like(f"{code_prefix}-%"))
            )
            count = result.scalar_one()
            
            return f"{code_prefix}-{count + 1:04d}"
        else:
            # Fall back to old behavior
            return await self.get_next_code(category_name)
    
    # ==================== Item Aliases ====================
    
    async def get_all_aliases(self) -> List[ItemAlias]:
        """Get all item aliases"""
        result = await self.session.execute(
            select(ItemAlias).order_by(ItemAlias.alias_name)
        )
        return list(result.scalars().all())
    
    async def get_alias_by_id(self, alias_id: str) -> Optional[ItemAlias]:
        """Get alias by ID"""
        result = await self.session.execute(
            select(ItemAlias).where(ItemAlias.id == alias_id)
        )
        return result.scalar_one_or_none()
    
    async def find_alias(self, alias_name: str) -> Optional[ItemAlias]:
        """Find alias by name (case-insensitive)"""
        result = await self.session.execute(
            select(ItemAlias).where(ItemAlias.alias_name.ilike(alias_name))
        )
        return result.scalar_one_or_none()
    
    async def create_alias(self, alias: ItemAlias) -> ItemAlias:
        """Create item alias"""
        self.session.add(alias)
        await self.session.flush()
        await self.session.refresh(alias)
        return alias
    
    async def delete_alias(self, alias_id: str) -> bool:
        """Delete item alias"""
        alias = await self.get_alias_by_id(alias_id)
        if alias:
            await self.session.delete(alias)
            await self.session.flush()
            return True
        return False

"""
Supplier Repository
فصل طبقة الوصول لقاعدة البيانات للموردين
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import Supplier
from .base import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    """Repository for Supplier entity"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[Supplier]:
        """Get supplier by ID"""
        result = await self.session.execute(
            select(Supplier).where(Supplier.id == str(id))
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Supplier]:
        """Get supplier by name"""
        result = await self.session.execute(
            select(Supplier).where(Supplier.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Supplier]:
        """Get all suppliers with pagination"""
        result = await self.session.execute(
            select(Supplier)
            .offset(skip)
            .limit(limit)
            .order_by(Supplier.name)
        )
        return list(result.scalars().all())
    
    async def get_active(self) -> List[Supplier]:
        """Get active suppliers (all suppliers are considered active since no is_active column)"""
        result = await self.session.execute(
            select(Supplier).order_by(Supplier.name)
        )
        return list(result.scalars().all())
    
    async def search(self, query: str) -> List[Supplier]:
        """Search suppliers by name"""
        result = await self.session.execute(
            select(Supplier)
            .where(Supplier.name.ilike(f"%{query}%"))
            .limit(20)
        )
        return list(result.scalars().all())
    
    async def create(self, supplier: Supplier) -> Supplier:
        """Create new supplier"""
        self.session.add(supplier)
        await self.session.flush()
        await self.session.refresh(supplier)
        return supplier
    
    async def update(self, id: UUID, data: dict) -> Optional[Supplier]:
        """Update supplier"""
        supplier = await self.get_by_id(id)
        if supplier:
            for key, value in data.items():
                if hasattr(supplier, key):
                    setattr(supplier, key, value)
            await self.session.flush()
            await self.session.refresh(supplier)
        return supplier
    
    async def delete(self, id: UUID) -> bool:
        """Delete supplier (soft delete)"""
        supplier = await self.get_by_id(id)
        if supplier:
            supplier.is_active = False
            await self.session.flush()
            return True
        return False
    
    async def count(self) -> int:
        """Count total suppliers"""
        result = await self.session.execute(
            select(func.count(Supplier.id))
        )
        return result.scalar_one()

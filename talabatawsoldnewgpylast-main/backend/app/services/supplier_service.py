"""
Supplier Service
فصل منطق العمل للموردين
"""
from typing import Optional, List
from uuid import UUID

from database import Supplier
from app.repositories.supplier_repository import SupplierRepository
from .base import BaseService


class SupplierService(BaseService[Supplier]):
    """Service for supplier operations"""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repo = supplier_repository
    
    async def get_supplier(self, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID"""
        return await self.supplier_repo.get_by_id(supplier_id)
    
    async def get_all_suppliers(self, skip: int = 0, limit: int = 100) -> List[Supplier]:
        """Get all suppliers"""
        return await self.supplier_repo.get_all(skip, limit)
    
    async def get_active_suppliers(self) -> List[Supplier]:
        """Get active suppliers only"""
        return await self.supplier_repo.get_active()
    
    async def search_suppliers(self, query: str) -> List[Supplier]:
        """Search suppliers by name"""
        return await self.supplier_repo.search(query)
    
    async def create_supplier(
        self,
        name: str,
        contact_person: str = "",
        phone: str = "",
        email: str = "",
        address: str = ""
    ) -> Supplier:
        """Create new supplier"""
        supplier = Supplier(
            name=name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address
        )
        return await self.supplier_repo.create(supplier)
    
    async def update_supplier(
        self, 
        supplier_id: UUID, 
        data: dict
    ) -> Optional[Supplier]:
        """Update supplier"""
        return await self.supplier_repo.update(supplier_id, data)
    
    async def delete_supplier(self, supplier_id: UUID) -> bool:
        """Delete supplier (soft delete)"""
        return await self.supplier_repo.delete(supplier_id)
    
    async def get_suppliers_summary(self) -> dict:
        """Get suppliers summary"""
        all_suppliers = await self.supplier_repo.get_all()
        
        return {
            "total_suppliers": len(all_suppliers),
            "active_suppliers": len(all_suppliers),  # All suppliers are active by default
            "inactive_suppliers": 0
        }
    
    async def count_suppliers(self) -> int:
        """Count total suppliers"""
        return await self.supplier_repo.count()

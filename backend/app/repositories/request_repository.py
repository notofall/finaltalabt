"""
Material Request Repository
فصل طبقة الوصول لقاعدة البيانات لطلبات المواد
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import MaterialRequest
from .base import BaseRepository


class RequestRepository(BaseRepository[MaterialRequest]):
    """Repository for MaterialRequest entity"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[MaterialRequest]:
        """Get request by ID"""
        result = await self.session.execute(
            select(MaterialRequest).where(MaterialRequest.id == str(id))
        )
        return result.scalar_one_or_none()
    
    async def get_by_request_number(self, number: str) -> Optional[MaterialRequest]:
        """Get request by number"""
        result = await self.session.execute(
            select(MaterialRequest).where(MaterialRequest.request_number == number)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[MaterialRequest]:
        """Get all requests with pagination"""
        result = await self.session.execute(
            select(MaterialRequest)
            .offset(skip)
            .limit(limit)
            .order_by(MaterialRequest.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_status(self, status: str) -> List[MaterialRequest]:
        """Get requests by status"""
        result = await self.session.execute(
            select(MaterialRequest)
            .where(MaterialRequest.status == status)
            .order_by(MaterialRequest.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_project(self, project_id: UUID) -> List[MaterialRequest]:
        """Get requests by project"""
        result = await self.session.execute(
            select(MaterialRequest)
            .where(MaterialRequest.project_id == str(project_id))
            .order_by(MaterialRequest.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_supervisor(self, supervisor_id: UUID) -> List[MaterialRequest]:
        """Get requests by supervisor"""
        result = await self.session.execute(
            select(MaterialRequest)
            .where(MaterialRequest.created_by == str(supervisor_id))
            .order_by(MaterialRequest.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_pending_engineer(self) -> List[MaterialRequest]:
        """Get requests pending engineer approval"""
        result = await self.session.execute(
            select(MaterialRequest)
            .where(MaterialRequest.status == "pending_engineer")
            .order_by(MaterialRequest.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def create(self, request: MaterialRequest) -> MaterialRequest:
        """Create new request"""
        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)
        return request
    
    async def update(self, id: UUID, data: dict) -> Optional[MaterialRequest]:
        """Update request"""
        request = await self.get_by_id(id)
        if request:
            for key, value in data.items():
                if hasattr(request, key):
                    setattr(request, key, value)
            await self.session.flush()
            await self.session.refresh(request)
        return request
    
    async def delete(self, id: UUID) -> bool:
        """Delete request"""
        request = await self.get_by_id(id)
        if request:
            await self.session.delete(request)
            await self.session.flush()
            return True
        return False
    
    async def count(self) -> int:
        """Count total requests"""
        result = await self.session.execute(
            select(func.count(MaterialRequest.id))
        )
        return result.scalar_one()
    
    async def count_by_status(self, status: str) -> int:
        """Count requests by status"""
        result = await self.session.execute(
            select(func.count(MaterialRequest.id))
            .where(MaterialRequest.status == status)
        )
        return result.scalar_one()
    
    async def get_request_items(self, request_id: str) -> List[dict]:
        """Get items for a specific request"""
        from database import MaterialRequestItem
        
        result = await self.session.execute(
            select(MaterialRequestItem)
            .where(MaterialRequestItem.request_id == request_id)
            .order_by(MaterialRequestItem.item_index)
        )
        items = result.scalars().all()
        
        return [
            {
                "name": item.name,
                "quantity": item.quantity or 0,
                "unit": item.unit or "قطعة",
                "estimated_price": item.estimated_price
            }
            for item in items
        ]
    
    async def get_requests_items_batch(self, request_ids: List[str]) -> dict:
        """Get items for multiple requests in one query"""
        from database import MaterialRequestItem
        
        if not request_ids:
            return {}
        
        result = await self.session.execute(
            select(MaterialRequestItem)
            .where(MaterialRequestItem.request_id.in_(request_ids))
            .order_by(MaterialRequestItem.request_id, MaterialRequestItem.item_index)
        )
        all_items = result.scalars().all()
        
        # Group items by request_id
        items_map = {}
        for item in all_items:
            if item.request_id not in items_map:
                items_map[item.request_id] = []
            items_map[item.request_id].append({
                "name": item.name,
                "quantity": item.quantity or 0,
                "unit": item.unit or "قطعة",
                "estimated_price": item.estimated_price
            })
        
        return items_map
    
    async def get_next_seq_for_supervisor(self, supervisor_id: str, prefix: Optional[str] = None) -> int:
        """
        Get next sequence number for a supervisor based on their prefix.
        Uses database-level locking to prevent race conditions.
        For SQLite: Uses IMMEDIATE transaction mode
        For PostgreSQL: Uses FOR UPDATE row locking
        """
        from database.connection import get_database_url
        
        database_url = get_database_url()
        is_sqlite = 'sqlite' in database_url
        
        if prefix:
            # Get max sequence for this prefix (prefix-based numbering)
            query = select(func.max(MaterialRequest.request_seq)).where(
                MaterialRequest.request_number.like(f"{prefix}-%")
            )
        else:
            # Fallback to supervisor_id based numbering
            query = select(func.max(MaterialRequest.request_seq)).where(
                MaterialRequest.supervisor_id == supervisor_id
            )
        
        # Add row locking for PostgreSQL only (SQLite doesn't support FOR UPDATE)
        if not is_sqlite:
            query = query.with_for_update()
        
        result = await self.session.execute(query)
        current_max = result.scalar_one_or_none() or 0
        return current_max + 1
    
    async def add_items(self, request_id: str, items: List[dict]) -> List:
        """Add items to a request"""
        from database import MaterialRequestItem
        import uuid
        
        created_items = []
        for idx, item in enumerate(items):
            item_obj = MaterialRequestItem(
                id=str(uuid.uuid4()),
                request_id=request_id,
                name=item.get("name", ""),
                quantity=item.get("quantity", 1),
                unit=item.get("unit", "قطعة"),
                estimated_price=item.get("estimated_price"),
                item_index=idx
            )
            self.session.add(item_obj)
            created_items.append(item_obj)
        
        await self.session.flush()
        return created_items
    
    async def update_items(self, request_id: str, items: List[dict]) -> bool:
        """Update items for a request (delete old, add new)"""
        from database import MaterialRequestItem
        from sqlalchemy import delete
        import uuid
        
        # Delete existing items
        await self.session.execute(
            delete(MaterialRequestItem).where(MaterialRequestItem.request_id == request_id)
        )
        
        # Add new items
        for idx, item in enumerate(items):
            item_obj = MaterialRequestItem(
                id=str(uuid.uuid4()),
                request_id=request_id,
                name=item.get("name", ""),
                quantity=item.get("quantity", 1),
                unit=item.get("unit", "قطعة"),
                estimated_price=item.get("estimated_price"),
                item_index=idx
            )
            self.session.add(item_obj)
        
        await self.session.flush()
        return True

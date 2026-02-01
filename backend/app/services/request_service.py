"""
Material Request Service
فصل منطق العمل لطلبات المواد
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from database import MaterialRequest
from app.repositories.request_repository import RequestRepository
from .base import BaseService


class RequestService(BaseService[MaterialRequest]):
    """Service for material request operations"""
    
    def __init__(self, request_repository: RequestRepository):
        self.request_repo = request_repository
    
    async def get_request(self, request_id: UUID) -> Optional[MaterialRequest]:
        """Get request by ID"""
        return await self.request_repo.get_by_id(request_id)
    
    async def get_all_requests(self, skip: int = 0, limit: int = 100) -> List[MaterialRequest]:
        """Get all requests"""
        return await self.request_repo.get_all(skip, limit)
    
    async def get_requests_by_status(self, status: str) -> List[MaterialRequest]:
        """Get requests by status"""
        return await self.request_repo.get_by_status(status)
    
    async def get_requests_by_project(self, project_id: UUID) -> List[MaterialRequest]:
        """Get requests for a project"""
        return await self.request_repo.get_by_project(project_id)
    
    async def get_pending_engineer_requests(self) -> List[MaterialRequest]:
        """Get requests pending engineer approval"""
        return await self.request_repo.get_pending_engineer()
    
    async def approve_request(
        self,
        request_id: UUID,
        approved_by: str
    ) -> Optional[MaterialRequest]:
        """Approve request by engineer"""
        return await self.request_repo.update(request_id, {
            "status": "approved_by_engineer",
            "approved_by": approved_by,
            "approved_at": datetime.now(timezone.utc).replace(tzinfo=None)
        })
    
    async def reject_request(
        self,
        request_id: UUID,
        rejected_by: str,
        reason: str = ""
    ) -> Optional[MaterialRequest]:
        """Reject request"""
        return await self.request_repo.update(request_id, {
            "status": "rejected_by_engineer",
            "rejected_by": rejected_by,
            "rejection_reason": reason
        })
    
    async def get_request_stats(self) -> dict:
        """Get request statistics"""
        total = await self.request_repo.count()
        pending = await self.request_repo.count_by_status("pending_engineer")
        approved = await self.request_repo.count_by_status("approved_by_engineer")
        rejected = await self.request_repo.count_by_status("rejected_by_engineer")
        ordered = await self.request_repo.count_by_status("purchase_order_issued")
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "ordered": ordered
        }
    
    async def get_request_items(self, request_id: str) -> List[dict]:
        """Get items for a specific request via Repository"""
        return await self.request_repo.get_request_items(request_id)
    
    async def get_requests_items_batch(self, request_ids: List[str]) -> dict:
        """Get items for multiple requests via Repository"""
        return await self.request_repo.get_requests_items_batch(request_ids)
    
    async def count_requests(self, status_filter: Optional[str] = None) -> int:
        """Count total requests, optionally filtered by status"""
        if status_filter:
            return await self.request_repo.count_by_status(status_filter)
        return await self.request_repo.count()
    
    async def create_request(
        self,
        project_id: str,
        project_name: str,
        reason: str,
        supervisor_id: str,
        supervisor_name: str,
        engineer_id: str,
        engineer_name: str,
        expected_delivery_date: Optional[str] = None,
        supervisor_prefix: Optional[str] = None,
        project_code: Optional[str] = None,
        # حقول الدور والنموذج (اختياري)
        floor_id: Optional[str] = None,
        floor_name: Optional[str] = None,
        template_id: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> MaterialRequest:
        """
        Create a new material request with unique sequential numbering
        Format: PREFIX-PROJECT_CODE-SEQUENCE (e.g., a1-PRJ001-0001)
        """
        import uuid
        
        # Get next sequence number for this supervisor's prefix and project
        next_seq = await self.request_repo.get_next_seq_for_supervisor(
            supervisor_id, 
            supervisor_prefix,
            project_code
        )
        
        # Generate request number with format: PREFIX-PROJECT_CODE-SEQUENCE
        if supervisor_prefix and project_code:
            # Format: prefix-project_code-sequence (4 digits)
            request_number = f"{supervisor_prefix}-{project_code}-{next_seq:04d}"
        elif supervisor_prefix:
            # Format without project code
            request_number = f"{supervisor_prefix}-{next_seq:04d}"
        else:
            # Fallback format for supervisors without prefix
            request_number = f"REQ-{next_seq:05d}"
        
        request = MaterialRequest(
            id=str(uuid.uuid4()),
            request_number=request_number,
            request_seq=next_seq,
            project_id=project_id,
            project_name=project_name,
            reason=reason,
            supervisor_id=supervisor_id,
            supervisor_name=supervisor_name,
            engineer_id=engineer_id,
            engineer_name=engineer_name,
            status="pending_engineer",
            expected_delivery_date=expected_delivery_date,
            # حقول الدور والنموذج
            floor_id=floor_id,
            floor_name=floor_name,
            template_id=template_id,
            template_name=template_name,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        return await self.request_repo.create(request)
    
    async def add_request_items(
        self,
        request_id: str,
        items: List[dict]
    ) -> List:
        """Add items to a request"""
        return await self.request_repo.add_items(request_id, items)
    
    async def update_request(
        self,
        request_id: UUID,
        data: dict
    ) -> Optional[MaterialRequest]:
        """Update a request"""
        data["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
        return await self.request_repo.update(request_id, data)
    
    async def update_request_items(
        self,
        request_id: str,
        items: List[dict]
    ) -> bool:
        """Update request items (delete old, add new)"""
        return await self.request_repo.update_items(request_id, items)

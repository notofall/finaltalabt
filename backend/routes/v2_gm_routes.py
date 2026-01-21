"""
V2 GM Routes - General Manager dashboard with proper layering
Uses: GMService -> GMRepository

Architecture: Route -> Service -> Repository
- Routes: HTTP handling, auth, response formatting
- Services: Business logic
- Repositories: Data access
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_postgres_session
from app.repositories.gm_repository import GMRepository
from app.services.gm_service import GMService
from routes.v2_auth_routes import get_current_user, UserRole


router = APIRouter(
    prefix="/api/v2/gm",
    tags=["V2 General Manager"]
)


# ==================== Dependencies ====================

def get_gm_service(session: AsyncSession = Depends(get_postgres_session)) -> GMService:
    """Get GM service with repository"""
    repository = GMRepository(session)
    return GMService(repository)


def require_general_manager(user):
    """Check if user is general manager"""
    if user.role != UserRole.GENERAL_MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك بهذا الإجراء - صلاحيات المدير العام مطلوبة"
        )


# ==================== Pydantic Models ====================

class GMRejectData(BaseModel):
    reason: str


# ==================== Endpoints ====================

@router.get("/stats")
async def get_gm_stats(
    current_user = Depends(get_current_user),
    service: GMService = Depends(get_gm_service)
):
    """
    Get GM dashboard statistics
    Uses: GMService -> GMRepository
    """
    require_general_manager(current_user)
    return await service.get_stats()


@router.get("/pending-orders")
async def get_gm_pending_orders(
    current_user = Depends(get_current_user),
    service: GMService = Depends(get_gm_service)
):
    """
    Get orders pending GM approval
    Uses: GMService -> GMRepository
    """
    require_general_manager(current_user)
    return await service.get_pending_orders()


@router.get("/all-orders")
async def get_gm_all_orders(
    approval_type: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: GMService = Depends(get_gm_service)
):
    """
    Get all orders for GM dashboard - filterable by approval type
    approval_type: 'gm_approved' | 'manager_approved' | 'pending'
    Uses: GMService -> GMRepository
    """
    require_general_manager(current_user)
    return await service.get_all_orders(approval_type)


@router.post("/orders/{order_id}/approve")
async def approve_order(
    order_id: str,
    current_user = Depends(get_current_user),
    service: GMService = Depends(get_gm_service)
):
    """
    Approve a purchase order by GM
    Uses: GMService -> GMRepository
    """
    require_general_manager(current_user)
    
    try:
        return await service.approve_order(
            order_id=order_id,
            user_id=str(current_user.id),
            user_name=current_user.name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/orders/{order_id}/reject")
async def reject_order(
    order_id: str,
    reject_data: GMRejectData,
    current_user = Depends(get_current_user),
    service: GMService = Depends(get_gm_service)
):
    """
    Reject purchase order by General Manager
    Uses: GMService -> GMRepository
    """
    require_general_manager(current_user)
    
    try:
        return await service.reject_order(
            order_id=order_id,
            reason=reject_data.reason
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

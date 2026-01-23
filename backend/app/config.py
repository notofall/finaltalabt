"""
API Configuration & Constants
إعدادات وثوابت الـ API

This module centralizes configuration for:
- Pagination limits
- Timezone handling
- API versioning constants
"""
from datetime import datetime, timezone
from typing import TypeVar, Generic
from pydantic import BaseModel, Field
from fastapi import Query


# ==================== Pagination ====================

class PaginationConfig:
    """Pagination configuration with strict limits"""
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1


class PaginationParams:
    """
    Reusable pagination parameters for FastAPI routes.
    
    Usage:
        @router.get("/items")
        async def get_items(pagination: PaginationParams = Depends()):
            skip = pagination.skip
            limit = pagination.limit
    """
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="عدد العناصر للتخطي"),
        limit: int = Query(
            PaginationConfig.DEFAULT_PAGE_SIZE,
            ge=PaginationConfig.MIN_PAGE_SIZE,
            le=PaginationConfig.MAX_PAGE_SIZE,
            description=f"عدد العناصر (الحد الأقصى: {PaginationConfig.MAX_PAGE_SIZE})"
        )
    ):
        self.skip = skip
        self.limit = min(limit, PaginationConfig.MAX_PAGE_SIZE)  # Enforce max
    
    @property
    def page(self) -> int:
        """Calculate current page number (1-based)"""
        return (self.skip // self.limit) + 1 if self.limit > 0 else 1


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response wrapper.
    
    Usage:
        return PaginatedResponse(
            items=projects,
            total=100,
            skip=0,
            limit=20,
            has_more=True
        )
    """
    items: list
    total: int
    skip: int
    limit: int
    has_more: bool
    
    @classmethod
    def create(cls, items: list, total: int, skip: int, limit: int):
        """Factory method to create paginated response"""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )


# ==================== Timezone ====================

def utc_now() -> datetime:
    """
    Get current UTC datetime.
    
    Always use this instead of:
    - datetime.now() ❌
    - datetime.utcnow() ❌ (deprecated)
    
    Usage:
        from app.config import utc_now
        created_at = utc_now()
    
    Note: Returns timezone-naive datetime for PostgreSQL compatibility.
    PostgreSQL TIMESTAMP columns store without timezone info.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None)


def to_iso_string(dt: datetime | None) -> str | None:
    """
    Convert datetime to ISO format string.
    
    Usage:
        created_at_str = to_iso_string(project.created_at)
    """
    if dt is None:
        return None
    
    # Ensure UTC timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()


# ==================== API Versioning ====================

class APIVersion:
    """API version constants"""
    V1_PREFIX = "/api/pg"
    V2_PREFIX = "/api/v2"
    CURRENT = "v2"


# ==================== Response Helpers ====================

def success_response(message: str, data: dict = None) -> dict:
    """Standard success response"""
    response = {"success": True, "message": message}
    if data:
        response["data"] = data
    return response


def error_response(message: str, code: str = None) -> dict:
    """Standard error response"""
    response = {"success": False, "message": message}
    if code:
        response["code"] = code
    return response

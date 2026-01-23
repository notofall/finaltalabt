"""
Admin Repository - Repository layer for admin operations
"""
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from database import (
    User, Project, Supplier, BudgetCategory, MaterialRequest,
    PurchaseOrder, DeliveryRecord, AuditLog, SystemSetting
)
from datetime import datetime, timedelta, timezone
import uuid


class AdminRepository:
    """Repository for admin operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== USERS ====================
    
    async def get_all_users(self) -> List[User]:
        """Get all users"""
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def check_prefix_exists(self, prefix: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if supervisor prefix already exists"""
        query = select(User).where(
            User.supervisor_prefix == prefix,
            User.role == 'supervisor'
        )
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def create_user(self, data: Dict) -> User:
        """Create a new user"""
        user = User(
            id=str(uuid.uuid4()),
            **data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_user(self, user_id: str, updates: Dict) -> Optional[User]:
        """Update a user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in updates.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        user.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.commit()
        return True
    
    # ==================== SYSTEM STATS ====================
    
    async def get_system_stats(self) -> Dict:
        """Get system statistics"""
        # Users count
        users_result = await self.session.execute(
            select(func.count()).select_from(User)
        )
        total_users = users_result.scalar() or 0
        
        # Projects count
        projects_result = await self.session.execute(
            select(func.count()).select_from(Project)
        )
        total_projects = projects_result.scalar() or 0
        
        # Suppliers count
        suppliers_result = await self.session.execute(
            select(func.count()).select_from(Supplier)
        )
        total_suppliers = suppliers_result.scalar() or 0
        
        # Orders count
        orders_result = await self.session.execute(
            select(func.count()).select_from(PurchaseOrder)
        )
        total_orders = orders_result.scalar() or 0
        
        # Requests count
        requests_result = await self.session.execute(
            select(func.count()).select_from(MaterialRequest)
        )
        total_requests = requests_result.scalar() or 0
        
        # Active users (last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_result = await self.session.execute(
            select(func.count()).select_from(User)
            .where(User.updated_at >= week_ago)
        )
        active_users = active_result.scalar() or 0
        
        return {
            "total_users": total_users,
            "total_projects": total_projects,
            "total_suppliers": total_suppliers,
            "total_orders": total_orders,
            "total_requests": total_requests,
            "active_users_7d": active_users
        }
    
    # ==================== AUDIT LOGS ====================
    
    async def get_audit_logs(
        self,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 30,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """Get audit logs with filters"""
        query = select(AuditLog)
        
        # Date filter
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.where(AuditLog.created_at >= since)
        
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size)
        
        result = await self.session.execute(query)
        return result.scalars().all(), total
    
    # ==================== DATABASE STATS ====================
    
    async def get_database_stats(self) -> Dict:
        """Get database statistics"""
        tables = {
            "users": User,
            "projects": Project,
            "suppliers": Supplier,
            "budget_categories": BudgetCategory,
            "material_requests": MaterialRequest,
            "purchase_orders": PurchaseOrder,
            "delivery_records": DeliveryRecord,
            "audit_logs": AuditLog
        }
        
        stats = {}
        for name, model in tables.items():
            result = await self.session.execute(
                select(func.count()).select_from(model)
            )
            stats[name] = result.scalar() or 0
        
        return stats

"""
User Repository
فصل طبقة الوصول لقاعدة البيانات عن منطق العمل
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == str(id))
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        result = await self.session.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        result = await self.session.execute(
            select(User).where(User.role == role)
        )
        return list(result.scalars().all())
    
    async def get_active_users(self) -> List[User]:
        """Get all active users"""
        result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())
    
    async def create(self, user: User) -> User:
        """Create new user"""
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
    
    async def update(self, id: UUID, user_data: dict) -> Optional[User]:
        """Update user"""
        user = await self.get_by_id(id)
        if user:
            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.session.flush()
            await self.session.refresh(user)
        return user
    
    async def delete(self, id: UUID) -> bool:
        """Delete user (soft delete by setting is_active=False)"""
        user = await self.get_by_id(id)
        if user:
            user.is_active = False
            await self.session.flush()
            return True
        return False
    
    async def count(self) -> int:
        """Count total users"""
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(User.id))
        )
        return result.scalar_one()

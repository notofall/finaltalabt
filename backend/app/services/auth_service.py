"""
Auth Service
فصل منطق العمل عن الـ API routes
"""
from typing import Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID
import bcrypt
import jwt
import os

from database import User
from app.repositories.user_repository import UserRepository
from .base import BaseService


class AuthService(BaseService[User]):
    """Service for authentication and authorization"""
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS = 24
    
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    
    def create_access_token(self, user_id: str, role: str) -> str:
        """Create JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(hours=self.ACCESS_TOKEN_EXPIRE_HOURS)
        payload = {
            "sub": user_id,
            "role": role,
            "exp": expire
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def authenticate(self, email: str, password: str) -> Optional[tuple[User, str]]:
        """
        Authenticate user and return user with token
        Returns: (User, token) or None
        """
        user = await self.user_repo.get_by_email(email)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not self.verify_password(password, user.password):
            return None
        
        token = self.create_access_token(str(user.id), user.role)
        return (user, token)
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token"""
        payload = self.decode_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return await self.user_repo.get_by_id(UUID(user_id))
    
    async def register_user(
        self, 
        email: str, 
        password: str, 
        name: str, 
        role: str = "supervisor"
    ) -> Optional[User]:
        """Register new user"""
        # Check if user exists
        existing = await self.user_repo.get_by_email(email)
        if existing:
            return None
        
        # Create user
        user = User(
            email=email,
            password=self.hash_password(password),
            name=name,
            role=role,
            is_active=True
        )
        
        return await self.user_repo.create(user)
    
    async def change_password(
        self, 
        user_id: UUID, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """Change user password"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        if not self.verify_password(old_password, user.password):
            return False
        
        await self.user_repo.update(user_id, {
            "password": self.hash_password(new_password)
        })
        return True
    
    async def admin_reset_password(self, user_id: UUID, new_password: str) -> bool:
        """Admin reset user password (no old password required)"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        await self.user_repo.update(user_id, {
            "password": self.hash_password(new_password)
        })
        return True
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return await self.user_repo.get_by_id(user_id)
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination"""
        return await self.user_repo.get_all(skip, limit)
    
    async def get_users_by_role(self, role: str) -> list[User]:
        """Get users by role"""
        return await self.user_repo.get_by_role(role)
    
    async def count_users(self) -> int:
        """Count total users"""
        return await self.user_repo.count()
    
    async def count_users_by_role(self, role: str) -> int:
        """Count users by role"""
        users = await self.user_repo.get_by_role(role)
        return len(users)
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: str,
        role: str,
        assigned_projects: list = None,
        assigned_engineers: list = None
    ) -> Optional[User]:
        """Create user (admin function)"""
        import json
        existing = await self.user_repo.get_by_email(email)
        if existing:
            return None
        
        # Convert lists to JSON strings for SQLite compatibility
        projects_json = json.dumps(assigned_projects or [])
        engineers_json = json.dumps(assigned_engineers or [])
        
        user = User(
            email=email,
            password=self.hash_password(password),
            name=name,
            role=role,
            is_active=True,
            assigned_projects=projects_json,
            assigned_engineers=engineers_json
        )
        
        return await self.user_repo.create(user)
    
    async def update_user(self, user_id: UUID, data: dict) -> Optional[User]:
        """Update user data"""
        # Hash password if included
        if "password" in data and data["password"]:
            data["password"] = self.hash_password(data["password"])
        return await self.user_repo.update(user_id, data)
    
    async def toggle_user_active(self, user_id: UUID) -> Optional[User]:
        """Toggle user active status"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        return await self.user_repo.update(user_id, {"is_active": not user.is_active})
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user (soft delete)"""
        return await self.user_repo.delete(user_id)

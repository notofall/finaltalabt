"""
Admin Service - Business logic for admin operations
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
import bcrypt
from app.repositories.admin_repository import AdminRepository
from app.services.base import BaseService


class AdminService(BaseService):
    """Service layer for admin operations"""
    
    def __init__(self, repository: AdminRepository):
        self.repository = repository
    
    # ==================== USERS ====================
    
    async def get_all_users(self) -> List[Dict]:
        """Get all users"""
        users = await self.repository.get_all_users()
        return [self._format_user(user) for user in users]
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        user = await self.repository.get_user_by_id(user_id)
        if user:
            return self._format_user(user)
        return None
    
    async def create_user(
        self,
        name: str,
        email: str,
        password: str,
        role: str,
        supervisor_prefix: Optional[str] = None
    ) -> Dict:
        """Create a new user"""
        # Check if email exists
        existing = await self.repository.get_user_by_email(email)
        if existing:
            raise ValueError("البريد الإلكتروني مسجل بالفعل")
        
        # Validate prefix uniqueness for supervisors
        if supervisor_prefix and role == 'supervisor':
            prefix_exists = await self.repository.check_prefix_exists(supervisor_prefix)
            if prefix_exists:
                raise ValueError(f"رمز المشرف '{supervisor_prefix}' مستخدم بالفعل")
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        user = await self.repository.create_user({
            "name": name,
            "email": email,
            "password": password_hash,
            "role": role,
            "is_active": True,
            "supervisor_prefix": supervisor_prefix if role == 'supervisor' else None
        })
        
        return self._format_user(user)
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict
    ) -> Optional[Dict]:
        """Update a user"""
        # If password is being updated, hash it
        if 'password' in updates and updates['password']:
            updates['password'] = bcrypt.hashpw(
                updates['password'].encode(), 
                bcrypt.gensalt()
            ).decode()
        
        # Validate prefix uniqueness if being updated
        if 'supervisor_prefix' in updates and updates['supervisor_prefix']:
            user = await self.repository.get_user_by_id(user_id)
            if user and user.role == 'supervisor':
                prefix_exists = await self.repository.check_prefix_exists(
                    updates['supervisor_prefix'], 
                    exclude_user_id=user_id
                )
                if prefix_exists:
                    raise ValueError(f"رمز المشرف '{updates['supervisor_prefix']}' مستخدم بالفعل")
        
        user = await self.repository.update_user(user_id, updates)
        if user:
            return self._format_user(user)
        return None
    
    async def toggle_user_active(self, user_id: str) -> Optional[Dict]:
        """Toggle user active status"""
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            return None
        
        user = await self.repository.update_user(user_id, {
            "is_active": not user.is_active
        })
        
        return self._format_user(user)
    
    async def reset_user_password(
        self, 
        user_id: str, 
        new_password: str
    ) -> bool:
        """Reset user password"""
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        user = await self.repository.update_user(user_id, {"password": password_hash})
        return user is not None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        return await self.repository.delete_user(user_id)
    
    # ==================== SYSTEM ====================
    
    async def get_system_stats(self) -> Dict:
        """Get system statistics"""
        return await self.repository.get_system_stats()
    
    async def get_database_stats(self) -> Dict:
        """Get database statistics"""
        return await self.repository.get_database_stats()
    
    async def get_system_info(self) -> Dict:
        """Get system information"""
        import platform
        import sys
        
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "server_time": datetime.now(timezone.utc).isoformat()
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
    ) -> Dict:
        """Get audit logs with pagination"""
        logs, total = await self.repository.get_audit_logs(
            entity_type=entity_type,
            action=action,
            user_id=user_id,
            days=days,
            page=page,
            page_size=page_size
        )
        
        return {
            "items": [
                {
                    "id": log.id,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "action": log.action,
                    "user_id": log.user_id,
                    "user_name": log.user_name,
                    "details": log.details,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    # ==================== HELPERS ====================
    
    def _format_user(self, user) -> Dict:
        """Format user for response"""
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }

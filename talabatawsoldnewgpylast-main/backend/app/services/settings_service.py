"""
Settings Service - Business logic for system settings
"""
from typing import Dict, List, Optional
from app.repositories.settings_repository import SettingsRepository
from app.services.base import BaseService


class SettingsService(BaseService):
    """Service layer for settings operations"""
    
    def __init__(self, repository: SettingsRepository):
        self.repository = repository
    
    async def get_company_settings(self) -> Dict[str, str]:
        """Get company settings for PDF and branding"""
        return await self.repository.get_company_settings()
    
    async def update_company_settings(
        self,
        settings: Dict[str, str],
        user_id: str,
        user_name: str
    ) -> Dict[str, str]:
        """Update company settings"""
        return await self.repository.update_company_settings(
            settings=settings,
            user_id=user_id,
            user_name=user_name
        )
    
    async def get_setting(self, key: str) -> Optional[str]:
        """Get a single setting value"""
        setting = await self.repository.get_setting(key)
        return setting.value if setting else None
    
    async def set_setting(
        self,
        key: str,
        value: str,
        user_id: str,
        user_name: str,
        description: str = None
    ):
        """Set a single setting value"""
        await self.repository.upsert_setting(
            key=key,
            value=value,
            user_id=user_id,
            user_name=user_name,
            description=description
        )
    
    async def get_approval_limit(self) -> float:
        """Get the GM approval limit"""
        value = await self.get_setting("approval_limit")
        try:
            return float(value) if value else 20000.0
        except (ValueError, TypeError):
            return 20000.0
    
    async def get_all_settings(self) -> List[Dict]:
        """Get all settings as list of dicts"""
        settings = await self.repository.get_all_settings()
        return [
            {
                "key": s.key,
                "value": s.value,
                "description": s.description,
                "updated_by_name": s.updated_by_name,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in settings
        ]

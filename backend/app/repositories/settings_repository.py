"""
Settings Repository - Repository layer for system settings
"""
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import SystemSetting
from datetime import datetime
import uuid


class SettingsRepository:
    """Repository for system settings operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_setting(self, key: str) -> Optional[SystemSetting]:
        """Get a single setting by key"""
        result = await self.session.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        return result.scalar_one_or_none()
    
    async def get_settings_by_keys(self, keys: List[str]) -> Dict[str, str]:
        """Get multiple settings by their keys"""
        settings = {}
        for key in keys:
            setting = await self.get_setting(key)
            settings[key] = setting.value if setting else ""
        return settings
    
    async def get_all_settings(self) -> List[SystemSetting]:
        """Get all system settings"""
        result = await self.session.execute(select(SystemSetting))
        return result.scalars().all()
    
    async def upsert_setting(
        self, 
        key: str, 
        value: str, 
        user_id: str, 
        user_name: str,
        description: str = None
    ) -> SystemSetting:
        """Create or update a setting"""
        now = datetime.utcnow()
        setting = await self.get_setting(key)
        
        if setting:
            setting.value = str(value)
            setting.updated_by = user_id
            setting.updated_by_name = user_name
            setting.updated_at = now
        else:
            setting = SystemSetting(
                id=str(uuid.uuid4()),
                key=key,
                value=str(value),
                description=description or f"System setting: {key}",
                updated_by=user_id,
                updated_by_name=user_name,
                created_at=now
            )
            self.session.add(setting)
        
        await self.session.commit()
        return setting
    
    async def get_company_settings(self) -> Dict[str, str]:
        """Get all company-related settings"""
        company_keys = [
            "company_name", "company_logo", "company_address", "company_phone",
            "company_email", "report_header", "report_footer", "pdf_primary_color", "pdf_show_logo"
        ]
        return await self.get_settings_by_keys(company_keys)
    
    async def update_company_settings(
        self, 
        settings: Dict[str, str],
        user_id: str,
        user_name: str
    ) -> Dict[str, str]:
        """Update company settings"""
        for key, value in settings.items():
            if value is not None:
                await self.upsert_setting(
                    key=key,
                    value=str(value),
                    user_id=user_id,
                    user_name=user_name,
                    description=f"إعداد الشركة: {key}"
                )
        
        return await self.get_company_settings()

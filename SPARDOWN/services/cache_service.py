import json
from datetime import datetime, timedelta
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from SPARDOWN.repositories.repos import CacheRepository

class MetadataCacheService:
    def __init__(self, session: AsyncSession):
        self.repo = CacheRepository(session)

    async def get(self, key: str) -> Optional[Any]:
        entry = await self.repo.get_by_id(key)
        if not entry:
            return None
        
        if datetime.utcnow() > entry.expires_at:
            await self.repo.delete(key)
            return None
            
        return json.loads(entry.value)

    async def set(self, key: str, value: Any, ttl_hours: int = 24):
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        val_str = json.dumps(value)
        
        # Check if exists to update or create
        existing = await self.repo.get_by_id(key)
        if existing:
            await self.repo.update(key, value=val_str, expires_at=expires_at)
        else:
            await self.repo.create(key=key, value=val_str, expires_at=expires_at)

    async def invalidate(self, key: str):
        await self.repo.delete(key)

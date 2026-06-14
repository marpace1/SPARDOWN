from SPARDOWN.repositories.base import BaseRepository
from SPARDOWN.models.models import DownloadJob, Track, CacheEntry, ApiKey
from sqlalchemy.ext.asyncio import AsyncSession

class JobRepository(BaseRepository[DownloadJob, int]):
    def __init__(self, session: AsyncSession):
        super().__init__(DownloadJob, session)

class TrackRepository(BaseRepository[Track, int]):
    def __init__(self, session: AsyncSession):
        super().__init__(Track, session)

class CacheRepository(BaseRepository[CacheEntry, str]):
    def __init__(self, session: AsyncSession):
        super().__init__(CacheEntry, session)

class ApiKeyRepository(BaseRepository[ApiKey, str]):
    def __init__(self, session: AsyncSession):
        super().__init__(ApiKey, session)

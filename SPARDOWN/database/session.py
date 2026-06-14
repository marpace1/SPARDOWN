from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from SPARDOWN.config.settings import settings
from SPARDOWN.models.models import Base

class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self.session_factory = async_sessionmaker(
            bind=self.engine, 
            expire_on_commit=False, 
            class_=AsyncSession
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        return self.session_factory()

db = DatabaseManager()

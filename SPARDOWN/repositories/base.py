from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

T = TypeVar("T")
PK = TypeVar("PK")

class BaseRepository(Generic[T, PK]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: PK) -> Optional[T]:
        # Use a more generic filter to handle different PK column names
        # We assume the primary key is the first column defined in the model's __table__
        pk_column = self.model.__table__.primary_key.columns.values()[0]
        result = await self.session.execute(
            select(self.model).filter(pk_column == id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: PK, **kwargs) -> Optional[T]:
        pk_column = self.model.__table__.primary_key.columns.values()[0]
        await self.session.execute(
            update(self.model).where(pk_column == id).values(**kwargs)
        )
        await self.session.commit()
        return await self.get_by_id(id)

    async def delete(self, id: PK) -> bool:
        pk_column = self.model.__table__.primary_key.columns.values()[0]
        result = await self.session.execute(
            delete(self.model).where(pk_column == id)
        )
        await self.session.commit()
        return result.rowcount > 0

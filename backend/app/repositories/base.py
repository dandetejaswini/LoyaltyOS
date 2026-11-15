from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from backend.app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Abstract base repository isolating SQL queries from the business service layer.
    Enforces the Data Tier boundary in the three-tier architecture.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        return await session.get(self.model, id)

    async def list_all(self, session: AsyncSession, limit: int = 100, offset: int = 0) -> List[ModelType]:
        result = await session.execute(select(self.model).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, obj: ModelType) -> ModelType:
        session.add(obj)
        await session.flush()
        return obj

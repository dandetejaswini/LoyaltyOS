from typing import Generic, TypeVar, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.base import BaseRepository, ModelType


class BaseService(Generic[ModelType]):
    """
    Abstract base service providing domain logic execution.
    Enforces the Application Tier boundary, never exposing database queries directly to presentation.
    """

    def __init__(self, repository: BaseRepository[ModelType]):
        self.repository = repository

    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        return await self.repository.get_by_id(session, id)

    async def list(self, session: AsyncSession, limit: int = 100, offset: int = 0) -> List[ModelType]:
        return await self.repository.list_all(session, limit=limit, offset=offset)

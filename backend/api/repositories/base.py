from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import TypeVar, Generic, Type, Optional, List
from ..db import Base
from ..models.entity import User, ApiKey

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id) -> Optional[T]:
        result = await self.session.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def create(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id) -> bool:
        await self.session.execute(delete(self.model).where(self.model.id == id))
        await self.session.commit()
        return True

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).filter(User.email == email))
        return result.scalars().first()

class ApiKeyRepository(BaseRepository[ApiKey]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ApiKey)

    async def get_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        result = await self.session.execute(select(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True))
        return result.scalars().first()

    async def get_by_user_id(self, user_id) -> List[ApiKey]:
        result = await self.session.execute(select(ApiKey).filter(ApiKey.user_id == user_id))
        return result.scalars().all()

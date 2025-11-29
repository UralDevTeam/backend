from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.user import User
from src.infrastructure.db.models.user import UserOrm


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_email(self, email: str) -> User | None:
        user_orm: UserOrm | None = (await self._session.execute(select(UserOrm).where(UserOrm.email == email))).scalar()
        if not user_orm:
            return None
        return User.model_validate(user_orm)

    async def create(self, user: User) -> User:
        insert_user_stmt = insert(UserOrm).values(**user.model_dump()).returning(UserOrm)
        user_orm: UserOrm = (await self._session.execute(insert_user_stmt)).scalar_one()
        return User.model_validate(user_orm)

    async def update_by_email(self, email: str, data: dict) -> User | None:
        if not data:
            return await self.find_by_email(email)

        stmt = (
            update(UserOrm)
            .where(UserOrm.email == email)
            .values(**data)
            .returning(UserOrm)
        )

        result = await self._session.execute(stmt)
        user_orm: UserOrm | None = result.scalar_one_or_none()

        if not user_orm:
            return None

        await self._session.flush()
        return User.model_validate(user_orm)

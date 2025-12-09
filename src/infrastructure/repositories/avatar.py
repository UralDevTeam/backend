from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Avatar
from src.infrastructure.db.models import AvatarOrm


class AvatarRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert(self, avatar: Avatar) -> Avatar:
        stmt = (
            insert(AvatarOrm)
            .values(
                employee_id=avatar.employee_id,
                mime_type=avatar.mime_type,
                image_small=avatar.image_small,
                image_large=avatar.image_large,
            )
            .on_conflict_do_update(
                index_elements=[AvatarOrm.employee_id],
                set_={
                    "mime_type": avatar.mime_type,
                    "image_small": avatar.image_small,
                    "image_large": avatar.image_large,
                },
            )
            .returning(AvatarOrm)
        )

        result = await self._session.execute(stmt)
        avatar_orm: AvatarOrm = result.scalar_one()
        await self._session.flush()
        return Avatar.model_validate(avatar_orm)

    async def get_by_employee_id(self, employee_id: UUID) -> Avatar | None:
        stmt = select(AvatarOrm).where(AvatarOrm.employee_id == employee_id)
        result = await self._session.execute(stmt)
        avatar_orm: AvatarOrm | None = result.scalar_one_or_none()
        if not avatar_orm:
            return None
        return Avatar.model_validate(avatar_orm)

    async def delete_by_employee_id(self, employee_id: UUID) -> bool:
        stmt = delete(AvatarOrm).where(AvatarOrm.employee_id == employee_id).returning(AvatarOrm.employee_id)
        result = await self._session.execute(stmt)
        employee_id = result.scalar_one_or_none()
        return employee_id is not None

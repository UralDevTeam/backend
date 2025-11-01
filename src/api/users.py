from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ad_users import ADUser
from sqlalchemy.orm import Session
from typing import List, Optional
from src.services.ad_users import Store, get_store
from src.infrastructure.repositories.employee import EmployeeRepository
from src.infrastructure.db.base import async_session_factory
from pydantic import BaseModel

router = APIRouter()

class UserLinkDTO(BaseModel):
    id: str
    fullName: str  # Траблона Е.К.
    shortName: str  # Иванова Анастасия Сергеевна


class UserDTO(BaseModel):
    id: str
    fio: str
    birthday: str
    team: List[str]
    boss: Optional[UserLinkDTO]
    role: str
    grade: str
    experience: int  # days
    status: str
    city: str
    contact: str
    aboutMe: str

async def get_db() -> AsyncSession:
    """Dependency для получения сессии БД"""
    async with async_session_factory() as session:
        yield session


@router.get("/users/{user_id}", response_model=UserDTO)
async def get_user_by_id(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Получить пользователя по ID из PostgreSQL"""
    repo = EmployeeRepository(db)
    employee = await repo.get_by_id(user_id)

    if not employee:
        raise HTTPException(status_code=404, detail=f"User with id '{user_id}' not found")

    # Маппинг Employee model -> UserDTO
    # Формируем boss если есть
    boss_dto = None
    if employee.boss_id:
        boss = await repo.get_by_id(employee.boss_id)
        if boss:
            boss_dto = UserLinkDTO(
                id=str(boss.id),
                fullName=boss.full_name or "",
                shortName=boss.short_name or ""
            )

    return UserDTO(
        id=str(employee.id),
        fio=employee.fio or "",
        birthday=employee.birthday.isoformat() if employee.birthday else "",
        team=employee.team or [],
        boss=boss_dto,
        role=employee.role or "",
        grade=employee.grade or "",
        experience=employee.experience or 0,
        status=employee.status or "active",
        city=employee.city or "",
        contact=employee.contact or "",
        aboutMe=employee.about_me or ""
    )


@router.get("/users/all", response_model=List[ADUser])
def users(store: Store = Depends(get_store)):
    total, items = store.search(q=None, enabled=True, department=None, title=None, offset=0, limit=10 ** 9,
                                sort='name')
    return items


@router.post("/reload")
def reload_data(store: Store = Depends(get_store)):
    store.load()
    return {"status": "ok", "count": len(store.items)}

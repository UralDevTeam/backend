from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_user_service
from src.api.auth import get_current_user
from src.application.dto import UserDTO, UserUpdatePayload
from src.domain.models.user import User
from src.application.services import UserService

router = APIRouter()

@router.get("/users", response_model=list[UserDTO])
async def get_users(
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.list_users()


@router.get("/users/{user_id}", response_model=UserDTO)
async def get_user_by_id(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """Получить пользователя по ID из PostgreSQL"""
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail=f"User with id '{user_id}' not found")

    return user


@router.get("/me", response_model=UserDTO)
async def get_me(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.get_me(current_user)

    if not user:
        raise HTTPException(status_code=404, detail="Employee not found for current user")

    return user


@router.put("/me", response_model=UserDTO)
async def update_me(
    payload: UserUpdatePayload,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.update_me(current_user, payload)

    if not user:
        raise HTTPException(status_code=404, detail="Employee not found for current user")

    return user

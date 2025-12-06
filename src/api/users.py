from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from src.api.dependencies import (
    get_avatar_service,
    get_employee_repository,
    get_user_service,
)
from src.api.auth import get_current_user, hash_password
from src.application.dto import AdminUserUpdatePayload, UserDTO, UserUpdatePayload, UserCreatePayload
from src.application.services import AvatarService, UserService
from src.domain.models.user import User
from src.infrastructure.repositories import EmployeeRepository

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


@router.put("/users/{user_id}", response_model=UserDTO)
async def update_user(
        user_id: UUID,
        payload: AdminUserUpdatePayload,
        current_user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    try:
        user = await user_service.update_user(user_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    if not user:
        raise HTTPException(status_code=404, detail=f"User with id '{user_id}' not found")

    return user


@router.post("/user", response_model=UserDTO, status_code=status.HTTP_201_CREATED)
async def create_user(
        payload: UserCreatePayload,
        current_user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    try:
        created_user = await user_service.create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
            employee_payload=payload.employee.model_dump(),
            creator=current_user,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    return created_user


@router.post("/users/{user_id}/avatar", status_code=status.HTTP_201_CREATED)
async def upload_avatar(
        user_id: UUID,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        avatar_service: AvatarService = Depends(get_avatar_service),
        employee_repository: EmployeeRepository = Depends(get_employee_repository),
):
    target_employee = await employee_repository.get_by_id(user_id)
    if not target_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id '{user_id}' not found")

    if current_user.role != "admin":
        current_employee = await employee_repository.get_by_email(current_user.email)
        if not current_employee or current_employee.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot upload avatar for this user")

    content = await file.read()
    try:
        await avatar_service.save_avatar(user_id, content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"detail": "Avatar uploaded"}


@router.get("/users/{user_id}/avatar/large")
async def get_large_avatar(
        user_id: UUID,
        avatar_service: AvatarService = Depends(get_avatar_service),
):
    avatar = await avatar_service.get_avatar(user_id)
    if not avatar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Avatar for user '{user_id}' not found")

    return Response(content=avatar.image_large, media_type=avatar.mime_type)


@router.get("/users/{user_id}/avatar/small")
async def get_small_avatar(
        user_id: UUID,
        avatar_service: AvatarService = Depends(get_avatar_service),
):
    avatar = await avatar_service.get_avatar(user_id)
    if not avatar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Avatar for user '{user_id}' not found")

    return Response(content=avatar.image_small, media_type=avatar.mime_type)

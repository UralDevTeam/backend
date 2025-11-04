from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from uuid6 import uuid7

from src.api.dependencies import get_user_repository
from src.domain.models.user import User
from src.infrastructure.repositories import UserRepository
from passlib.context import CryptContext


router = APIRouter()
security = HTTPBasic()
pwd = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

Role = Literal["admin", "user"]

def hash_password(p: str) -> str:
    return pwd.hash(p)

def verify_password(plain: str, hashed: str) -> bool:
    """Проверка совпадения пароля"""
    return pwd.verify(plain, hashed)

class UserIn(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: UUID
    email: str
    role: Role

@router.post("/auth/register", response_model=UserOut, status_code=201)
async def register(payload: UserIn, user_repository: UserRepository = Depends(get_user_repository)) -> UserOut:
    if await user_repository.find_by_email(payload.email):
        raise HTTPException(400, "User already registered")
    user = User(id=uuid7(), email=payload.email, password_hash=hash_password(payload.password), role="user")
    await user_repository.create(user)
    return UserOut(id=user.id, email=user.email, role=user.role)

@router.post("/auth/login", response_model=UserOut, status_code=200)
async def login(payload: UserIn, user_repository: UserRepository = Depends(get_user_repository)) -> UserOut:
    user = await user_repository.find_by_email(payload.email)
    if not user:
        raise HTTPException(400, "User does not exist")
    return UserOut(id=user.id, email=user.email, role=user.role)

async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    """
    1. Парсим логин/пароль из заголовка Authorization: Basic ...
    2. Ищем пользователя по email
    3. Сравниваем пароль через passlib
    4. Возвращаем объект User или 401
    """
    email = credentials.username
    user = await user_repository.find_by_email(email)

    if not user or not verify_password(credentials.password, user.password_hash):
        # возвращаем стандартный ответ Basic 401
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": 'Basic realm="Login"'},
        )

    return user





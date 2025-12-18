from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from uuid6 import uuid7

from src.api.dependencies import get_employee_repository, get_user_repository
from src.domain.models.user import User
from src.infrastructure.repositories import EmployeeRepository, UserRepository

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=True)

pwd = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

Role = Literal["admin", "user"]

SECRET_KEY = "super-secret-key-change-me"  # брать из env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 8 * 60


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


class Token(BaseModel):
    access_token: str = Field(
        serialization_alias="accessToken",
        validation_alias=AliasChoices("accessToken", "access_token"),
    )
    token_type: str = Field(
        serialization_alias="tokenType",
        validation_alias=AliasChoices("tokenType", "token_type"),
    )

    model_config = ConfigDict(populate_by_name=True)


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
    iat: int | None = None


class PasswordChangeIn(BaseModel):
    old_password: str = Field(
        validation_alias=AliasChoices("oldPassword", "old_password"),
        serialization_alias="oldPassword",
    )
    new_password: str = Field(
        validation_alias=AliasChoices("newPassword", "new_password"),
        serialization_alias="newPassword",
    )

    model_config = ConfigDict(populate_by_name=True)


def create_access_token(subject: str, issued_at: int, expires_delta: int) -> str:
    """
    subject — кого токен представляет. Сейчас кладём туда user_id (UUID в виде строки).
    """
    expire_at = issued_at + expires_delta

    to_encode = {
        "sub": subject,
        "exp": expire_at,
        "iat": issued_at,
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    """
    1. Достаём токен из заголовка Authorization: Bearer <token>
    2. Декодируем JWT
    3. Берём sub (user_id) из payload
    4. Ищем пользователя
    5. Проверяем, что токен не старее смены пароля
    """
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except JWTError:
        raise credentials_exception

    if token_data.sub is None:
        raise credentials_exception

    user_id = UUID(token_data.sub)
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise credentials_exception

    if getattr(user, "password_changed_at", None) and token_data.iat is not None:
        token_iat_dt = datetime.fromtimestamp(token_data.iat, tz=timezone.utc)
        if token_iat_dt < user.password_changed_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked (password changed)",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user


@router.post("/auth/register", response_model=UserOut, status_code=201)
async def register(
    payload: UserIn,
    user_repository: UserRepository = Depends(get_user_repository),
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
) -> UserOut:
    if await user_repository.find_by_email(payload.email):
        raise HTTPException(400, "User already registered")

    employee = await employee_repository.get_by_email(payload.email)
    if not employee:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")

    user = User(
        id=uuid7(),
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    await user_repository.create(user)
    role: Role = "admin" if employee.is_admin else "user"
    return UserOut(id=user.id, email=user.email, role=role)


@router.post("/auth/login", response_model=Token, status_code=200)
async def login(
    payload: UserIn,
    user_repository: UserRepository = Depends(get_user_repository),
) -> Token:
    """
    Логин возвращает JWT, а не данные пользователя.
    """
    user = await user_repository.find_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        subject=str(user.id),
        issued_at=int(datetime.now(timezone.utc).timestamp()),
        expires_delta=60*60*8,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/auth/change-password", response_model=Token, status_code=200)
async def change_password(
    payload: PasswordChangeIn,
    current_user: User = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
) -> Token:
    """
    Смена пароля у залогиненного пользователя.

    Шаги:
    1. Проверяем старый пароль.
    2. Обновляем password_hash и password_changed_at (для ревокации старых токенов).
    3. Возвращаем новый access-токен.
    """
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    password_hash = hash_password(payload.new_password)
    password_changed_at_ts = int(datetime.now(timezone.utc).timestamp())

    data = {
        "password_hash": password_hash,
        "password_changed_at_ts": password_changed_at_ts,
    }
    user_id = UUID(str(current_user.id))
    await user_repository.update_by_id(user_id, data)

    new_token = create_access_token(
        subject=str(user_id),
        issued_at=password_changed_at_ts,
        expires_delta=60*60*8,
    )

    return Token(access_token=new_token, token_type="bearer")

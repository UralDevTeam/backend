import pytest
from fastapi import HTTPException

from src.api.auth import UserIn, register


@pytest.mark.asyncio
async def test_register_allows_known_employee(sample_employee, user_repo, employee_repo, session):
    payload = UserIn(email=sample_employee.email, password="password123")

    user_out = await register(payload, user_repo, employee_repo)
    await session.commit()

    created_user = await user_repo.find_by_email(sample_employee.email)

    assert created_user is not None
    assert created_user.id == user_out.id
    assert user_out.email == sample_employee.email


@pytest.mark.asyncio
async def test_register_rejects_unknown_email(user_repo, employee_repo):
    payload = UserIn(email="unknown@example.com", password="password123")

    with pytest.raises(HTTPException) as exc_info:
        await register(payload, user_repo, employee_repo)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Employee not found"
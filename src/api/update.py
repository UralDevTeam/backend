from fastapi import APIRouter, Depends, HTTPException, status

from src.api.auth import get_current_user
from src.api.dependencies import get_ad_import_service, get_employee_repository
from src.application.dto import AdImportResultDTO
from src.application.services import AdImportService
from src.domain.models.user import User
from src.infrastructure.repositories import EmployeeRepository

router = APIRouter()


@router.post("/update", response_model=AdImportResultDTO)
async def update_from_active_directory(
        current_user: User = Depends(get_current_user),
        ad_import_service: AdImportService = Depends(get_ad_import_service),
        employee_repository: EmployeeRepository = Depends(get_employee_repository),
) -> AdImportResultDTO:
    current_employee = await employee_repository.get_by_email(current_user.email)
    if not current_employee or not current_employee.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    try:
        result = await ad_import_service.update_from_ad()
        return AdImportResultDTO(**result)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

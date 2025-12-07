from fastapi import APIRouter, Depends, HTTPException, status

from src.api.auth import get_current_user
from src.api.dependencies import get_ad_import_service
from src.application.dto import AdImportResultDTO
from src.application.services import AdImportService
from src.domain.models.user import User

router = APIRouter()


@router.post("/update", response_model=AdImportResultDTO)
async def update_from_active_directory(
        current_user: User = Depends(get_current_user),
        ad_import_service: AdImportService = Depends(get_ad_import_service),
) -> AdImportResultDTO:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    try:
        result = await ad_import_service.update_from_ad()
        return AdImportResultDTO(**result)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

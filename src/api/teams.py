from fastapi import APIRouter, Depends

from src.api.dependencies import get_team_repository
from src.domain.models import Team
from src.infrastructure.repositories import TeamRepository

router = APIRouter()


@router.get("/teams", response_model=list[Team])
async def list_teams(team_repository: TeamRepository = Depends(get_team_repository)) -> list[Team]:
    """Возвращает список всех команд."""
    return await team_repository.get_all()
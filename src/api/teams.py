from fastapi import APIRouter, Depends

from src.api.dependencies import get_team_repository
from src.application.dto import TeamDTO
from src.infrastructure.repositories import TeamRepository

router = APIRouter()

@router.get("/teams", response_model=list[TeamDTO])
async def list_teams(team_repository: TeamRepository = Depends(get_team_repository)) -> list[TeamDTO]:
    """Возвращает список всех команд."""
    teams = await team_repository.get_all()
    return [TeamDTO.from_team(team) for team in teams]

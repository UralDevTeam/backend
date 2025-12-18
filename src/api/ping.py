from fastapi import APIRouter
from src.application.dto import PingResponse
from src.application.services import get_pong

router = APIRouter()


@router.get("/ping", response_model=PingResponse)
def ping() -> PingResponse:
    return PingResponse(ping="pong")

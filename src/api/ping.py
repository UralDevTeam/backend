from fastapi import APIRouter
from src.application.dto import PingResponse

router = APIRouter()


@router.get("/ping", response_model=PingResponse)
def ping() -> PingResponse:
    return PingResponse(ping="pong")

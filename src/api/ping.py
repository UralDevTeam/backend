from fastapi import APIRouter
from src.application.services import get_pong

router = APIRouter()

@router.get("/ping")
def ping():
    return get_pong()

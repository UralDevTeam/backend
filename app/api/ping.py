from fastapi import APIRouter
from app.services.ping_service import get_pong

router = APIRouter()

@router.get("/ping")
def ping():
    return get_pong()

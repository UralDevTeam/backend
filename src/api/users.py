from fastapi import APIRouter, Depends
from src.services.ad_users import ADUser
from typing import List
from src.services.ad_users import Store, get_store

router = APIRouter()


@router.get("/users/all", response_model=List[ADUser])
def users(store: Store = Depends(get_store)):
    total, items = store.search(q=None, enabled=True, department=None, title=None, offset=0, limit=10 ** 9,
                                sort='name')
    return items


@router.post("/reload")
def reload_data(store: Store = Depends(get_store)):
    store.load()
    return {"status": "ok", "count": len(store.items)}

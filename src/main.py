from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.ping import router as ping_router
from src.api.users import router as users_router
from src.api.auth import router as auth_router
from src.services.ad_users import Store

CSV_PATH = "src/res/test_users.csv"

@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.store = Store(CSV_PATH)
    application.state.store.load()
    yield

app = FastAPI(title="UDV Team Map API", lifespan=lifespan)
app.include_router(ping_router, prefix="/api", tags=["ping"])
app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(auth_router, prefix="/api", tags=["auth"])

origins = [
    "http://localhost:3000",   # ваш фронтенд dev URL
    # "https://your.production.frontend"  # production origin, если нужно
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # нельзя ставить ["*"] если allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

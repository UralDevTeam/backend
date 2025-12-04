from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.auth import router as auth_router
from src.api.ping import router as ping_router
from src.api.users import router as users_router
from src.api.teams import router as teams_router
from src.api.update import router as update_router

CSV_PATH = "src/res/test_users.csv"

app = FastAPI(title="UDV Team Map API")
app.include_router(ping_router, prefix="/api", tags=["ping"])
app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(teams_router, prefix="/api", tags=["teams"])
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(update_router, prefix="/api", tags=["ad"])

origins = [
    "http://localhost:3000",  # ваш фронтенд dev URL
    "https://udv-pi.vercel.app"  # production origin, если нужно
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

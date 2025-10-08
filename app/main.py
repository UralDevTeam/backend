from fastapi import FastAPI
from app.api.ping import router as ping_router

app = FastAPI(title="Ping API (modular)")

app.include_router(ping_router, prefix="/api", tags=["ping"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

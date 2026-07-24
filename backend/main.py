from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.games import router as game_router

app = FastAPI(title="Chess Platform API")

app.include_router(auth_router)
app.include_router(game_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Chess API is running"}


@app.get("/health")
def health_status() -> dict[str, str]:
    return {"status": "fine"}


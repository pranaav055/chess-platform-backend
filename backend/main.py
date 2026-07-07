from fastapi import FastAPI 
from app.routes.auth import router as auth_router
from app.routes.games import router as game_router

app = FastAPI(title = "Chess project")

app.include_router(auth_router)
app.include_router(game_router)

@app.get("/")
def root():
    return {"message": "Chess API is running"}

@app.get("/health")
def health_status():
    return {"status": "fine"}


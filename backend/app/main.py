from fastapi import FastAPI
from .api.routes import router
from .db.session import engine
from .models.base import Base

app = FastAPI(title="AI Knowledge Worker - Backend")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)  # quick start (Alembic later)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Backend OK - Phase 2 ready"}
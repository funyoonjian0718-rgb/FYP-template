from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.init_db import init_db
from app.routes.auth import router as auth_router
from app.routes.query import router as query_router
from app.routes.health import router as health_router
from app.routes.ui import router as ui_router


app = FastAPI(title="FYP RAG Dietary Advice", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()


app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.include_router(health_router)
app.include_router(ui_router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(query_router, prefix="/diet", tags=["diet"])


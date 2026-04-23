from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.config import ensure_directories, settings
from app.db.base import Base
from app.db.bootstrap import ensure_sqlite_schema_compatibility
from app.db.session import engine
from app.web.routes import router as web_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_directories()
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema_compatibility(engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount(
    "/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static"
)
app.include_router(web_router)
app.include_router(api_router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

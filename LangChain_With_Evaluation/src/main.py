from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.app.api.depedencies import get_evaluation_service
from src.app.api.routes.evaluations import router as evaluations_router
from src.app.api.routes.health import router as health_router
from src.app.core.config import get_settings, Settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_evaluation_service()
    yield

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,

    )

    app.include_router(health_router)
    app.include_router(evaluations_router, prefix="/api/v1" )

    return app
app = create_app()



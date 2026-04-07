from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.config.database import init_db
from src.config.logging_config import setup_logging
from src.infrastructure.security.rate_limiter import limiter
from src.presentation.api.v1 import events, health
from src.presentation.middleware.audit import AuditMiddleware
from src.presentation.middleware.error_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="HTQA Event Monitoring Service",
        description="Microservice for infrastructure monitoring event ingestion",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(AuditMiddleware)

    register_exception_handlers(app)

    app.include_router(events.router)
    app.include_router(health.router)

    return app


app = create_app()

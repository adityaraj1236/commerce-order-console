import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging import log_with_context, setup_logging
from app.core.middleware import REQUEST_ID_HEADER, RequestContextMiddleware
from app.dashboard.router import router as dashboard_router
from app.db.session import engine
from app.health.router import router as health_router
from app.orders.router import router as orders_router
from app.products.router import router as products_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    log_with_context(
        logger,
        "INFO",
        "APP: Application startup (main.py lifespan)",
        context={"environment": get_settings().environment},
    )
    yield
    engine.dispose()
    log_with_context(logger, "INFO", "APP: Application shutdown (main.py lifespan)")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.environment)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )
    # Added last so it wraps everything, including CORS, and every request gets an ID.
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    for router in (health_router, products_router, orders_router, dashboard_router):
        app.include_router(router, prefix=settings.api_v1_prefix)
    return app


app = create_app()

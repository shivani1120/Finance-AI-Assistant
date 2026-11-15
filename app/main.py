import logging

from fastapi import FastAPI

from app.api.routes.auth import admin_router, router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.documents import router as documents_router
from app.api.routes.retrieval import router as retrieval_router
from app.api.routes.chat import router as chat_router
from app.api.routes.history import router as history_router
from app.core.config import get_settings
from app.auth.bootstrap import initialize_auth_storage
from app.observability.logging import configure_logging
from app.observability.middleware import RequestObservabilityMiddleware

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

api = FastAPI(title=settings.app_name, version="0.1.0")
api.include_router(health_router)
api.include_router(auth_router)
api.include_router(admin_router)
api.include_router(documents_router)
api.include_router(retrieval_router)
api.include_router(chat_router)
api.include_router(history_router)


@api.on_event("startup")
async def log_startup() -> None:
    initialize_auth_storage(settings)
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)


# Keep observability outside FastAPI's error middleware so even unhandled 500 responses
# receive a request ID and a completion log.
app = RequestObservabilityMiddleware(api)

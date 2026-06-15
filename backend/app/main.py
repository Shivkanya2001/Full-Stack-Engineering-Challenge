from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.api.router import api_router
from app.api.v1 import health
from app.core.config import get_settings
from app.core.exceptions import DomainError
from app.core.logging import request_id_var, setup_logging
from app.database import AsyncSessionLocal
from app.integrations.redis_client import close_redis
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.services.exchange_service import ExchangeService
from app.workers.rate_refresh_worker import refresh_exchange_rates

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()

    scheduler.add_job(
        refresh_exchange_rates,
        "interval",
        minutes=settings.exchange_refresh_interval_minutes,
        id="exchange_rate_refresh",
        replace_existing=True,
    )
    scheduler.start()

    try:
        async with AsyncSessionLocal() as session:
            service = ExchangeService(session)
            await service.refresh_rates()
    except Exception:
        pass

    yield

    scheduler.shutdown(wait=False)
    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        status_map = {
            "NOT_FOUND": 404,
            "VALIDATION_ERROR": 422,
            "AUTHENTICATION_ERROR": 401,
            "AUTHORIZATION_ERROR": 403,
            "INSUFFICIENT_FUNDS": 422,
            "CONFLICT": 409,
            "EXCHANGE_RATE_ERROR": 503,
            "RATE_LIMIT_EXCEEDED": 429,
        }
        status_code = status_map.get(exc.code, 400)
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id_var.get(),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": exc.errors()},
                    "request_id": request_id_var.get(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                    "request_id": request_id_var.get(),
                }
            },
        )

    app.include_router(health.router, tags=["health"])
    app.include_router(api_router)
    return app


app = create_app()

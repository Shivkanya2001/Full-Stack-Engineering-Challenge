from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_session
from app.integrations.redis_client import get_redis
from app.services.exchange_service import ExchangeService

router = APIRouter()


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    checks: dict[str, str] = {}
    overall = "healthy"

    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception:
        checks["database"] = "down"
        overall = "unhealthy"

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "up"
    except Exception:
        checks["redis"] = "down"
        overall = "unhealthy"

    try:
        exchange = ExchangeService(session)
        provider_ok = await exchange.health_check()
        checks["exchange_provider"] = "up" if provider_ok else "degraded"
        if not provider_ok:
            overall = "degraded" if overall == "healthy" else overall
    except Exception:
        checks["exchange_provider"] = "down"
        overall = "degraded" if overall == "healthy" else overall

    status_code = 200 if overall in ("healthy", "degraded") else 503
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "service": settings.app_name,
            "version": settings.app_version,
            "checks": checks,
        },
    )


@router.get("/metrics")
async def metrics():
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    from fastapi.responses import Response

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_session
from app.schemas.exchange_rate import ExchangeRateListResponse, ExchangeRateResponse
from app.services.exchange_service import ExchangeService

router = APIRouter()


@router.get("", response_model=list[ExchangeRateResponse])
async def get_latest_rates(
    base_currency: str | None = Query(default=None),
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = ExchangeService(session)
    rates = await service.get_latest_rates(base_currency)
    return [ExchangeRateResponse(**r) for r in rates]


@router.get("/history", response_model=ExchangeRateListResponse)
async def get_rate_history(
    base_currency: str | None = Query(default=None),
    target_currency: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = ExchangeService(session)
    result = await service.list_history(base_currency, target_currency, page, page_size)
    return ExchangeRateListResponse(
        items=[ExchangeRateResponse(**r) for r in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.post("/refresh", response_model=list[ExchangeRateResponse])
async def refresh_rates(
    base_currency: str | None = Query(default=None),
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = ExchangeService(session)
    rates = await service.refresh_rates(base_currency)
    return [ExchangeRateResponse(**r) for r in rates]

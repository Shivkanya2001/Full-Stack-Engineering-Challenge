from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_session
from app.schemas.transaction import TransactionListResponse, TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str | None = Query(default=None, alias="type"),
    currency: str | None = Query(default=None),
    wallet_id: UUID | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    types = [t.strip() for t in type.split(",")] if type else None
    service = TransactionService(session)
    result = await service.list_transactions(
        user_id=user_id,
        page=page,
        page_size=page_size,
        types=types,
        currency=currency,
        wallet_id=wallet_id,
        from_date=from_date,
        to_date=to_date,
    )
    return TransactionListResponse(
        items=[TransactionResponse(**item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )

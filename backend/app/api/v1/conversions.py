from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_session
from app.schemas.conversion import ConversionRequest, ConversionResponse
from app.services.conversion_service import ConversionService

router = APIRouter()


@router.post("", response_model=ConversionResponse, status_code=201)
async def convert_currency(
    body: ConversionRequest,
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = ConversionService(session)
    result = await service.convert(
        user_id=user_id,
        source_wallet_id=UUID(body.source_wallet_id),
        target_wallet_id=UUID(body.target_wallet_id),
        amount_minor_units=body.amount_minor_units,
    )
    return ConversionResponse(**result)

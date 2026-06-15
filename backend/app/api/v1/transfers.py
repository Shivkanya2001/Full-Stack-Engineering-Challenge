from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_session
from app.schemas.transfer import TransferRequest, TransferResponse
from app.services.transfer_service import TransferService

router = APIRouter()


@router.post("", response_model=TransferResponse, status_code=201)
async def create_transfer(
    body: TransferRequest,
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    service = TransferService(session)
    result = await service.transfer(
        sender_id=user_id,
        receiver_email=body.receiver_email,
        sender_wallet_id=UUID(body.sender_wallet_id),
        amount_minor_units=body.amount_minor_units,
        idempotency_key=idempotency_key,
        receiver_currency=body.receiver_currency,
    )
    return TransferResponse(**result)


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: UUID,
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = TransferService(session)
    result = await service.get_transfer(user_id, transfer_id)
    return TransferResponse(**result)

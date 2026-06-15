from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_session
from app.schemas.wallet import (
    AmountRequest,
    CreateWalletRequest,
    WalletOperationResponse,
    WalletResponse,
)
from app.services.wallet_service import WalletService

router = APIRouter()


@router.get("", response_model=list[WalletResponse])
async def list_wallets(
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = WalletService(session)
    return await service.list_wallets(user_id)


@router.post("", response_model=WalletResponse, status_code=201)
async def create_wallet(
    body: CreateWalletRequest,
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = WalletService(session)
    return await service.create_wallet(user_id, body.currency)


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: UUID,
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = WalletService(session)
    return await service.get_wallet(user_id, wallet_id)


@router.post("/{wallet_id}/deposit", response_model=WalletOperationResponse)
async def deposit(
    wallet_id: UUID,
    body: AmountRequest,
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = WalletService(session)
    result = await service.deposit(user_id, wallet_id, body.amount_minor_units)
    return WalletOperationResponse(**result)


@router.post("/{wallet_id}/withdraw", response_model=WalletOperationResponse)
async def withdraw(
    wallet_id: UUID,
    body: AmountRequest,
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = WalletService(session)
    result = await service.withdraw(user_id, wallet_id, body.amount_minor_units)
    return WalletOperationResponse(**result)

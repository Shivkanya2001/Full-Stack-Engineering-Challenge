import pytest
from uuid import uuid4

from app.core.exceptions import ConflictError, InsufficientFundsError, ValidationError
from app.services.wallet_service import WalletService


@pytest.mark.asyncio
async def test_create_wallet(session):
    from app.models.user import UserModel
    from app.core.security import hash_password

    user = UserModel(
        email="wallet@example.com",
        password_hash=hash_password("password123"),
        full_name="Wallet User",
        default_currency="USD",
    )
    session.add(user)
    await session.commit()

    service = WalletService(session)
    wallet = await service.create_wallet(user.id, "USD")
    assert wallet["currency"] == "USD"
    assert wallet["balance_minor_units"] == 0


@pytest.mark.asyncio
async def test_deposit_and_withdraw(session):
    from app.models.user import UserModel
    from app.core.security import hash_password

    user = UserModel(
        email="dep@example.com",
        password_hash=hash_password("password123"),
        full_name="Dep User",
        default_currency="USD",
    )
    session.add(user)
    await session.commit()

    service = WalletService(session)
    wallet = await service.create_wallet(user.id, "USD")
    wallet_id = wallet["id"]

    from uuid import UUID
    result = await service.deposit(user.id, UUID(wallet_id), 10000)
    assert result["wallet"]["balance_minor_units"] == 10000

    result = await service.withdraw(user.id, UUID(wallet_id), 3000)
    assert result["wallet"]["balance_minor_units"] == 7000


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(session):
    from app.models.user import UserModel
    from app.core.security import hash_password
    from uuid import UUID

    user = UserModel(
        email="insuf@example.com",
        password_hash=hash_password("password123"),
        full_name="Insuf User",
        default_currency="USD",
    )
    session.add(user)
    await session.commit()

    service = WalletService(session)
    wallet = await service.create_wallet(user.id, "USD")

    with pytest.raises(InsufficientFundsError):
        await service.withdraw(user.id, UUID(wallet["id"]), 100)


@pytest.mark.asyncio
async def test_duplicate_wallet_raises_conflict(session):
    from app.models.user import UserModel
    from app.core.security import hash_password

    user = UserModel(
        email="dup@example.com",
        password_hash=hash_password("password123"),
        full_name="Dup User",
        default_currency="USD",
    )
    session.add(user)
    await session.commit()

    service = WalletService(session)
    await service.create_wallet(user.id, "EUR")
    with pytest.raises(ConflictError):
        await service.create_wallet(user.id, "EUR")

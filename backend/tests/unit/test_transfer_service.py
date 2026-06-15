import pytest
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

from app.core.security import hash_password
from app.models.user import UserModel
from app.services.transfer_service import TransferService


@pytest.mark.asyncio
async def test_transfer_same_currency(session, monkeypatch):
    sender = UserModel(
        email="sender@example.com",
        password_hash=hash_password("password123"),
        full_name="Sender",
        default_currency="USD",
    )
    receiver = UserModel(
        email="receiver@example.com",
        password_hash=hash_password("password123"),
        full_name="Receiver",
        default_currency="USD",
    )
    session.add_all([sender, receiver])
    await session.commit()

    from app.services.wallet_service import WalletService

    wallet_service = WalletService(session)
    sender_wallet = await wallet_service.create_wallet(sender.id, "USD")
    receiver_wallet = await wallet_service.create_wallet(receiver.id, "USD")
    await wallet_service.deposit(sender.id, UUID(sender_wallet["id"]), 50000)

    service = TransferService(session)
    result = await service.transfer(
        sender_id=sender.id,
        receiver_email="receiver@example.com",
        sender_wallet_id=UUID(sender_wallet["id"]),
        amount_minor_units=10000,
        idempotency_key="test-key-1",
    )

    assert result["sender_amount_minor_units"] == 10000
    assert result["receiver_amount_minor_units"] == 10000
    assert result["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_transfer_idempotency(session):
    sender = UserModel(
        email="idem-sender@example.com",
        password_hash=hash_password("password123"),
        full_name="Sender",
        default_currency="USD",
    )
    receiver = UserModel(
        email="idem-receiver@example.com",
        password_hash=hash_password("password123"),
        full_name="Receiver",
        default_currency="USD",
    )
    session.add_all([sender, receiver])
    await session.commit()

    from app.services.wallet_service import WalletService

    wallet_service = WalletService(session)
    sender_wallet = await wallet_service.create_wallet(sender.id, "USD")
    await wallet_service.create_wallet(receiver.id, "USD")
    await wallet_service.deposit(sender.id, UUID(sender_wallet["id"]), 50000)

    service = TransferService(session)
    key = "idem-key-123"
    first = await service.transfer(
        sender_id=sender.id,
        receiver_email="idem-receiver@example.com",
        sender_wallet_id=UUID(sender_wallet["id"]),
        amount_minor_units=5000,
        idempotency_key=key,
    )
    second = await service.transfer(
        sender_id=sender.id,
        receiver_email="idem-receiver@example.com",
        sender_wallet_id=UUID(sender_wallet["id"]),
        amount_minor_units=5000,
        idempotency_key=key,
    )
    assert first["id"] == second["id"]

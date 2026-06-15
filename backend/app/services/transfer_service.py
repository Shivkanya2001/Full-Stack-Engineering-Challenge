import logging
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.core.logging import log_event
from app.domain.rules import (
    validate_positive_amount,
    validate_sufficient_balance,
    validate_transfer_participants,
    validate_wallet_ownership,
)
from app.domain.value_objects.money import convert_amount, format_amount
from app.models.transaction import TransactionType
from app.repositories import TransactionRepository, TransferRepository, UserRepository, WalletRepository
from app.services.exchange_service import ExchangeService

logger = logging.getLogger(__name__)


class TransferService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.wallets = WalletRepository(session)
        self.transfers = TransferRepository(session)
        self.transactions = TransactionRepository(session)
        self.exchange = ExchangeService(session)

    async def transfer(
        self,
        sender_id: UUID,
        receiver_email: str,
        sender_wallet_id: UUID,
        amount_minor_units: int,
        idempotency_key: str | None = None,
        receiver_currency: str | None = None,
    ) -> dict:
        validate_positive_amount(amount_minor_units)
        key = idempotency_key or str(uuid4())

        existing = await self.transfers.get_by_idempotency_key(key)
        if existing:
            if existing.sender_user_id != sender_id:
                raise AuthorizationError("Idempotency key belongs to another user")
            return await self._transfer_response(existing)

        receiver_result = await self.users.get_by_email(receiver_email)
        if not receiver_result:
            raise NotFoundError("User", receiver_email)
        receiver, _ = receiver_result
        validate_transfer_participants(sender_id, receiver.id)

        sender_preview = await self.wallets.get_by_id(sender_wallet_id)
        if not sender_preview:
            raise NotFoundError("Wallet", str(sender_wallet_id))
        validate_wallet_ownership(sender_preview.user_id, sender_id)

        target_currency = (receiver_currency or sender_preview.currency).upper()
        receiver_wallet = await self.wallets.get_by_user_and_currency(receiver.id, target_currency)
        if not receiver_wallet:
            raise ValidationError(
                f"Receiver does not have a {target_currency} wallet",
                {"currency": target_currency, "receiver_email": receiver_email},
            )

        wallet_ids = sorted([sender_wallet_id, receiver_wallet.id])
        locked = await self.wallets.get_many_for_update(wallet_ids)
        wallet_map = {w.id: w for w in locked}
        sender = wallet_map[sender_wallet_id]
        receiver_wallet_model = wallet_map[receiver_wallet.id]

        validate_sufficient_balance(sender.balance_minor_units, amount_minor_units)

        exchange_rate_id = None
        converted_amount = amount_minor_units
        rate_str = "1"
        provider = "identity"

        if sender.currency != receiver_wallet_model.currency:
            rate_id, rate, provider, fetched_at = await self.exchange.get_rate_for_conversion(
                sender.currency, receiver_wallet_model.currency
            )
            converted_amount = convert_amount(
                amount_minor_units, sender.currency, receiver_wallet_model.currency, rate
            )
            exchange_rate_id = rate_id
            rate_str = str(rate)

        validate_positive_amount(converted_amount)

        sender.balance_minor_units -= amount_minor_units
        sender.version += 1
        receiver_wallet_model.balance_minor_units += converted_amount
        receiver_wallet_model.version += 1

        transfer = await self.transfers.create(
            sender_user_id=sender_id,
            receiver_user_id=receiver.id,
            sender_wallet_id=sender_wallet_id,
            receiver_wallet_id=receiver_wallet.id,
            sender_amount_minor_units=amount_minor_units,
            receiver_amount_minor_units=converted_amount,
            sender_currency=sender.currency,
            receiver_currency=receiver_wallet_model.currency,
            idempotency_key=key,
            exchange_rate_id=exchange_rate_id,
        )

        metadata = {
            "transfer_id": str(transfer.id),
            "receiver_email": receiver_email,
            "exchange_rate": rate_str,
            "provider": provider,
        }

        await self.transactions.append(
            wallet_id=sender_wallet_id,
            tx_type=TransactionType.TRANSFER_OUT,
            amount_minor_units=-amount_minor_units,
            currency=sender.currency,
            balance_after_minor_units=sender.balance_minor_units,
            transfer_id=transfer.id,
            exchange_rate_id=exchange_rate_id,
            metadata=metadata,
        )
        await self.transactions.append(
            wallet_id=receiver_wallet.id,
            tx_type=TransactionType.TRANSFER_IN,
            amount_minor_units=converted_amount,
            currency=receiver_wallet_model.currency,
            balance_after_minor_units=receiver_wallet_model.balance_minor_units,
            transfer_id=transfer.id,
            exchange_rate_id=exchange_rate_id,
            metadata=metadata,
        )

        try:
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            if "idempotency_key" in str(exc).lower() or "unique" in str(exc).lower():
                existing = await self.transfers.get_by_idempotency_key(key)
                if existing:
                    return await self._transfer_response(existing)
                raise ConflictError("Duplicate transfer request") from exc
            raise

        log_event(
            logger,
            "transfer.completed",
            sender_id=str(sender_id),
            receiver_id=str(receiver.id),
            transfer_id=str(transfer.id),
            amount=amount_minor_units,
        )
        return await self._transfer_response(transfer)

    async def get_transfer(self, user_id: UUID, transfer_id: UUID) -> dict:
        transfer = await self.transfers.get_by_id(transfer_id)
        if not transfer:
            raise NotFoundError("Transfer", str(transfer_id))
        if user_id not in (transfer.sender_user_id, transfer.receiver_user_id):
            raise AuthorizationError("Not authorized to view this transfer")
        return await self._transfer_response(transfer)

    async def _transfer_response(self, transfer) -> dict:
        return {
            "id": str(transfer.id),
            "sender_user_id": str(transfer.sender_user_id),
            "receiver_user_id": str(transfer.receiver_user_id),
            "sender_wallet_id": str(transfer.sender_wallet_id),
            "receiver_wallet_id": str(transfer.receiver_wallet_id),
            "sender_amount_minor_units": transfer.sender_amount_minor_units,
            "receiver_amount_minor_units": transfer.receiver_amount_minor_units,
            "sender_currency": transfer.sender_currency,
            "receiver_currency": transfer.receiver_currency,
            "sender_amount_display": format_amount(
                transfer.sender_amount_minor_units, transfer.sender_currency
            ),
            "receiver_amount_display": format_amount(
                transfer.receiver_amount_minor_units, transfer.receiver_currency
            ),
            "exchange_rate_id": str(transfer.exchange_rate_id) if transfer.exchange_rate_id else None,
            "status": transfer.status,
            "idempotency_key": transfer.idempotency_key,
            "created_at": transfer.created_at.isoformat(),
        }

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import log_event
from app.domain.rules import (
    validate_positive_amount,
    validate_sufficient_balance,
    validate_wallet_ownership,
)
from app.domain.value_objects.money import convert_amount, format_amount
from app.models.transaction import TransactionType
from app.repositories import TransactionRepository, WalletRepository
from app.services.exchange_service import ExchangeService

logger = logging.getLogger(__name__)


class ConversionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.wallets = WalletRepository(session)
        self.transactions = TransactionRepository(session)
        self.exchange = ExchangeService(session)

    async def convert(
        self,
        user_id: UUID,
        source_wallet_id: UUID,
        target_wallet_id: UUID,
        amount_minor_units: int,
    ) -> dict:
        validate_positive_amount(amount_minor_units)

        wallet_ids = sorted([source_wallet_id, target_wallet_id])
        locked = await self.wallets.get_many_for_update(wallet_ids)
        wallet_map = {w.id: w for w in locked}

        source = wallet_map.get(source_wallet_id)
        target = wallet_map.get(target_wallet_id)
        if not source or not target:
            from app.core.exceptions import NotFoundError

            raise NotFoundError("Wallet")

        validate_wallet_ownership(source.user_id, user_id)
        validate_wallet_ownership(target.user_id, user_id)
        validate_sufficient_balance(source.balance_minor_units, amount_minor_units)

        rate_id, rate, provider, fetched_at = await self.exchange.get_rate_for_conversion(
            source.currency, target.currency
        )
        converted_amount = convert_amount(
            amount_minor_units, source.currency, target.currency, rate
        )
        validate_positive_amount(converted_amount)

        source.balance_minor_units -= amount_minor_units
        source.version += 1
        target.balance_minor_units += converted_amount
        target.version += 1

        metadata = {
            "source_currency": source.currency,
            "target_currency": target.currency,
            "exchange_rate": str(rate),
            "provider": provider,
            "fetched_at": fetched_at.isoformat(),
        }

        out_tx = await self.transactions.append(
            wallet_id=source_wallet_id,
            tx_type=TransactionType.CONVERSION_OUT,
            amount_minor_units=-amount_minor_units,
            currency=source.currency,
            balance_after_minor_units=source.balance_minor_units,
            exchange_rate_id=rate_id,
            metadata=metadata,
        )
        in_tx = await self.transactions.append(
            wallet_id=target_wallet_id,
            tx_type=TransactionType.CONVERSION_IN,
            amount_minor_units=converted_amount,
            currency=target.currency,
            balance_after_minor_units=target.balance_minor_units,
            exchange_rate_id=rate_id,
            metadata=metadata,
        )
        await self.session.commit()

        log_event(
            logger,
            "conversion.executed",
            user_id=str(user_id),
            source_wallet_id=str(source_wallet_id),
            target_wallet_id=str(target_wallet_id),
            amount=amount_minor_units,
            converted=converted_amount,
        )

        return {
            "source_wallet": {
                "id": str(source.id),
                "currency": source.currency,
                "balance_minor_units": source.balance_minor_units,
                "balance_display": format_amount(source.balance_minor_units, source.currency),
            },
            "target_wallet": {
                "id": str(target.id),
                "currency": target.currency,
                "balance_minor_units": target.balance_minor_units,
                "balance_display": format_amount(target.balance_minor_units, target.currency),
            },
            "exchange_rate": str(rate),
            "provider": provider,
            "source_transaction": {"id": str(out_tx.id), "type": out_tx.type},
            "target_transaction": {"id": str(in_tx.id), "type": in_tx.type},
        }

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import log_event
from app.domain.rules import validate_positive_amount, validate_sufficient_balance, validate_wallet_ownership
from app.domain.value_objects.money import format_amount
from app.models.transaction import TransactionType
from app.repositories import TransactionRepository, WalletRepository

logger = logging.getLogger(__name__)


class WalletService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.wallets = WalletRepository(session)
        self.transactions = TransactionRepository(session)
        self.settings = get_settings()

    async def create_wallet(self, user_id: UUID, currency: str) -> dict:
        currency = currency.upper()
        if currency not in self.settings.supported_currencies:
            raise ValidationError(f"Unsupported currency: {currency}")

        existing = await self.wallets.get_by_user_and_currency(user_id, currency)
        if existing:
            raise ConflictError(f"Wallet for {currency} already exists")

        wallet = await self.wallets.create(user_id, currency)
        await self.session.commit()
        log_event(logger, "wallet.created", user_id=str(user_id), wallet_id=str(wallet.id), currency=currency)
        return self._wallet_response(wallet)

    async def list_wallets(self, user_id: UUID) -> list[dict]:
        wallets = await self.wallets.list_by_user(user_id)
        return [self._wallet_response(w) for w in wallets]

    async def get_wallet(self, user_id: UUID, wallet_id: UUID) -> dict:
        wallet = await self.wallets.get_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet", str(wallet_id))
        validate_wallet_ownership(wallet.user_id, user_id)
        return self._wallet_response(wallet)

    async def deposit(self, user_id: UUID, wallet_id: UUID, amount_minor_units: int) -> dict:
        validate_positive_amount(amount_minor_units)
        wallet_model = await self._get_owned_wallet_model(user_id, wallet_id)

        new_balance = wallet_model.balance_minor_units + amount_minor_units
        wallet_model.balance_minor_units = new_balance
        wallet_model.version += 1

        tx = await self.transactions.append(
            wallet_id=wallet_id,
            tx_type=TransactionType.DEPOSIT,
            amount_minor_units=amount_minor_units,
            currency=wallet_model.currency,
            balance_after_minor_units=new_balance,
            metadata={"operation": "deposit"},
        )
        await self.session.commit()

        log_event(
            logger,
            "wallet.deposit",
            user_id=str(user_id),
            wallet_id=str(wallet_id),
            amount=amount_minor_units,
        )
        return {"wallet": self._wallet_response_from_model(wallet_model), "transaction": self._tx_response(tx)}

    async def withdraw(self, user_id: UUID, wallet_id: UUID, amount_minor_units: int) -> dict:
        validate_positive_amount(amount_minor_units)
        wallet_model = await self._get_owned_wallet_model(user_id, wallet_id)
        validate_sufficient_balance(wallet_model.balance_minor_units, amount_minor_units)

        new_balance = wallet_model.balance_minor_units - amount_minor_units
        wallet_model.balance_minor_units = new_balance
        wallet_model.version += 1

        tx = await self.transactions.append(
            wallet_id=wallet_id,
            tx_type=TransactionType.WITHDRAWAL,
            amount_minor_units=-amount_minor_units,
            currency=wallet_model.currency,
            balance_after_minor_units=new_balance,
            metadata={"operation": "withdraw"},
        )
        await self.session.commit()

        log_event(
            logger,
            "wallet.withdraw",
            user_id=str(user_id),
            wallet_id=str(wallet_id),
            amount=amount_minor_units,
        )
        return {"wallet": self._wallet_response_from_model(wallet_model), "transaction": self._tx_response(tx)}

    async def _get_owned_wallet_model(self, user_id: UUID, wallet_id: UUID):
        wallet_model = await self.wallets.get_for_update(wallet_id)
        if not wallet_model:
            raise NotFoundError("Wallet", str(wallet_id))
        validate_wallet_ownership(wallet_model.user_id, user_id)
        return wallet_model

    @staticmethod
    def _wallet_response(wallet) -> dict:
        return {
            "id": str(wallet.id),
            "user_id": str(wallet.user_id),
            "currency": wallet.currency,
            "balance_minor_units": wallet.balance_minor_units,
            "balance_display": format_amount(wallet.balance_minor_units, wallet.currency),
            "version": wallet.version,
            "created_at": wallet.created_at.isoformat(),
        }

    @staticmethod
    def _wallet_response_from_model(model) -> dict:
        return {
            "id": str(model.id),
            "user_id": str(model.user_id),
            "currency": model.currency,
            "balance_minor_units": model.balance_minor_units,
            "balance_display": format_amount(model.balance_minor_units, model.currency),
            "version": model.version,
            "created_at": model.created_at.isoformat(),
        }

    @staticmethod
    def _tx_response(tx) -> dict:
        return {
            "id": str(tx.id),
            "wallet_id": str(tx.wallet_id),
            "type": tx.type,
            "amount_minor_units": tx.amount_minor_units,
            "currency": tx.currency,
            "balance_after_minor_units": tx.balance_after_minor_units,
            "created_at": tx.created_at.isoformat(),
        }

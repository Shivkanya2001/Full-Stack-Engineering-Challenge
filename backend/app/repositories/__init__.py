from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import ExchangeRate, Transaction, Transfer, User, Wallet
from app.models.exchange_rate import ExchangeRateModel
from app.models.transaction import TransactionModel, TransactionType
from app.models.transfer import TransferModel, TransferStatus
from app.models.user import UserModel
from app.models.wallet import WalletModel


def _to_user(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        full_name=model.full_name,
        profile_photo_url=model.profile_photo_url,
        default_currency=model.default_currency,
        created_at=model.created_at,
    )


def _to_wallet(model: WalletModel) -> Wallet:
    return Wallet(
        id=model.id,
        user_id=model.user_id,
        currency=model.currency,
        balance_minor_units=model.balance_minor_units,
        version=model.version,
        created_at=model.created_at,
    )


def _to_transaction(model: TransactionModel) -> Transaction:
    return Transaction(
        id=model.id,
        wallet_id=model.wallet_id,
        type=model.type,
        amount_minor_units=model.amount_minor_units,
        currency=model.currency,
        balance_after_minor_units=model.balance_after_minor_units,
        transfer_id=model.transfer_id,
        exchange_rate_id=model.exchange_rate_id,
        metadata=model.metadata_,
        created_at=model.created_at,
    )


def _to_transfer(model: TransferModel) -> Transfer:
    return Transfer(
        id=model.id,
        sender_user_id=model.sender_user_id,
        receiver_user_id=model.receiver_user_id,
        sender_wallet_id=model.sender_wallet_id,
        receiver_wallet_id=model.receiver_wallet_id,
        sender_amount_minor_units=model.sender_amount_minor_units,
        receiver_amount_minor_units=model.receiver_amount_minor_units,
        sender_currency=model.sender_currency,
        receiver_currency=model.receiver_currency,
        exchange_rate_id=model.exchange_rate_id,
        status=model.status,
        idempotency_key=model.idempotency_key,
        created_at=model.created_at,
    )


def _to_exchange_rate(model: ExchangeRateModel) -> ExchangeRate:
    return ExchangeRate(
        id=model.id,
        base_currency=model.base_currency,
        target_currency=model.target_currency,
        rate=model.rate,
        provider=model.provider,
        fetched_at=model.fetched_at,
        valid_from=model.valid_from,
        valid_until=model.valid_until,
    )


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, email: str, password_hash: str, full_name: str, default_currency: str) -> User:
        model = UserModel(
            email=email.lower(),
            password_hash=password_hash,
            full_name=full_name,
            default_currency=default_currency,
        )
        self.session.add(model)
        await self.session.flush()
        return _to_user(model)

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return _to_user(model) if model else None

    async def get_by_email(self, email: str) -> tuple[User, str] | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return _to_user(model), model.password_hash

    async def update_profile(
        self,
        user_id: UUID,
        full_name: str | None = None,
        profile_photo_url: str | None = None,
        default_currency: str | None = None,
    ) -> User | None:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        if not model:
            return None
        if full_name is not None:
            model.full_name = full_name
        if profile_photo_url is not None:
            model.profile_photo_url = profile_photo_url
        if default_currency is not None:
            model.default_currency = default_currency
        await self.session.flush()
        return _to_user(model)


class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, currency: str) -> Wallet:
        model = WalletModel(user_id=user_id, currency=currency)
        self.session.add(model)
        await self.session.flush()
        return _to_wallet(model)

    async def get_by_id(self, wallet_id: UUID) -> Wallet | None:
        result = await self.session.execute(select(WalletModel).where(WalletModel.id == wallet_id))
        model = result.scalar_one_or_none()
        return _to_wallet(model) if model else None

    async def get_by_user_and_currency(self, user_id: UUID, currency: str) -> Wallet | None:
        result = await self.session.execute(
            select(WalletModel).where(
                WalletModel.user_id == user_id,
                WalletModel.currency == currency,
            )
        )
        model = result.scalar_one_or_none()
        return _to_wallet(model) if model else None

    async def list_by_user(self, user_id: UUID) -> list[Wallet]:
        result = await self.session.execute(
            select(WalletModel).where(WalletModel.user_id == user_id).order_by(WalletModel.currency)
        )
        return [_to_wallet(m) for m in result.scalars().all()]

    async def get_for_update(self, wallet_id: UUID) -> WalletModel | None:
        result = await self.session.execute(
            select(WalletModel).where(WalletModel.id == wallet_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_many_for_update(self, wallet_ids: list[UUID]) -> list[WalletModel]:
        ordered_ids = sorted(wallet_ids)
        result = await self.session.execute(
            select(WalletModel).where(WalletModel.id.in_(ordered_ids)).with_for_update()
        )
        wallets = list(result.scalars().all())
        wallets.sort(key=lambda w: w.id)
        return wallets


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append(
        self,
        wallet_id: UUID,
        tx_type: TransactionType,
        amount_minor_units: int,
        currency: str,
        balance_after_minor_units: int,
        transfer_id: UUID | None = None,
        exchange_rate_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> Transaction:
        model = TransactionModel(
            wallet_id=wallet_id,
            type=tx_type.value,
            amount_minor_units=amount_minor_units,
            currency=currency,
            balance_after_minor_units=balance_after_minor_units,
            transfer_id=transfer_id,
            exchange_rate_id=exchange_rate_id,
            metadata_=metadata,
        )
        self.session.add(model)
        await self.session.flush()
        return _to_transaction(model)

    async def list_for_user(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
        types: list[str] | None = None,
        currency: str | None = None,
        wallet_id: UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[Transaction], int]:
        query: Select = (
            select(TransactionModel)
            .join(WalletModel, TransactionModel.wallet_id == WalletModel.id)
            .where(WalletModel.user_id == user_id)
        )
        count_query = (
            select(func.count())
            .select_from(TransactionModel)
            .join(WalletModel, TransactionModel.wallet_id == WalletModel.id)
            .where(WalletModel.user_id == user_id)
        )

        filters = []
        if types:
            filters.append(TransactionModel.type.in_(types))
        if currency:
            filters.append(TransactionModel.currency == currency.upper())
        if wallet_id:
            filters.append(TransactionModel.wallet_id == wallet_id)
        if from_date:
            filters.append(TransactionModel.created_at >= from_date)
        if to_date:
            filters.append(TransactionModel.created_at <= to_date)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        result = await self.session.execute(
            query.order_by(desc(TransactionModel.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [_to_transaction(m) for m in result.scalars().all()]
        return items, total


class TransferRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_idempotency_key(self, key: str) -> Transfer | None:
        result = await self.session.execute(
            select(TransferModel).where(TransferModel.idempotency_key == key)
        )
        model = result.scalar_one_or_none()
        return _to_transfer(model) if model else None

    async def get_by_id(self, transfer_id: UUID) -> Transfer | None:
        result = await self.session.execute(select(TransferModel).where(TransferModel.id == transfer_id))
        model = result.scalar_one_or_none()
        return _to_transfer(model) if model else None

    async def create(
        self,
        sender_user_id: UUID,
        receiver_user_id: UUID,
        sender_wallet_id: UUID,
        receiver_wallet_id: UUID,
        sender_amount_minor_units: int,
        receiver_amount_minor_units: int,
        sender_currency: str,
        receiver_currency: str,
        idempotency_key: str,
        exchange_rate_id: UUID | None = None,
    ) -> Transfer:
        model = TransferModel(
            sender_user_id=sender_user_id,
            receiver_user_id=receiver_user_id,
            sender_wallet_id=sender_wallet_id,
            receiver_wallet_id=receiver_wallet_id,
            sender_amount_minor_units=sender_amount_minor_units,
            receiver_amount_minor_units=receiver_amount_minor_units,
            sender_currency=sender_currency,
            receiver_currency=receiver_currency,
            exchange_rate_id=exchange_rate_id,
            status=TransferStatus.COMPLETED.value,
            idempotency_key=idempotency_key,
        )
        self.session.add(model)
        await self.session.flush()
        return _to_transfer(model)


class ExchangeRateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def store_rates(self, rates: list[tuple[str, str, Decimal, str, datetime]]) -> list[ExchangeRate]:
        models = []
        for base, target, rate, provider, fetched_at in rates:
            model = ExchangeRateModel(
                base_currency=base,
                target_currency=target,
                rate=rate,
                provider=provider,
                fetched_at=fetched_at,
            )
            self.session.add(model)
            models.append(model)
        await self.session.flush()
        return [_to_exchange_rate(m) for m in models]

    async def get_latest(self, base_currency: str, target_currency: str) -> ExchangeRate | None:
        result = await self.session.execute(
            select(ExchangeRateModel)
            .where(
                ExchangeRateModel.base_currency == base_currency.upper(),
                ExchangeRateModel.target_currency == target_currency.upper(),
            )
            .order_by(desc(ExchangeRateModel.fetched_at))
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _to_exchange_rate(model) if model else None

    async def list_latest_for_base(self, base_currency: str) -> list[ExchangeRate]:
        subq = (
            select(
                ExchangeRateModel.target_currency,
                func.max(ExchangeRateModel.fetched_at).label("max_fetched"),
            )
            .where(ExchangeRateModel.base_currency == base_currency.upper())
            .group_by(ExchangeRateModel.target_currency)
            .subquery()
        )
        result = await self.session.execute(
            select(ExchangeRateModel).join(
                subq,
                and_(
                    ExchangeRateModel.target_currency == subq.c.target_currency,
                    ExchangeRateModel.fetched_at == subq.c.max_fetched,
                ),
            )
        )
        return [_to_exchange_rate(m) for m in result.scalars().all()]

    async def list_history(
        self,
        base_currency: str | None,
        target_currency: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[ExchangeRate], int]:
        query = select(ExchangeRateModel)
        count_query = select(func.count()).select_from(ExchangeRateModel)
        filters = []
        if base_currency:
            filters.append(ExchangeRateModel.base_currency == base_currency.upper())
        if target_currency:
            filters.append(ExchangeRateModel.target_currency == target_currency.upper())
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        result = await self.session.execute(
            query.order_by(desc(ExchangeRateModel.fetched_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [_to_exchange_rate(m) for m in result.scalars().all()], total

    async def get_by_id(self, rate_id: UUID) -> ExchangeRate | None:
        result = await self.session.execute(
            select(ExchangeRateModel).where(ExchangeRateModel.id == rate_id)
        )
        model = result.scalar_one_or_none()
        return _to_exchange_rate(model) if model else None

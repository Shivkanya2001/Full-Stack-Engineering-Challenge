from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    full_name: str
    profile_photo_url: str | None
    default_currency: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Wallet:
    id: UUID
    user_id: UUID
    currency: str
    balance_minor_units: int
    version: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Transaction:
    id: UUID
    wallet_id: UUID
    type: str
    amount_minor_units: int
    currency: str
    balance_after_minor_units: int
    transfer_id: UUID | None
    exchange_rate_id: UUID | None
    metadata: dict | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Transfer:
    id: UUID
    sender_user_id: UUID
    receiver_user_id: UUID
    sender_wallet_id: UUID
    receiver_wallet_id: UUID
    sender_amount_minor_units: int
    receiver_amount_minor_units: int
    sender_currency: str
    receiver_currency: str
    exchange_rate_id: UUID | None
    status: str
    idempotency_key: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ExchangeRate:
    id: UUID
    base_currency: str
    target_currency: str
    rate: Decimal
    provider: str
    fetched_at: datetime
    valid_from: datetime
    valid_until: datetime | None

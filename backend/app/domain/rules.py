from uuid import UUID

from app.core.exceptions import InsufficientFundsError, ValidationError
from app.domain.value_objects.money import normalize_currency


def validate_positive_amount(amount_minor_units: int) -> None:
    if amount_minor_units <= 0:
        raise ValidationError("Amount must be greater than zero")


def validate_wallet_ownership(wallet_user_id: UUID, requester_id: UUID) -> None:
    if wallet_user_id != requester_id:
        raise ValidationError("Wallet does not belong to user")


def validate_sufficient_balance(balance: int, amount: int) -> None:
    if balance < amount:
        raise InsufficientFundsError(available=balance, required=amount)


def validate_transfer_participants(sender_id: UUID, receiver_id: UUID) -> None:
    if sender_id == receiver_id:
        raise ValidationError("Cannot transfer to yourself")


def validate_currencies(*currencies: str, supported: list[str]) -> list[str]:
    normalized = []
    for currency in currencies:
        code = normalize_currency(currency)
        if code not in supported:
            raise ValidationError(f"Unsupported currency: {currency}")
        normalized.append(code)
    return normalized

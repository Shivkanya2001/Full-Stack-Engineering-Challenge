from pydantic import BaseModel, EmailStr, Field


class TransferRequest(BaseModel):
    receiver_email: EmailStr
    sender_wallet_id: str
    amount_minor_units: int = Field(gt=0)
    receiver_currency: str | None = Field(default=None, min_length=3, max_length=3)


class TransferResponse(BaseModel):
    id: str
    sender_user_id: str
    receiver_user_id: str
    sender_wallet_id: str
    receiver_wallet_id: str
    sender_amount_minor_units: int
    receiver_amount_minor_units: int
    sender_currency: str
    receiver_currency: str
    sender_amount_display: str
    receiver_amount_display: str
    exchange_rate_id: str | None
    status: str
    idempotency_key: str
    created_at: str

from pydantic import BaseModel


class TransactionResponse(BaseModel):
    id: str
    wallet_id: str
    type: str
    amount_minor_units: int
    currency: str
    balance_after_minor_units: int
    transfer_id: str | None
    exchange_rate_id: str | None
    metadata: dict | None
    created_at: str


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
